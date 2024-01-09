import os
import logging

APP_NAME = os.getenv("APP_NAME", "insights-puptoo")

logger = logging.getLogger(APP_NAME)

CLOWDER_ENABLED = True if os.getenv("CLOWDER_ENABLED", default="False").lower() in ["true", "t", "yes", "y"] else False


def log_config():
    import sys

    for k, v in sys.modules[__name__].__dict__.items():
        if k == k.upper():
            if "AWS" in k.split("_"):
                continue
            logger.info("Using %s: %s", k, v)

    if CLOWDER_ENABLED:
        logger.info("Using CLOWDAPP KAFKA_BROKER: %s:%s",
                    LoadedConfig.kafka.brokers[0].hostname,
                    LoadedConfig.kafka.brokers[0].port)


def get_namespace():
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as f:
            namespace = f.read()
        return namespace
    except EnvironmentError:
        logger.info("Not running in openshift")


# Shim layer for dual support of using Clowder and Legacy Mode
if CLOWDER_ENABLED:
    logger.info("Using Clowder Operator...")
    from app_common_python import LoadedConfig, KafkaTopics, KafkaServers
    BOOTSTRAP_SERVERS = KafkaServers
    KAFKA_BROKER = LoadedConfig.kafka.brokers[0]
    ANNOUNCE_TOPIC = os.getenv("ANNOUNCE_TOPIC", KafkaTopics["platform.upload.announce"].name)
    INVENTORY_TOPIC = os.getenv("INVENTORY_TOPIC") or KafkaTopics["platform.inventory.host-ingress-p1"].name
    VALIDATION_TOPIC = os.getenv("VALIDATION_TOPIC", KafkaTopics["platform.upload.validation"].name)
    TRACKER_TOPIC = os.getenv("TRACKER_TOPIC", KafkaTopics["platform.payload-status"].name)
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", LoadedConfig.metricsPort))
    LOG_GROUP = os.getenv("LOG_GROUP", LoadedConfig.logging.cloudwatch.logGroup)

    # Storage secrets
    BUCKET_NAME = os.getenv("PUPTOO_BUCKET", LoadedConfig.objectStore.buckets[0].requestedName)
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", f'{LoadedConfig.objectStore.hostname}:{LoadedConfig.objectStore.port}')
    AWS_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY", LoadedConfig.objectStore.buckets[0].accessKey)
    AWS_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY", LoadedConfig.objectStore.buckets[0].secretKey)
    USE_SSL = os.getenv("USE_SSL", LoadedConfig.objectStore.tls)
    REDIS_HOST = LoadedConfig.inMemoryDb.hostname
    REDIS_PORT = LoadedConfig.inMemoryDb.port

else:
    KAFKA_BROKER = None
    BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split(",")
    ANNOUNCE_TOPIC = os.getenv("ANNOUNCE_TOPIC", "platform.upload.announce")
    INVENTORY_TOPIC = os.getenv("INVENTORY_TOPIC", "platform.inventory.host-ingress")
    VALIDATION_TOPIC = os.getenv("VALIDATION_TOPIC", "platform.upload.validation")
    TRACKER_TOPIC = os.getenv("TRACKER_TOPIC", "platform.payload-status")
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 8000))
    LOG_GROUP = os.getenv("LOG_GROUP", "platform-dev")

    # Storage secrets
    BUCKET_NAME = os.getenv("PUPTOO_BUCKET", "insights-upload-puptoo")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", "minio:9000")
    AWS_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY", os.getenv("MINIO_ACCESS_KEY", None))
    AWS_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY", os.getenv("MINIO_SECRET_KEY", None))
    USE_SSL = os.getenv("USE_SSL", False)
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GROUP_ID = os.getenv("GROUP_ID", APP_NAME)
FACT_EXTRACT_LOGLEVEL = os.getenv("FACT_EXTRACT_LOGLEVEL", "ERROR")
DISABLE_PROMETHEUS = True if os.getenv("DISABLE_PROMETHEUS") == "True" else False
MAX_EXTRACTED_SIZE = os.getenv("MAX_EXTRACTED_SIZE", 1000000000)  # 1GB Default
NAMESPACE = get_namespace()
HOSTNAME = os.environ.get("HOSTNAME")
BUILD_COMMIT = os.getenv("OPENSHIFT_BUILD_COMMIT", "not_in_openshift")
KAFKA_QUEUE_MAX_KBYTES = os.getenv("KAFKA_QUEUE_MAX_KBYTES", 1024)
KAFKA_AUTO_COMMIT = os.getenv("KAFKA_AUTO_COMMIT", False)
KAFKA_ALLOW_CREATE_TOPICS = os.getenv("KAFKA_ALLOW_CREATE_TOPICS", False)
KAFKA_LOGGER = os.getenv("KAFKA_LOGGER", "ERROR").upper()
