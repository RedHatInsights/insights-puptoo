import os

from ..utils import config

CACERT_PATH = "/tmp/cacert"


def write_kafka_cert():
    if config.KAFKA_BROKER and config.KAFKA_BROKER.cacert:
        fd = os.open(CACERT_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(config.KAFKA_BROKER.cacert)


def kafka_auth_config(connection_info):
    if config.KAFKA_BROKER:
        if config.KAFKA_BROKER.cacert:
            connection_info["ssl.ca.location"] = CACERT_PATH
        if config.KAFKA_BROKER.sasl and config.KAFKA_BROKER.sasl.username:
            connection_info.update(
                {
                    "security.protocol": config.KAFKA_BROKER.sasl.securityProtocol,
                    "sasl.mechanisms": config.KAFKA_BROKER.sasl.saslMechanism,
                    "sasl.username": config.KAFKA_BROKER.sasl.username,
                    "sasl.password": config.KAFKA_BROKER.sasl.password,
                }
            )
    return connection_info
