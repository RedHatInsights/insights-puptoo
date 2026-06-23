import json
import logging
import re
from abc import ABC, abstractmethod
from base64 import b64decode
from datetime import datetime, timedelta
from time import time

from ..mq import msgs
from ..process.profile import MAC_REGEX
from ..upload import upload_object
from ..utils import config, metrics, validators

logger = logging.getLogger("puptoo")


def _get_staletime():
    the_time = datetime.now() + timedelta(hours=29)
    return the_time.astimezone().isoformat()


def _get_owner(ident):
    s = b64decode(ident).decode("utf-8")
    identity = json.loads(s)
    if identity["identity"].get("system"):
        owner_id = identity["identity"]["system"].get("cn")
        return owner_id


def _clean_macs(facts):
    if facts["metadata"].get("mac_addresses"):
        m = re.compile(MAC_REGEX)
        facts["metadata"]["mac_addresses"] = [
            mac for mac in facts["metadata"]["mac_addresses"] if m.match(mac)
        ]
    return facts


class BaseHandler(ABC):
    @abstractmethod
    def process(self, msg: dict, extra: dict) -> dict:
        """Extract facts from the incoming message. Returns a facts dict."""

    @abstractmethod
    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
        """Build HBI message payload(s). Returns a list of dicts."""

    def handle(self, msg, service, extra, *, send_message):
        msg["elapsed_time"] = time()
        logger.info("received request_id: %s", extra["request_id"])
        send_message(
            config.TRACKER_TOPIC,
            msgs.tracker_message(extra, "received", "Received message"),
            extra,
        )
        metrics.msg_processed_count.labels(service).inc()

        facts = {}
        try:
            facts = self.process(msg, extra)

            if not facts:
                raise Exception("Empty facts extracted.")
            if not validators.validateCanonicalFacts(facts):
                raise Exception("Missing canonical fact(s).")

            yum_updates = None
            facts["stale_timestamp"] = _get_staletime()
            facts["reporter"] = "puptoo"
            if facts.get("metadata"):
                _clean_macs(facts)
            if facts.get("system_profile"):
                owner_id = _get_owner(msg["b64_identity"])
                if owner_id:
                    facts["system_profile"]["owner_id"] = owner_id
                if facts["system_profile"].get("is_ros"):
                    msg["is_ros"] = True
                if facts["system_profile"].get("is_ros_v2"):
                    msg["is_ros_v2"] = True
                if facts["system_profile"].get("is_pcp_raw_data_collected"):
                    msg["is_pcp_raw_data_collected"] = True
                if facts["system_profile"].get("is_runtimes"):
                    msg["is_runtimes"] = True
                if facts["system_profile"].get("yum_updates"):
                    yum_updates = facts["system_profile"].get("yum_updates")
                    del facts["system_profile"]["yum_updates"]

            if msg["metadata"].get("display_name"):
                facts["display_name"] = msg["metadata"]["display_name"]
            if msg["metadata"].get("ansible_host"):
                facts["ansible_host"] = msg["metadata"]["ansible_host"]

            if yum_updates and not config.DISABLE_S3_UPLOAD:
                try:
                    upload_object(yum_updates, extra, msg)
                except:
                    logger.exception("Error occurred while uploading object.")

        except Exception as e:
            metrics.msg_processed_failure.labels(service).inc()
            logger.exception(
                "Failed to process message of %s service: %s: %s",
                service,
                extra["request_id"],
                str(e),
            )
            send_message(
                config.TRACKER_TOPIC,
                msgs.tracker_message(
                    extra,
                    "error",
                    "Unable to extract facts of %s service: %s" % (service, str(e)),
                ),
                extra,
            )
            send_message(
                config.VALIDATION_TOPIC,
                msgs.validation_message(msg, facts, "failure"),
                extra,
            )
            send_message(
                config.TRACKER_TOPIC,
                msgs.tracker_message(
                    extra,
                    "failed",
                    "Validation failure. Message sent to storage broker",
                ),
                extra,
            )
        else:
            metrics.msg_processed_success.labels(service).inc()
            for hbi_msg in self.build_hbi_messages(facts, msg):
                send_message(config.INVENTORY_TOPIC, hbi_msg, extra)
            send_message(
                config.TRACKER_TOPIC,
                msgs.tracker_message(extra, "success", "Message sent to inventory"),
                extra,
            )
