import json
import logging
from functools import partial

from confluent_kafka import KafkaException, Producer

from ..utils import config, metrics
from .auth import kafka_auth_config

logger = logging.getLogger(config.APP_NAME)

producer = None


def init_producer():
    global producer
    connection_info = {
        "bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS),
        "message.max.bytes": config.KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE,
    }

    kafka_auth_config(connection_info)

    producer = Producer(connection_info)
    return producer


def delivery_report(err, msg=None, extra=None):
    if err is not None:
        logger.error(
            "Message delivery for topic %s failed for request_id [%s]: %s",
            msg.topic(),
            extra["request_id"],
            err,
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
        org_id = msg.get("platform_metadata", {}).get("org_id")
        key = (
            org_id.encode("utf-8")
            if topic == config.INVENTORY_TOPIC and org_id
            else None
        )
        producer.produce(
            topic, _bytes, key, callback=partial(delivery_report, extra=extra)
        )

        if topic == config.INVENTORY_TOPIC and msg.get("system_profile"):
            msg["data"].pop("system_profile")
            logger.info("Message sent to inventory: %s", msg)

    except KafkaException:
        metrics.msg_send_failure.labels(topic).inc()
        logger.exception(
            "Failed to produce message to [%s] topic: %s", topic, extra["request_id"]
        )
