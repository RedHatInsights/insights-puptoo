import json
import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from ..exceptions import FailExtractException, QPCKafkaMsgException
from ..utils.config import (
    ANNOUNCE_TOPIC,
    BYPASS_PAYLOAD_EXPIRATION,
    MAX_HOSTS_PER_REP,
)
from ..utils.metrics import qpc_incoming_hosts_counter

LOG = logging.getLogger(__name__)


def validate_qpc_message(upload_message):
    if upload_message.get("topic") == ANNOUNCE_TOPIC:
        org_id = upload_message.get("org_id")
        LOG.info("Received record on %s topic for org_id %s.", ANNOUNCE_TOPIC, org_id)
        missing_fields = []
        request_id = upload_message.get("request_id")
        url = upload_message.get("url")
        if not org_id:
            missing_fields.append("org_id")
        if not request_id:
            missing_fields.append("request_id")
        if not url:
            missing_fields.append("url")
        if missing_fields:
            raise QPCKafkaMsgException(
                f"Message missing required field(s): {', '.join(missing_fields)}."
            )

        if not BYPASS_PAYLOAD_EXPIRATION:
            check_if_url_expired(url, request_id)
        return {
            "request_id": request_id,
            "account": upload_message.get("account"),
            "org_id": org_id,
            "b64_identity": upload_message.get("b64_identity"),
        }
    else:
        LOG.error("Message not found on topic: %s", ANNOUNCE_TOPIC)


def check_if_url_expired(url, request_id):
    parsed_url_query = parse_qs(urlparse(url).query)
    creation_timestamp = parsed_url_query["X-Amz-Date"]
    expire_time = timedelta(seconds=int(parsed_url_query["X-Amz-Expires"][0]))
    creation_datatime = datetime.strptime(str(creation_timestamp[0]), "%Y%m%dT%H%M%SZ")

    if datetime.now().replace(microsecond=0) > (creation_datatime + expire_time):
        raise QPCKafkaMsgException(
            f"Request_id = {request_id} is already expired and cannot be processed:"
            f"Creation time = {creation_datatime}, Expiry interval = {expire_time}."
        )


def validate_metadata_file(tar, metadata, request_obj):
    LOG.info("Attempting to decode the file %s", metadata.name)
    metadata_file = tar.extractfile(metadata)
    try:
        metadata_str = metadata_file.read().decode("utf-8")
    except UnicodeDecodeError as error:
        LOG.error(
            "Attempting to decode the file %s the following error occured: %s."
            " Discarding file.",
            metadata_file.name,
            error,
        )
        return {}

    LOG.info("Successfully decoded the file %s", metadata.name)
    metadata_json = json.loads(metadata_str)
    required_keys = [
        "report_id",
        "host_inventory_api_version",
        "source",
        "report_slices",
    ]
    missing_keys = []
    for key in required_keys:
        required_key = metadata_json.get(key)
        if not required_key:
            missing_keys.append(key)

    if missing_keys:
        missing_keys_str = ", ".join(missing_keys)
        raise FailExtractException(
            f"Metadata is missing required fields: {missing_keys_str}"
        )

    request_obj["report_platform_id"] = metadata_json.get("report_id")
    request_obj["source"] = metadata_json.get("source")
    source_metadata = metadata_json.get("source_metadata")
    if source_metadata:
        LOG.info("The following source metadata was uploaded: %s", source_metadata)

    invalid_slice_ids = {}
    valid_slice_ids = {}
    report_slices = metadata_json.get("report_slices", {})

    total_hosts_in_report = 0
    for report_slice_id, report_info in report_slices.items():
        num_hosts = int(report_info.get("number_hosts", MAX_HOSTS_PER_REP + 1))
        if num_hosts <= MAX_HOSTS_PER_REP:
            total_hosts_in_report += num_hosts
            valid_slice_ids[report_slice_id] = num_hosts
        else:
            invalid_slice_ids[report_slice_id] = num_hosts
    qpc_incoming_hosts_counter.labels(source=request_obj["source"]).inc(
        total_hosts_in_report
    )

    if invalid_slice_ids:
        for report_slice_id, num_hosts in invalid_slice_ids.items():
            LOG.warning(
                "Report %s has %s hosts. There must be no more than %s hosts"
                " per report.",
                report_slice_id,
                num_hosts,
                MAX_HOSTS_PER_REP,
            )

    return valid_slice_ids
