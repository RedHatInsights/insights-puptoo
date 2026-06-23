import logging

from . import handler
from .base import BaseHandler
from ..mq import msgs
from ..process import extract
from ..utils import metrics

logger = logging.getLogger("puptoo")


@handler("advisor")
class AdvisorHandler(BaseHandler):
    def process(self, msg: dict, extra: dict) -> dict:
        metrics.extraction_count.inc()
        facts = extract(msg, extra)
        if facts.get("error"):
            metrics.extract_failure.inc()
            raise Exception("process_archive failure", facts.get("error"))
        logger.debug(
            "extracted facts from message for %s\nMessage: %s\nFacts: %s",
            extra["request_id"],
            msg,
            facts,
        )
        metrics.extract_success.inc()
        return facts

    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
        return [msgs.inv_message("add_host", facts, msg)]
