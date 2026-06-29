from confluent_kafka import Consumer

from ..utils import config
from .auth import kafka_auth_config


def init_consumer():

    connection_info = {
        "group.id": config.APP_NAME,
        "queued.max.messages.kbytes": config.KAFKA_QUEUE_MAX_KBYTES,
        "enable.auto.commit": config.KAFKA_AUTO_COMMIT,
        "allow.auto.create.topics": config.KAFKA_ALLOW_CREATE_TOPICS,
        "bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS),
    }

    kafka_auth_config(connection_info)

    consumer = Consumer(connection_info)

    consumer.subscribe([config.ANNOUNCE_TOPIC])
    return consumer
