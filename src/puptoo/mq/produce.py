from confluent_kafka import Producer

from ..utils import config


def init_producer():
    connection_info = {}
    if config.KAFKA_BROKER:
        connection_info[
            "bootstrap.servers"
        ] = f"{config.KAFKA_BROKER.hostname}:{config.KAFKA_BROKER.port}"
        if config.KAFKA_BROKER.cacert:
            connection_info["ssl.ca.location"] = "/tmp/cacert"
        if config.KAFKA_BROKER.sasl and config.KAFKA_BROKER.sasl.username:
            connection_info.update(
                {
                    "security.protocol": "sasl_ssl",
                    "sasl.mechanisms": "SCRAM-SHA-512",
                    "sasl.username": config.KAFKA_BROKER.sasl.username,
                    "sasl.password": config.KAFKA_BROKER.sasl.password,
                }
            )
    else:
        connection_info["bootstrap.servers"] = ",".join(config.BOOTSTRAP_SERVERS)
    
    print("producer info:\n")
    print(connection_info.keys())
    producer = Producer(connection_info)
    return producer
