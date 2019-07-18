import config

from kafka import KafkaProducer

def init_producer():
    producer = KafkaProducer(bootstrap_servers=[config.MQ])
    return producer
