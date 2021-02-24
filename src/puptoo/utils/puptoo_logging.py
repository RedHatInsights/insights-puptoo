import os
import sys
import logging
from threading import local

from . import config


threadctx = local()


def initialize_logging():
    kafkalogger = logging.getLogger("kafka")
    kafkalogger.setLevel("ERROR")
    if any("KUBERNETES" in k for k in os.environ):
        handler = logging.StreamHandler(sys.stderr)
        handler.addFilter(ContextualFilter())
        logging.root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        logging.root.addHandler(handler)
    else:
        logging.basicConfig(
            level=config.LOG_LEVEL,
            format="%(threadName)s %(levelname)s %(name)s - %(message)s",
        )

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

        return True
