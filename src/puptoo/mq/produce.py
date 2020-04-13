from confluent_kafka import Producer

from ..utils import config


def init_producer():
    producer = Producer({"bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS)})
    return producer
