import json
import signal
import re
from datetime import datetime, timedelta
from functools import partial
from time import time
from base64 import b64decode

from confluent_kafka import KafkaError
from prometheus_client import Info, Summary, start_http_server
from .upload import upload_object

from .process import extract
from .process.profile import MAC_REGEX
from .mq import consume, msgs, produce
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


def write_cert(cert):
    with open('/tmp/cacert', 'w') as f:
        f.write(cert)


def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)


def get_extra(account="unknown", org_id="unknown", request_id="unknown"):
    threadctx.request_id = request_id
    threadctx.account = account
    threadctx.org_id = org_id
    return {"account": account, "org_id": org_id, "request_id": request_id}


def get_staletime():
    the_time = datetime.now() + timedelta(hours=29)
    return the_time.astimezone().isoformat()


def get_owner(ident):
    s = b64decode(ident).decode("utf-8")
    identity = json.loads(s)
    if identity["identity"].get("system"):
        owner_id = identity["identity"]["system"].get("cn")
        return owner_id


def clean_macs(facts):
    if facts["metadata"].get("mac_addresses"):
        m = re.compile(MAC_REGEX)
        facts["metadata"]["mac_addresses"] = [mac for mac in facts["metadata"]["mac_addresses"] if m.match(mac)]
    return facts


producer = None

running = True


def handle_signal(signal, frame):
    global running
    running = False


def redis_client() :
    return Redis(host=config.REDIS_HOST, port=config.REDIS_PORT) 


def handle_retries(redis, request_id):
    if redis == None:
        return
    count = redis.get(request_id)
    if not count:
        count = 0
    if int(count) == 3:
        raise Exception("Message process attempts exceeded for request_id: %s", request_id)
    else:
        count = int(count) + 1
        redis.set(request_id, count, ex=3600)


signal.signal(signal.SIGTERM, handle_signal)


def main():
    try:
        logger.info("Starting Puptoo Service")

        config.log_config()

        if not config.DISABLE_PROMETHEUS:
            logger.info("Starting Puptoo Prometheus Server")
            start_prometheus()

        if config.KAFKA_BROKER:
            if config.KAFKA_BROKER.cacert:
                write_cert(config.KAFKA_BROKER.cacert)

        consumer = consume.init_consumer()
        global producer
        producer = produce.init_producer()
        if config.DISABLE_REDIS:
            redis = None
        else:
            redis = redis_client()

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
                service = dict(msg.headers() or []).get('service')
                if service:
                    service = service.decode("utf-8")
                    if service in ['advisor', 'compliance', 'malware-detection']:
                        msg = json.loads(msg.value().decode("utf-8"))
                        extra = get_extra(msg.get("account"), msg.get("org_id"), msg.get("request_id"))
                        handle_retries(redis, extra["request_id"])
                        handle_message(msg, service, extra)
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


def handle_message(msg, service, extra):
    msg["elapsed_time"] = time()
    logger.info("received request_id: %s", extra["request_id"])
    send_message(
        config.TRACKER_TOPIC,
        msgs.tracker_message(extra, "received", "Received message"),
        extra,
    )
    metrics.msg_count.inc()
    owner_id = get_owner(msg["b64_identity"])

    if service == "advisor":
        facts = process_archive(msg, extra)
    if service in ["compliance", "malware-detection"]:
        facts = msg.get("metadata")

    if facts:
        yum_updates=None
        facts["stale_timestamp"] = get_staletime()
        facts["reporter"] = "puptoo"
        if facts.get("metadata"):
            clean_macs(facts)
        if facts.get("system_profile"):
            if owner_id:
                facts["system_profile"]["owner_id"] = owner_id
            if facts["system_profile"].get("is_ros"):
                msg["is_ros"] = True
            if facts["system_profile"].get("is_runtimes"):
                msg["is_runtimes"] = True
            if facts["system_profile"].get("yum_updates"):
                yum_updates = facts["system_profile"].get("yum_updates")
                # delete yum_updates from system_profile as it is already present under custom_metadata 
                del facts["system_profile"]["yum_updates"]

        # Override archive hostname with name provided by client metadata
        if msg["metadata"].get("display_name"):
            facts["display_name"] = msg["metadata"]["display_name"]
        if msg["metadata"].get("ansible_host"):
            facts["ansible_host"] = msg["metadata"]["ansible_host"]   

        # Upload yum_updates to s3  
        if yum_updates:
            try:
                upload_object(yum_updates, extra, msg)
            except:
                logger.exception("Error occurred while uploading object.")

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
