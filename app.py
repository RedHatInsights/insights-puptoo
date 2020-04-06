import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from time import time

import process
from kafka.errors import KafkaError
from mq import consume, msgs, produce
from prometheus_client import Info, Summary, start_http_server
from utils import config, metrics, puptoo_logging

CONSUMER_WAIT_TIME = Summary(
    "puptoo_consumer_wait_time", "Time spent waiting on consumer iteration"
)
CONSUMER_ASSIGNMENTS = Info(
    "puptoo_consumer_assignments", "List of partitions assigned to the consumer"
)

logger = puptoo_logging.initialize_logging()


def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", request_id="unknown"):
    return {"account": account, "request_id": request_id}


def get_staletime():
    the_time = datetime.now() + timedelta(hours=26)
    return the_time.astimezone().isoformat()


producer = None


def _get_assignments(consumer):
    grouped = defaultdict(list)
    for tp in consumer.assignment():
        grouped[tp.topic].append(str(tp.partition))
    CONSUMER_ASSIGNMENTS.info(
        {topic: ", ".join(sorted(partitions)) for topic, partitions in grouped.items()}
    )


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
        # call this every time around so that we have a chance to update the listing
        # when a rebalance occurs
        _get_assignments(consumer)
        start = time()
        for data in consumer:
            now = time()
            CONSUMER_WAIT_TIME.observe(now - start)
            start = now

            try:
                handle_message(data.value)
            except Exception:
                logger.exception("An error occurred during message processing")

        producer.flush()


def validation(msg, facts, status, extra):
    send_message(
        config.VALIDATION_TOPIC, msgs.validation_message(msg, facts, status), extra
    )
    send_message(
        config.TRACKER_TOPIC,
        msgs.tracker_message(
            extra, "failed", "Validation failure. Message sent to storage broker"
        ),
        extra,
    )


def process_archive(msg, extra):
    facts = process.extraction(msg, extra)
    if facts.get("error"):
        metrics.extract_failure.inc()
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(extra, "error", "Unable to extract facts"),
            extra,
        )
        validation(msg, "failure", extra)
        return None
    logger.debug(
        "extracted facts from message for %s\nMessage: %s\nFacts: %s",
        extra["request_id"],
        msg,
        facts,
    )
    return facts


def send_message(topic, msg, extra):
    try:
        producer.send(topic, value=msg)
        if topic == config.INVENTORY_TOPIC:
            msg["data"].pop("system_profile")
        logger.info(
            "Message sent to [%s] topic for id [%s]: %s",
            topic,
            extra["request_id"],
            msg,
        )
    except KafkaError:
        logger.exception(
            "Failed to produce message to [%s] topic: %s", topic, extra["request_id"]
        )
        metrics.msg_send_failure()
    metrics.msg_processed.inc()


def handle_message(msg):
    msg["elapsed_time"] = time()
    extra = get_extra(msg.get("account"), msg.get("request_id"))
    logger.info("received request_id: %s", extra["request_id"])
    send_message(
        config.TRACKER_TOPIC,
        msgs.tracker_message(extra, "received", "Received message"),
        extra,
    )
    metrics.msg_count.inc()

    facts = process_archive(msg, extra)
    facts["stale_timestamp"] = get_staletime()
    facts["reporter"] = "puptoo"

    if facts:
        send_message(
            config.INVENTORY_TOPIC, msgs.inv_message("add_host", facts, msg), extra
        )
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(extra, "success", "Message sent to inventory"),
            extra,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        the_error = traceback.format_exc()
        logger.error(f"Puptoo failed with Error: {the_error}")
