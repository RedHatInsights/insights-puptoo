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


def main():

    logger.info("Starting Puptoo Service")

    config.log_config()

    if not config.DISABLE_PROMETHEUS:
        logger.info("Starting Puptoo Prometheus Server")
        start_prometheus()

    consumer = consume.init_consumer()
    producer = produce.init_producer()

    while True:
        for data in consumer:
            msg = data.value
            msg["elapsed_time"] = time()
            extra = get_extra(msg.get("account"), msg.get("request_id"))
            logger.info("received request_id: %s", extra["request_id"])
            producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "received", "Received message"))
            metrics.msg_count.inc()
            facts = process.extraction(msg, extra)
            if facts.get("error"):
                metrics.extract_failure.inc()
                producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "failure", "Unable to extract facts"))
                continue
            logger.debug("extracted facts from message for %s", extra["request_id"])
            inv_msg = {"data": facts, "platform_metadata": msg}
            try:
                inv_msg["data"]["elapsed_time"] = time() - msg["elapsed_time"]
                logger.debug("Message traversed pup in %s seconds", inv_msg["data"]["elapsed_time"])
                logger.debug("Message sent to Inventory: %s", extra["request_id"])
                producer.send(config.INVENTORY_TOPIC, value=inv_msg)
            except KafkaError:
                logger.exception("Failed to produce message to inventory: %s", extra["request_id"])
                metrics.msg_send_failure.inc()
                continue
            metrics.msg_processed.inc()
            try:
                producer.send(config.TRACKER_TOPIC, value=tracker.tracker_msg(extra, "success", "Sent to inventory"))
            except KafkaError:
                logger.exception("Failed to send payload tracker message for request %s", extra["request_id"])
                metrics.msg_send_failure.inc()
            metrics.msg_produced.inc()

        producer.flush()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        the_error = traceback.format_exc()
        logger.error(f"Puptoo failed with Error: {the_error}")
