import json
import os
import signal
from time import time

from prometheus_client import Summary, start_http_server
from redis import Redis

from .exceptions import RetryExhaustedException
from .handlers import get_handler
from .mq import consume
from .mq import produce as produce_mod
from .mq.auth import write_kafka_cert
from .mq.produce import init_producer, send_message
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from .telemetry import (
    extract_context_from_kafka_message,
    get_tracer,
    init_otel,
    instrument_kafka_producer,
    instrument_outbound_http,
)
from .utils import config, metrics, puptoo_logging
from .utils.puptoo_logging import threadctx

CONSUMER_WAIT_TIME = Summary(
    "puptoo_consumer_wait_time", "Time spent waiting on consumer iteration"
)

logger = puptoo_logging.initialize_logging()
tracer = get_tracer(__name__)


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

        init_otel(
            service_name="insights-puptoo",
            service_version=config.IMAGE_TAG,
        )
        instrument_outbound_http()

        config.log_config()

        write_kafka_cert()

        consumer = consume.init_consumer()
        logger.info("Kafka consumer initialized")
        producer = instrument_kafka_producer(init_producer())
        produce_mod.producer = producer
        logger.info("Kafka producer initialized")
        if config.DISABLE_REDIS:
            logger.info("Redis is disabled; retry tracking will be skipped")
            redis = None
        else:
            redis = redis_client()
            logger.info(
                "Redis client connected to %s:%s", config.REDIS_HOST, config.REDIS_PORT
            )

        if not config.DISABLE_PROMETHEUS:
            logger.info("Starting Puptoo Prometheus Server")
            start_prometheus()

        logger.info("Entering main consumer loop")
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
                    logger.info("Received message with service header: %s", service)
                    handler = get_handler(service)
                    if handler:
                        logger.info(
                            "Handler found for service '%s': %s",
                            service,
                            type(handler).__name__,
                        )
                        parent_ctx = extract_context_from_kafka_message(msg)
                        msg = json.loads(msg.value().decode("utf-8"))
                        extra = get_extra(
                            msg.get("account"), msg.get("org_id"), msg.get("request_id")
                        )
                        logger.info(
                            "Processing message [request_id=%s org_id=%s account=%s service=%s]",
                            extra["request_id"],
                            extra["org_id"],
                            extra["account"],
                            service,
                        )
                        threadctx.service = service
                        with tracer.start_as_current_span(
                            "puptoo.handle_message",
                            kind=SpanKind.CONSUMER,
                            context=parent_ctx,
                            attributes={
                                "messaging.system": "kafka",
                                "messaging.destination.name": "platform.upload.announce",
                                "messaging.operation": "process",
                            },
                        ) as span:
                            try:
                                with tracer.start_as_current_span(
                                    "puptoo.redis_retry_check",
                                ):
                                    logger.info(
                                        "Checking retry count for request_id=%s",
                                        extra["request_id"],
                                    )
                                    handle_retries(redis, extra["request_id"])
                                handler.handle(
                                    msg, service, extra, send_message=send_message
                                )
                                logger.info(
                                    "Message processed successfully [request_id=%s service=%s]",
                                    extra["request_id"],
                                    service,
                                )
                                span.set_status(trace.StatusCode.OK)
                            except Exception as exc:
                                span.set_status(trace.StatusCode.ERROR, str(exc))
                                span.record_exception(exc)
                                raise
                    else:
                        logger.info(
                            "No handler registered for service '%s'; skipping message",
                            service,
                        )
                else:
                    logger.info("Received message with no 'service' header; skipping")
            except Exception:
                consumer.commit()
                logger.exception("An error occurred during message processing")
            finally:
                producer.flush()
                if not config.KAFKA_AUTO_COMMIT:
                    consumer.commit()

        logger.info("Shutdown signal received; closing consumer and flushing producer")
        consumer.close()
        producer.flush()
    except Exception:
        logger.exception("Puptoo failed with Error")


if __name__ == "__main__":
    main()
