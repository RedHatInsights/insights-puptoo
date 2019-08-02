import json

from kafka import KafkaConsumer

from utils import config

def init_consumer():
    consumer = KafkaConsumer(config.CONSUME_TOPIC,
                             bootstrap_servers=config.BOOTSTRAP_SERVERS,
                             group_id=config.APP_NAME,
                             value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                             retry_backoff_ms=1000,
                             consumer_timeout_ms=200)
    return consumer
