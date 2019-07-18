import json

from kafka import KafkaConsumer

import config

def init_consumer():
    consumer = KafkaConsumer(config.CONSUME_TOPIC,
                             bootstrap_servers=[config.MQ],
                             group_id=config.APP_NAME,
                             value_deserializer=lambda m: json.loads(m.decode("utf-8")))
    return consumer
