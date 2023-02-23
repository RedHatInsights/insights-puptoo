import os
import sys
import logging
import socket
from threading import local
from logstash_formatter import LogstashFormatterV1

from . import config


threadctx = local()


def clowder_config():
    # Cloudwatch Configuration with Clowder
    if os.environ.get("ACG_CONFIG"):
        import app_common_python

        cfg = app_common_python.LoadedConfig
        if cfg.logging:
            cw = cfg.logging.cloudwatch
            return cw.accessKeyId, cw.secretAccessKey, cw.region, cw.logGroup, False
        else:
            return None, None, None, None, None


def non_clowder_config():
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    aws_region_name = os.getenv("AWS_REGION_NAME", None)
    aws_log_group = os.getenv("AWS_LOG_GROUP", "platform")
    create_log_group = str(os.getenv("AWS_CREATE_LOG_GROUP")).lower() == "true"
    return aws_access_key_id, aws_secret_access_key, aws_region_name, aws_log_group, create_log_group


def initialize_logging():
    if any("KUBERNETES" in k for k in os.environ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(LogstashFormatterV1())
        handler.addFilter(ContextualFilter())
        logging.root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        logging.root.addHandler(handler)
    else:
        logging.basicConfig(
            level=config.LOG_LEVEL,
            format="%(threadName)s %(levelname)s %(name)s - %(message)s",
        )

    if os.environ.get("ACG_CONFIG"):
        f = clowder_config
    else:
        f = non_clowder_config

    aws_access_key_id, aws_secret_access_key, aws_region_name, aws_log_group, create_log_group = f()

    if all((aws_access_key_id, aws_secret_access_key, aws_region_name, aws_log_group)):
        from boto3.session import Session
        import watchtower

        boto3_session = Session(aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key,
                                region_name=aws_region_name)

        # configure logging to use watchtower
        cw_handler = watchtower.CloudWatchLogHandler(boto3_session=boto3_session,
                                                  log_group=aws_log_group,
                                                  stream_name=socket.gethostname(),
                                                  create_log_group=create_log_group)

        cw_handler.setFormatter(LogstashFormatterV1())
        cw_handler.addFilter(ContextualFilter())
        logging.root.addHandler(cw_handler)

    logger = logging.getLogger(config.APP_NAME)

    return logger


class ContextualFilter(logging.Filter):
    """
    This filter gets the request_id from the message and adds it to
    each log record. This way we do not have to explicitly retreive/pass
    around the request_id for each log message
    """

    def filter(self, log_record):
        try:
            log_record.request_id = threadctx.request_id
        except Exception:
            log_record.request_id = "-1"

        try:
            log_record.account = threadctx.account
        except Exception:
            log_record.account = "000001"

        try:
            log_record.org_id = threadctx.org_id
        except Exception:
            log_record.org_id = "000001"

        return True
