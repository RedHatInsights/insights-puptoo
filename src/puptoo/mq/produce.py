from confluent_kafka import Producer

from ..utils import config


def init_producer():
    connection_info = config.kafka_config()

    producer = Producer(connection_info)
    return producer
