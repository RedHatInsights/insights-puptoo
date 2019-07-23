import traceback
import collections

from prometheus_client import start_http_server
from kafka.errors import KafkaError

import config
import consumer
import process
import producer
import puptoo_logging
import metrics
import tracker

logger = puptoo_logging.initialize_logging()

produce_queue = collections.deque([])
consume_queue = collections.deque([])


def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", request_id="unknown"):
    return {"account": account, "request_id": request_id}


def main():

    logger.info("Starting Extracto Service")

    logger.info("Using LOG_LEVEL: %s", config.LOG_LEVEL)
    logger.info("Using BOOTSTRAP_SERVERS: %s", config.BOOTSTRAP_SERVERS)
    logger.info("Using GROUP_ID: %s", config.GROUP_ID)
    logger.info("Using TRACKER_TOPIC: %s", config.TRACKER_TOPIC)
    logger.info("Using DISABLE_PROMETHEUS: %s", config.DISABLE_PROMETHEUS)
    logger.info("Using PROMETHEUS_PORT: %s", config.PROMETHEUS_PORT)

    if not config.DISABLE_PROMETHEUS:
        logger.info("Starting Extracto Prometheus Server")
        start_prometheus()

    consume = consumer.init_consumer()
    produce = producer.init_producer()

    while True:
        for data in consume:
            msg = data.value
            extra = get_extra(msg.get("account"), msg.get("request_id"))
            consume_queue.append(msg)
            logger.info("consumed message from queue: %s", msg, extra=extra)
            produce_queue.append(tracker.tracker_msg(extra, "received", "Received message"))
            metrics.msg_count.inc()

        while len(consume_queue) >= 1:
            consumed = consume_queue.popleft()
            extra = get_extra(consumed.get("account"), consumed.get("request_id"))
            produce_queue.append(tracker.tracker_msg(extra, "processing", "Extracting facts"))
            facts = process.extraction(consumed, extra)
            if facts.get("error"):
                metrics.extract_failure.inc()
                produce_queue.append(tracker.tracker_msg(extra, "failure", "Unable to extract facts"))
                continue
            inv_msg = {"data": {**consumed, **facts}}
            produce_queue.append(tracker.tracker_msg(extra, "processing", "Successfully extracted facts"))
            produce_queue.append({"topic": config.INVENTORY_TOPIC, "msg": inv_msg, "extra": extra})
            metrics.msg_processed.inc()

        while len(produce_queue) >= 1:
            item = produce_queue.popleft()
            logger.info("producing message on %s", item["topic"], extra=item["extra"])
            try:
                produce.send(item["topic"], value=item["msg"])
            except KafkaError:
                logger.exception("Failed to produce message. Placing back on queue: %s", item["extra"]["request_id"])
            if item["topic"] == config.INVENTORY_TOPIC:
                produce_queue.append(tracker.tracker_msg(item["extra"], "Success", "Sent to inventory"))
            metrics.msg_produced.inc()
            logger.info("Produce queue size: %d", len(produce_queue))

        produce.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        the_error = traceback.format_exc()
        logger.error(f"Puptoo failed with Error: {the_error}")
