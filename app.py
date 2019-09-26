import traceback
import requests

from collections import deque
from prometheus_client import start_http_server
from kafka.errors import KafkaError
from time import time

import process

from utils import config, metrics, puptoo_logging
from mq import consume, produce, msgs

logger = puptoo_logging.initialize_logging()

def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", request_id="unknown"):
    return {"account": account, "request_id": request_id}


def get_inv_id(msg, insights_id):
    headers = {"x-rh-identity": msg["b64_identity"]}
    query_string = "?insights_id={}".format(insights_id)
    r = requests.get(config.INVENTORY_URL + query_string, headers=headers).json()
    try:
        result = r["results"][0]["id"]
        logger.debug("Got inventory ID successfully for [%s] - [%s]", msg.get("request_id"), result)
    except KeyError:
        logger.error("unable to get inventory ID for request: %s", msg["request_id"])
        result = None

    return result


producer = None

def main():

    logger.info("Starting Puptoo Service")

    config.log_config()

    if not config.DISABLE_PROMETHEUS:
        logger.info("Starting Puptoo Prometheus Server")
        start_prometheus()

    consumer = consume.init_consumer()
    global producer
    producer = produce.init_producer()

    while True:
        for data in consumer:
            try:
                handle_message(data.value)
            except Exception:
                logger.exception("An error occurred during message processing")

        producer.flush()


def validation(msg, status, extra):
    send_message(config.VALIDATION_TOPIC, msgs.validation_message(msg, status), extra)


def process_archive(msg, extra):
    facts = process.extraction(msg, extra)
    if facts.get("error"):
        metrics.extract_failure.inc()
        send_message(config.TRACKER_TOPIC, msgs.tracker_message(extra, "failure", "Unable to extract facts"), extra)
        validation(msg, "failure", extra)
        return None
    logger.debug("extracted facts from message for %s", extra["request_id"])
    logger.debug("Message: %s", msg)
    if facts.get("id") is None:
        msg["id"] = get_inv_id(msg, facts.get("insights_id"))
    validation(msg, "success", extra)
    return facts


def send_message(topic, msg, extra):
    try:
        producer.send(topic, value=msg)
        logger.debug("Message sent to [%s] topic for id [%s]", topic, extra["request_id"])
    except KafkaError:
        logger.exception("Failed to produce message to [%s] topic: %s", topic, extra["request_id"])
        metrics.msg_send_failure()
    metrics.msg_processed.inc()


def handle_message(msg):
    msg["elapsed_time"] = time()
    extra = get_extra(msg.get("account"), msg.get("request_id"))
    logger.info("received request_id: %s", extra["request_id"])
    send_message(config.TRACKER_TOPIC, msgs.tracker_message(extra, "received", "Received message"), extra)
    metrics.msg_count.inc()

    facts = process_archive(msg, extra)

    if facts:
        send_message(config.INVENTORY_TOPIC, msgs.inv_message("add_host", facts, msg), extra)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        the_error = traceback.format_exc()
        logger.error(f"Puptoo failed with Error: {the_error}")
