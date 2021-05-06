from confluent_kafka import Producer

from ..utils import config


def init_producer():
    producer = Producer({"bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS),
                         "sasl.username": config.KAFKA_SASL_USERNAME,
                         "sasl.password": config.KAFKA_SASL_PASSWORD})
    return producer
