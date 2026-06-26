from . import handler
from .base import BaseHandler
from ..mq import msgs


@handler("compliance")
class ComplianceHandler(BaseHandler):
    def process(self, msg: dict, extra: dict) -> dict:
        return msg.get("metadata") or {}

    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
        return [msgs.inv_message("add_host", facts, msg)]


@handler("malware-detection")
class MalwareDetectionHandler(ComplianceHandler):
    pass
