import json
import logging
import tarfile
import uuid
from io import BytesIO

import requests

from ..exceptions import FailDownloadException, FailExtractException, QPCReportException
from ..feature_flags import get_flag_value
from ..modifiers import get_modifiers
from ..mq.produce import send_message
from ..utils import config, metrics
from .validators import validate_metadata_file

LOG = logging.getLogger(__name__)

SUCCESS_CONFIRM_STATUS = "success"
FAILURE_CONFIRM_STATUS = "failure"


def download_report(consumed_message):
    report_url = consumed_message.get("url")
    if not report_url:
        raise FailDownloadException(
            f"Kafka message has no report url.  Message: {consumed_message}"
        )
    LOG.info("Downloading Report from %s", report_url)
    try:
        download_response = requests.get(report_url, timeout=120)
    except Exception as err:
        metrics.qpc_archive_failed_to_download.inc()
        raise FailDownloadException(
            f"Unexpected error for URL {report_url}. Error: {err}"
        ) from err
    metrics.qpc_archive_downloaded_success.inc()
    LOG.info("Successfully downloaded TAR from %s", report_url)
    return download_response.content


def has_canonical_facts(host):
    canonical_facts = [
        "insights_id",
        "bios_uuid",
        "ip_addresses",
        "mac_addresses",
        "vm_uuid",
        "etc_machine_id",
        "subscription_manager_id",
    ]
    return any(host.get(fact) for fact in canonical_facts)


def _tracker_message(request_obj, status, status_msg):
    return {
        "account": request_obj.get("account"),
        "org_id": request_obj.get("org_id"),
        "request_id": request_obj.get("request_id"),
        "payload_id": request_obj.get("request_id"),
        "service": "puptoo",
        "status": status,
        "status_msg": status_msg,
    }


def _print_transformed_info(host_id, transformed_obj):
    if transformed_obj is None:
        return
    log_sections = []
    for key, value in transformed_obj.items():
        if value:
            log_sections.append("%s: %s" % (key, ",".join(value)))
    if log_sections:
        LOG.info(
            "Transformed details host with id %s.%s", host_id, "\n".join(log_sections)
        )


def _upload_to_host_inventory_via_kafka(host, request_obj):
    extra = {"request_id": request_obj.get("request_id")}
    upload_msg = {
        "operation": "add_host",
        "data": host,
        "platform_metadata": {
            "request_id": host.get("system_unique_id"),
            "b64_identity": request_obj.get("b64_identity"),
            "org_id": request_obj.get("org_id"),
        },
    }
    try:
        send_message(config.INVENTORY_TOPIC, upload_msg, extra)
        request_obj["host_inventory_upload_count"] += 1
        metrics.qpc_host_uploaded.inc()
    except Exception as err:
        LOG.error("The following error occurred: %s", err)
        metrics.qpc_host_upload_failures.inc()


def process_report_slice(report_slice, request_obj):
    LOG.info(
        "Processing hosts in slice with id - %s",
        report_slice.get("report_slice_id"),
    )
    hosts = report_slice.get("hosts", [])
    org_id = request_obj.get("org_id", "")
    request_obj["total_host_count"] += len(hosts)
    for host in hosts:
        yupana_host_id = str(uuid.uuid4())
        host["yupana_host_id"] = yupana_host_id
        if has_canonical_facts(host):
            host["report_slice_id"] = report_slice.get("report_slice_id")
            request_obj["candidate_hosts"] += 1
            transformed_obj = {"removed": [], "modified": [], "missing_data": []}
            if get_flag_value("puptoo.qpc-hosts-transformation", org_id):
                for modifier in get_modifiers():
                    modifier.run(host, transformed_obj, request_obj=request_obj)
            _print_transformed_info(yupana_host_id, transformed_obj)
            _upload_to_host_inventory_via_kafka(host, request_obj)
        else:
            request_obj["hosts_without_facts"].append(
                {report_slice.get("report_slice_id"): host.get("fqdn")}
            )
            metrics.qpc_host_upload_failures.inc()


def _log_report_summary(request_obj):
    total_fingerprints = request_obj["candidate_hosts"]
    total_valid = total_fingerprints - len(request_obj["hosts_without_facts"])
    LOG.info("%s/%s hosts are valid.", total_valid, total_fingerprints)
    host_upload_msg = (
        f"{request_obj['host_inventory_upload_count']}"
        f"/{request_obj['total_host_count']}"
        " hosts has been send to the inventory service."
    )
    LOG.info(host_upload_msg)
    if request_obj["hosts_without_facts"]:
        LOG.warning(
            "%s host(s) found that contain(s) 0 canonical facts: %s.",
            len(request_obj["hosts_without_facts"]),
            request_obj["hosts_without_facts"],
        )
    if total_fingerprints == 0:
        LOG.error("Report does not contain any valid hosts.")
        raise QPCReportException()
    extra = {"request_id": request_obj.get("request_id")}
    send_message(
        config.TRACKER_TOPIC,
        _tracker_message(request_obj, "success", host_upload_msg),
        extra,
    )


def process_report(consumed_message, request_obj):
    org_id = request_obj.get("org_id", "")
    if not get_flag_value("puptoo.qpc-processing-enabled", org_id):
        LOG.info(
            "QPC processing disabled by feature flag for org_id=%s; skipping report",
            org_id,
        )
        return

    request_obj.update(
        {
            "candidate_hosts": 0,
            "hosts_without_facts": [],
            "total_host_count": 0,
            "host_inventory_upload_count": 0,
        }
    )
    extra = {"request_id": request_obj.get("request_id")}
    report_tar = download_report(consumed_message)
    send_message(
        config.TRACKER_TOPIC,
        _tracker_message(request_obj, "processing", "Report Downloaded"),
        extra,
    )
    try:
        tar = tarfile.open(fileobj=BytesIO(report_tar), mode="r:*")
        files = tar.getmembers()
        json_files = []
        metadata_file = None
        for file in files:
            if "/metadata.json" in file.name or file.name == "metadata.json":
                metadata_file = file
            elif ".json" in file.name:
                json_files.append(file)
        if json_files and metadata_file:
            try:
                valid_slice_ids = validate_metadata_file(
                    tar, metadata_file, request_obj
                )
                for report_id, num_hosts in valid_slice_ids.items():
                    for file in json_files:
                        if report_id in file.name:
                            report_slice = tar.extractfile(file)
                            LOG.info("Attempting to decode the file %s", file.name)
                            try:
                                report_slice_string = report_slice.read().decode(
                                    "utf-8"
                                )
                            except UnicodeDecodeError as error:
                                LOG.error(
                                    "Attempting to decode the file %s resulted in"
                                    " the following error: %s. Discarding file.",
                                    file.name,
                                    error,
                                )
                                metrics.qpc_extract_report_slices_failures.inc()
                                continue
                            LOG.info("Successfully decoded the file %s", file.name)
                            report_slice_json = json.loads(report_slice_string)
                            report_slice_id = report_slice_json.get(
                                "report_slice_id", ""
                            )

                            matches_metadata = True
                            mismatch_message = ""
                            if report_slice_id != report_id:
                                matches_metadata = False
                                mismatch_message += (
                                    "Metadata & filename reported the"
                                    f" 'report_slice_id' as {report_id} but the"
                                    " 'report_slice_id' inside the JSON has a"
                                    f" value of {report_slice_id}. "
                                )
                            hosts = report_slice_json.get("hosts", {})
                            if len(hosts) != num_hosts:
                                matches_metadata = False
                                mismatch_message += (
                                    f"Metadata for report slice"
                                    f" {report_slice_id} reported {num_hosts}"
                                    f" hosts but report contains {len(hosts)}"
                                    " hosts. "
                                )
                            if not matches_metadata:
                                mismatch_message += (
                                    "Metadata must match report slice data."
                                    " Discarding the report slice as invalid."
                                )
                                LOG.warning(mismatch_message)
                                continue

                            process_report_slice(report_slice_json, request_obj)

                validation_message = {
                    "hash": request_obj.get("request_id"),
                    "request_id": request_obj.get("request_id"),
                    "validation": SUCCESS_CONFIRM_STATUS,
                }
                send_message(config.VALIDATION_TOPIC, validation_message, extra)
                _log_report_summary(request_obj)
            except ValueError as error:
                raise FailExtractException(
                    f"Report is not valid JSON. Error: {error}"
                ) from error
    except tarfile.ReadError as err:
        raise FailExtractException(f"Unexpected error reading tar file: {err}") from err
