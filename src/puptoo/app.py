import json
import os
import signal
from functools import partial
from time import time

from confluent_kafka import KafkaError
from prometheus_client import Info, Summary, start_http_server

from .handlers import get_handler
from .mq import consume, produce
from .mq.auth import write_kafka_cert
from .utils import config, metrics, puptoo_logging
from .utils.puptoo_logging import threadctx
from redis import Redis

CONSUMER_WAIT_TIME = Summary(
    "puptoo_consumer_wait_time", "Time spent waiting on consumer iteration"
)
CONSUMER_ASSIGNMENTS = Info(
    "puptoo_consumer_assignments", "List of partitions assigned to the consumer"
)

logger = puptoo_logging.initialize_logging()


def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", org_id="unknown", request_id="unknown"):
    threadctx.request_id = request_id
    threadctx.account = account
    threadctx.org_id = org_id
    return {"account": account, "org_id": org_id, "request_id": request_id}


producer = None

running = True


def handle_signal(signal, frame):
    global running
    running = False


def redis_client():
    return Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD,
        ssl=config.REDIS_SSL,
    )


def handle_retries(redis, request_id):
    if redis is None:
        return
    count = redis.get(request_id)
    if not count:
        count = 0
    if int(count) == 3:
        raise Exception(
            "Message process attempts exceeded for request_id: %s", request_id
        )
    else:
        count = int(count) + 1
        redis.set(request_id, count, ex=3600)


signal.signal(signal.SIGTERM, handle_signal)


def main():
    try:
        logger.info("Starting Puptoo Service")

        config.log_config()

        write_kafka_cert()

        consumer = consume.init_consumer()
        global producer
        producer = produce.init_producer()
        if config.DISABLE_REDIS:
            redis = None
        else:
            redis = redis_client()

        if not config.DISABLE_PROMETHEUS:
            logger.info("Starting Puptoo Prometheus Server")
            start_prometheus()

        start = time()
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: %s", msg.error())
                metrics.kafka_consume_msg_failure_count.inc()
                # Known kafka msg error that pod exiting for: SESSTMOUT, MAXPOLL
                logger.error(
                    "Puptoo exiting on kafka consumer poll error to let the pod be recreated!"
                )
                os._exit(os.EX_SOFTWARE)

            now = time()
            CONSUMER_WAIT_TIME.observe(now - start)
            start = now
            try:
                metrics.kafka_consume_msg_count.inc()
                service = dict(msg.headers() or []).get("service")
                if service:
                    service = service.decode("utf-8")
                    handler = get_handler(service)
                    if handler:
                        msg = json.loads(msg.value().decode("utf-8"))
                        extra = get_extra(
                            msg.get("account"), msg.get("org_id"), msg.get("request_id")
                        )
                        handle_retries(redis, extra["request_id"])
                        handler.handle(msg, service, extra, send_message=send_message)
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

    except KafkaError:
        metrics.msg_send_failure.labels(topic).inc()
        logger.exception(
            "Failed to produce message to [%s] topic: %s", topic, extra["request_id"]
        )


if __name__ == "__main__":
    main()
