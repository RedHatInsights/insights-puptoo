import os
import sys
import config
import logging

import watchtower

from logstash_formatter import LogstashFormatterV1
from boto3.session import Session


def config_cloudwatch(logger):
    CW_SESSION = Session(aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                         region_name=config.AWS_REGION_NAME)
    cw_handler = watchtower.CloudWatchLogHandler(boto3_session=CW_SESSION,
                                                 log_group=config.LOG_GROUP,
                                                 stream_name=config.NAMESPACE)
    cw_handler.setFormatter(LogstashFormatterV1())
    logger.addHandler


def initialize_logging():
    if any("KUBERNETES" in k for k in os.environ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(LogstashFormatterV1())
        logging.root.setLevel(os.getenv("LOGLEVEL", "INFO"))
        logging.root.addHandler(handler)
    else:
        logging.basicConfig(
            level=config.LOGLEVEL,
            format="%(threadName)s %(levelname)s %(name)s - %(message)s"
        )

    logger = logging.getLogger(config.APP_NAME)

    if (config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY):
        config_cloudwatch(logger)

    return logger
