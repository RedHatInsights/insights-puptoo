import json
import logging
import os
from time import time

from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split()

consumer = KafkaConsumer(
    "platform.inventory.host-ingress",
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id="pup_test_consumer",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    retry_backoff_ms=1000,
)


logging.basicConfig(
    level="INFO", format="%(threadName)s %(levelname)s %(name)s - %(message)s"
)

logger = logging.getLogger("consumer")


def main():
    for data in consumer:
        msg = data.value
        metadata = msg.get("platform_metadata", {})
        request_id = metadata.get("request_id", "unknown")
        start_time = metadata.get("elapsed_time")
        if start_time:
            elapsed = round(time() - start_time, 3)
            logger.info(
                "request_id %s took %s seconds to traverse pup",
                request_id,
                elapsed,
            )
        else:
            logger.info("received message for request_id %s", request_id)


if __name__ == "__main__":
    main()
