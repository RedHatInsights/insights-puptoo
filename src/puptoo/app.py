import json
import signal
from datetime import datetime, timedelta
from functools import partial
from time import time
from base64 import b64decode

from confluent_kafka import KafkaError
from prometheus_client import Info, Summary, start_http_server

from .process import extract
from .mq import consume, msgs, produce
from .utils import config, metrics, puptoo_logging
from .utils.puptoo_logging import threadctx

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
    threadctx.request_id = request_id
    threadctx.account = account
    return {"account": account, "request_id": request_id}


def get_staletime():
    the_time = datetime.now() + timedelta(hours=26)
    return the_time.astimezone().isoformat()


def get_owner(ident):
    s = b64decode(ident).decode("utf-8")
    identity = json.loads(s)
    if identity["identity"].get("system"):
        owner_id = identity["identity"]["system"].get("cn")
        return owner_id


producer = None

running = True


def handle_signal(signal, frame):
    global running
    running = False


signal.signal(signal.SIGTERM, handle_signal)


def main():
    try:
        logger.info("Starting Puptoo Service")

        config.log_config()

        if not config.DISABLE_PROMETHEUS:
            logger.info("Starting Puptoo Prometheus Server")
            start_prometheus()

        consumer = consume.init_consumer()
        global producer
        producer = produce.init_producer()

        start = time()
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: %s", msg.error())
                metrics.failed_msg_count.inc()
                continue

            now = time()
            CONSUMER_WAIT_TIME.observe(now - start)
            start = now
            try:
                msg = json.loads(msg.value().decode("utf-8"))
                handle_message(msg)
            except Exception:
                consumer.commit()
                logger.exception("An error occurred during message processing")
            finally:
                producer.flush()
                if not config.KAFKA_AUTO_COMMIT:
                    consumer.commit()

        consumer.close()
        producer.flush()
    except Exception:
        logger.exception("Puptoo failed with Error")


def process_archive(msg, extra):
    facts = extract(msg, extra)
    if facts.get("error"):
        metrics.extract_failure.inc()
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(extra, "error", "Unable to extract facts"),
            extra,
        )
        send_message(
            config.VALIDATION_TOPIC,
            msgs.validation_message(msg, facts, "failure"),
            extra,
        )
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(
                extra, "failed", "Validation failure. Message sent to storage broker"
            ),
            extra,
        )
        return None
    logger.debug(
        "extracted facts from message for %s\nMessage: %s\nFacts: %s",
        extra["request_id"],
        msg,
        facts,
    )
    return facts


def delivery_report(err, msg=None, extra=None):
    if err is not None:
        logger.error(
            "Message delivery for topic %s failed for request_id [%s]: %s",
            msg.topic(),
            err,
            extra["request_id"],
        )
        metrics.msg_send_failure.labels(msg.topic()).inc()
    else:
        logger.info(
            "Message delivered to %s [%s] for request_id [%s]",
            msg.topic(),
            msg.partition(),
            extra["request_id"],
        )
        metrics.msg_produced.labels(msg.topic()).inc()


@metrics.send_time.time()
def send_message(topic, msg, extra):
    try:
        producer.poll(0)
        _bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        producer.produce(topic, _bytes, callback=partial(delivery_report, extra=extra))
        if topic == config.INVENTORY_TOPIC and msg.get("system_profile"):
            msg["data"].pop("system_profile")
            logger.info("Message sent to inventory: %s", msg)
    except KafkaError:
        metrics.msg_send_failure.labels(topic).inc()
        logger.exception(
            "Failed to produce message to [%s] topic: %s", topic, extra["request_id"]
        )


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
    owner_id = get_owner(msg["b64_identity"])

    if msg.get("service") == "advisor":
        facts = process_archive(msg, extra)
    if msg.get("service") == "compliance":
        facts = msg.get("metadata")

    if facts:
        facts["stale_timestamp"] = get_staletime()
        facts["reporter"] = "puptoo"
        if facts.get("system_profile"):
            if owner_id:
                facts["system_profile"]["owner_id"] = owner_id
            if facts["system_profile"].get("is_ros"):
                msg["is_ros"] = "true"
        send_message(
            config.INVENTORY_TOPIC, msgs.inv_message("add_host", facts, msg), extra
        )
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(extra, "success", "Message sent to inventory"),
            extra,
        )


if __name__ == "__main__":
    main()
