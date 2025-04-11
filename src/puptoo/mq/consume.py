from confluent_kafka import Consumer

from ..utils import config


def init_consumer():

    connection_info = {
        "group.id": config.APP_NAME,
        "queued.max.messages.kbytes": config.KAFKA_QUEUE_MAX_KBYTES,
        "enable.auto.commit": config.KAFKA_AUTO_COMMIT,
        "allow.auto.create.topics": config.KAFKA_ALLOW_CREATE_TOPICS,
        "bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS)
    }

    if config.KAFKA_BROKER:
        if config.KAFKA_BROKER.cacert:
            connection_info["ssl.ca.location"] = "/tmp/cacert"
        if config.KAFKA_BROKER.sasl and config.KAFKA_BROKER.sasl.username:
            connection_info.update(
                {
                    "security.protocol": config.KAFKA_BROKER.sasl.securityProtocol,
                    "sasl.mechanisms": config.KAFKA_BROKER.sasl.saslMechanism,
                    "sasl.username": config.KAFKA_BROKER.sasl.username,
                    "sasl.password": config.KAFKA_BROKER.sasl.password,
                }
            )

    consumer = Consumer(connection_info)

    consumer.subscribe([config.ANNOUNCE_TOPIC])
    return consumer
