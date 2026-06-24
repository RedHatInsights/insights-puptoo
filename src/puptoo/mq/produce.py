from confluent_kafka import Producer

from ..utils import config
from .auth import kafka_auth_config


def init_producer():

    connection_info = {
        "bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS),
    }

    kafka_auth_config(connection_info)

    producer = Producer(connection_info)
    return producer
