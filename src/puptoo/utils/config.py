import os
import logging

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
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split(",")
CONSUME_TOPIC = os.getenv("CONSUME_TOPIC", "platform.upload.advisor")
AWS_ACCESS_KEY_ID = os.getenv("CW_AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("CW_AWS_SECRET_ACCESS_KEY", None)
AWS_REGION_NAME = os.getenv("CW_AWS_REGION_NAME", "us-east-1")
INVENTORY_TOPIC = os.getenv("INVENTORY_TOPIC", "platform.inventory.host-ingress")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://insights-inventory:8080/api/inventory/v1/hosts")
VALIDATION_TOPIC = os.getenv("VALIDATION_TOPIC", "platform.upload.validation")
FACT_EXTRACT_LOGLEVEL = os.getenv("FACT_EXTRACT_LOGLEVEL", "ERROR")
LOG_GROUP = os.getenv("LOG_GROUP", "platform-dev")
TRACKER_TOPIC = os.getenv("TRACKER_TOPIC", "platform.payload-status")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 8000))
DISABLE_PROMETHEUS = True if os.getenv("DISABLE_PROMETHEUS") == "True" else False
NAMESPACE = get_namespace()
HOSTNAME = os.environ.get("HOSTNAME")
BUILD_COMMIT = os.getenv("OPENSHIFT_BUILD_COMMIT", "not_in_openshift")
KAFKA_QUEUE_MAX_KBYTES = os.getenv("KAFKA_QUEUE_MAX_KBYTES", 1024)
