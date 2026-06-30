import json
import os
import signal
from time import time

from prometheus_client import Summary, start_http_server

from .exceptions import RetryExhaustedException
from .handlers import get_handler
from .mq import consume
from .mq.auth import write_kafka_cert
from .mq.produce import init_producer, send_message
from .utils import config, metrics, puptoo_logging
from .utils.puptoo_logging import threadctx
from redis import Redis

CONSUMER_WAIT_TIME = Summary(
    "puptoo_consumer_wait_time", "Time spent waiting on consumer iteration"
)

logger = puptoo_logging.initialize_logging()


def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", org_id="unknown", request_id="unknown"):
    threadctx.request_id = request_id
    threadctx.account = account
    threadctx.org_id = org_id
    return {"account": account, "org_id": org_id, "request_id": request_id}


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
        raise RetryExhaustedException(
            f"Message process attempts exceeded for request_id: {request_id}"
        )
    else:
        count = int(count) + 1
        redis.set(request_id, count, ex=3600)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def main():
    try:
        logger.info("Starting Puptoo Service")

        config.log_config()

        write_kafka_cert()

        consumer = consume.init_consumer()
        producer = init_producer()
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


if __name__ == "__main__":
    main()
