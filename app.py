import traceback

from prometheus_client import start_http_server

import config
import consumer
import process
import producer
import puptoo_logging

logger = puptoo_logging.initialize_logging()

produce_queue = []
consume_queue = []

def start_prometheus():
    start_http_server(config.PROMETHEUS_PORT)

def get_extra(msg):
    account = msg["account"], "unknown"
    request_id = msg["request_id"], "unknown"
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
            consume_queue.append(msg)
            logger.info("consumed message from queue: %s", msg, extra=get_extra(msg))
            break


        for consumed in consume_queue:
            extra = get_extra(consumed)
            facts = process.extraction(consumed, extra)
            if facts.get("error"):
                break
            produce_queue.append(facts)
            break

        for item in produce_queue:
            logger.info("producing message on %s", config.INVENTORY_TOPIC, extra=get_extra(msg))
            produce.send(config.INVENTORY_TOPIC, value={"data": item})
            break

        produce.flush()



if __name__ == "__main__":
    try:
        main()
    except:
        the_error = traceback.format_exc()
        logger.error(f"Failed to start Extracto with Error: {the_error}")
