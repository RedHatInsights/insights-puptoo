import traceback

from collections import deque
from prometheus_client import start_http_server
from kafka.errors import KafkaError
from time import time

import process
import tracker

from utils import config, metrics, puptoo_logging
from mq import consume, produce

logger = puptoo_logging.initialize_logging()

def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", request_id="unknown"):
    return {"account": account, "request_id": request_id}

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


def process_archive(msg, extra):
    facts = process.extraction(msg, extra)
    if facts.get("error"):
        metrics.extract_failure.inc()
        producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "failure", "Unable to extract facts"))
        return None
    logger.debug("extracted facts from message for %s", extra["request_id"])
    return facts


def send_data_to_inventory(msg, facts, extra):
    inv_msg = {"operation": "add_host", "data": facts, "platform_metadata": msg}
    inv_msg["data"]["account"] = msg.get("account")
    try:
        inv_msg["data"]["elapsed_time"] = time() - msg["elapsed_time"]
        logger.debug("Message traversed pup in %s seconds", inv_msg["data"]["elapsed_time"])
        logger.debug("Message sent to Inventory: %s", extra["request_id"])
        producer.send(config.INVENTORY_TOPIC, value=inv_msg)
    except KafkaError:
        logger.exception("Failed to produce message to inventory: %s", extra["request_id"])
        metrics.msg_send_failure.inc()
    metrics.msg_processed.inc()
    try:
        producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "success", "Sent to inventory"))
    except KafkaError:
        logger.exception("Failed to send payload tracker message for request %s", extra["request_id"])
        metrics.msg_send_failure.inc()
    metrics.msg_produced.inc()


def handle_message(msg):
    msg["elapsed_time"] = time()
    extra = get_extra(msg.get("account"), msg.get("request_id"))
    logger.info("received request_id: %s", extra["request_id"])
    producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "received", "Received message"))
    metrics.msg_count.inc()

    facts = process_archive(msg, extra)

    if facts:
        send_data_to_inventory(msg, facts, extra)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        the_error = traceback.format_exc()
        logger.error(f"Puptoo failed with Error: {the_error}")
