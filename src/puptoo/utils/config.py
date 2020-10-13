import os
import logging
from app_common_python import LoadedConfig, KafkaTopics

APP_NAME = os.getenv("APP_NAME", "insights-puptoo")

logger = logging.getLogger(APP_NAME)


def log_config():
    import sys

    for k, v in sys.modules[__name__].__dict__.items():
        if k == k.upper():
            if "AWS" in k.split("_"):
                continue
            logger.info("Using %s: %s", k, v)


def get_namespace():
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as f:
            namespace = f.read()
        return namespace
    except EnvironmentError:
        logger.info("Not running in openshift")


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GROUP_ID = os.getenv("GROUP_ID", APP_NAME)
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", LoadedConfig.kafka.brokers[0].hostname+":"+str(LoadedConfig.kafka.brokers[0].port)).split(",")
ADVISOR_TOPIC = os.getenv("CONSUME_TOPIC", KafkaTopics["platform.upload.advisor"].name)
COMPLIANCE_TOPIC = os.getenv("COMPLIANCE_TOPIC", KafkaTopics["platform.upload.compliance"].name)
AWS_ACCESS_KEY_ID = os.getenv("CW_AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("CW_AWS_SECRET_ACCESS_KEY", None)
AWS_REGION_NAME = os.getenv("CW_AWS_REGION_NAME", "us-east-1")
INVENTORY_TOPIC = os.getenv("INVENTORY_TOPIC", KafkaTopics["platform.inventory.host-ingress"].name)
VALIDATION_TOPIC = os.getenv("VALIDATION_TOPIC", KafkaTopics["platform.upload.validation"].name)
FACT_EXTRACT_LOGLEVEL = os.getenv("FACT_EXTRACT_LOGLEVEL", "ERROR")
LOG_GROUP = os.getenv("LOG_GROUP", "platform-dev")
TRACKER_TOPIC = os.getenv("TRACKER_TOPIC", KafkaTopics["platform.payload-status"].name)
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", LoadedConfig.metricsPort))
DISABLE_PROMETHEUS = True if os.getenv("DISABLE_PROMETHEUS") == "True" else False
NAMESPACE = get_namespace()
HOSTNAME = os.environ.get("HOSTNAME")
BUILD_COMMIT = os.getenv("OPENSHIFT_BUILD_COMMIT", "not_in_openshift")
KAFKA_QUEUE_MAX_KBYTES = os.getenv("KAFKA_QUEUE_MAX_KBYTES", 1024)
KAFKA_AUTO_COMMIT = os.getenv("KAFKA_AUTO_COMMIT", False)
KAFKA_ALLOW_CREATE_TOPICS = os.getenv("KAFKA_ALLOW_CREATE_TOPICS", False)
