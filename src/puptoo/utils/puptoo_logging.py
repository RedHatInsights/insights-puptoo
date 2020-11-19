import os
import sys
import logging
from threading import local

import watchtower

from logstash_formatter import LogstashFormatterV1
from boto3.session import Session

from . import config


threadctx = local()


def config_cloudwatch(logger):
    CW_SESSION = Session(
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION_NAME,
    )
    cw_handler = watchtower.CloudWatchLogHandler(
        boto3_session=CW_SESSION,
        log_group=config.LOG_GROUP,
        stream_name=config.HOSTNAME,
        create_log_group=False,
    )
    cw_handler.setFormatter(LogstashFormatterV1())
    logger.addHandler(cw_handler)


def initialize_logging():
    kafkalogger = logging.getLogger("kafka")
    kafkalogger.setLevel("ERROR")
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

    logger = logging.getLogger(config.APP_NAME)

    if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
        logger.info("Configuring cloudwatch")
        config_cloudwatch(logger)
    else:
        logger.info("Skipping cloudwatch configuration")

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

        return True
