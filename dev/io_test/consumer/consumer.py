import json
import time
import logging
import os


from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split()

consumer = KafkaConsumer("platform.inventory.host-ingress",
                         bootstrap_servers=BOOTSTRAP_SERVERS,
                         group_id="pup_test_consumer",
                         value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                         retry_backoff_ms=1000,
                         )


logging.basicConfig(level="INFO",
                    format="%(threadName)s %(levelname)s %(name)s - %(message)s"
                    )

logger = logging.getLogger("consumer")


def main():
    while True:
        for data in consumer:
            msg = data.value
            logger.info("request_id %s took %s seconds to traverse pup", msg["data"]["request_id"], msg["data"]["elapsed_time"])


if __name__ == "__main__":
    time.sleep(10)
    main()
