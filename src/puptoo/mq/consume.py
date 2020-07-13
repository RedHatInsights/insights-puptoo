from confluent_kafka import Consumer

from ..utils import config


def init_consumer():
    consumer = Consumer(
        {
            "bootstrap.servers": ",".join(config.BOOTSTRAP_SERVERS),
            "group.id": config.APP_NAME,
            "queued.max.messages.kbytes": config.KAFKA_QUEUE_MAX_KBYTES,
            "enable.auto.commit": config.KAFKA_AUTO_COMMIT,
        }
    )

    consumer.subscribe([config.ADVISOR_TOPIC, config.COMPLIANCE_TOPIC])
    return consumer
