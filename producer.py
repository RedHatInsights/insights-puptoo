import config
import json

from kafka import KafkaProducer

def init_producer():
    producer = KafkaProducer(bootstrap_servers=config.BOOTSTRAP_SERVERS,
                             value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    return producer
