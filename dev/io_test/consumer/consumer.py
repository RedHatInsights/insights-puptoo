import json
import time
import logging
import os
import sys


from kafka import KafkaConsumer, KafkaProducer

consumer = KafkaConsumer("platform.inventory.host-ingress",
                         bootstrap_servers=["kafka:29092"],
                         group_id="test_consumer",
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
            logger.info("message took %s seconds to traverse pup", msg["data"]["elapsed_time"])

if __name__ == "__main__":
    time.sleep(10)
    main()
