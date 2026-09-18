import json
import logging

from . import handler
from .base import BaseHandler
from ..exceptions import FailExtractException, QPCKafkaMsgException
from ..qpc.report_processor import process_report
from ..qpc.validators import validate_qpc_message
from ..utils import metrics

logger = logging.getLogger(__name__)


@handler("qpc")
class QPCHandler(BaseHandler):
    def handle(self, msg: dict, service: str, extra: dict, *, send_message) -> None:
        try:
            request_obj = validate_qpc_message(msg)
            process_report(msg, request_obj)
        except json.JSONDecodeError:
            logger.exception("QPC message is not valid JSON")
        except QPCKafkaMsgException:
            metrics.qpc_kafka_failures.inc()
            logger.exception("Invalid QPC Kafka message")
        except FailExtractException:
            metrics.qpc_extract_report_slices_failures.inc()
            logger.exception("Failed to extract QPC report")
        except Exception:
            metrics.qpc_report_processing_exceptions.inc()
            logger.exception("Unexpected error processing QPC message")
