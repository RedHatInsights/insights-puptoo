import json

from kafka import KafkaProducer

from utils import config


def init_producer():
    producer = KafkaProducer(bootstrap_servers=config.BOOTSTRAP_SERVERS,
                             value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode("utf-8"))
    return producer
