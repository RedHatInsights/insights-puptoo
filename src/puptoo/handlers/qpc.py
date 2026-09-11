import logging

from . import handler
from .base import BaseHandler
from ..qpc.report_processor import process_report
from ..qpc.validators import validate_qpc_message

logger = logging.getLogger(__name__)


@handler("qpc")
class QPCHandler(BaseHandler):
    def handle(self, msg: dict, service: str, extra: dict, *, send_message) -> None:
        request_obj = validate_qpc_message(msg)
        process_report(msg, request_obj)
