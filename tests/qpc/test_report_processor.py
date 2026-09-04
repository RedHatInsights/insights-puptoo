import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.puptoo.exceptions import FailDownloadException, QPCReportException
from src.puptoo.qpc.report_processor import (
    download_report,
    has_canonical_facts,
    process_report,
    process_report_slice,
)
from tests.qpc.conftest import create_tar_buffer


def _make_report_files(uuid1, num_hosts=1, hosts=None):
    if hosts is None:
        hosts = [{str(uuid1): {"key": "value"}, "ip_addresses": "127.0.0.1"}]
    metadata_json = {
        "report_id": 1,
        "host_inventory_api_version": "1.0.0",
        "source": "qpc",
        "source_metadata": {"foo": "bar"},
        "report_slices": {str(uuid1): {"number_hosts": num_hosts}},
    }
    report_json = {
        "report_slice_id": str(uuid1),
        "hosts": hosts,
    }
    return {
        "metadata.json": metadata_json,
        f"{uuid1}.json": report_json,
    }


def _make_consumed_message():
    return {
        "account": "12345",
        "org_id": "123",
        "request_id": "32bcf6e59d03/IhactaBNbg-000001",
        "url": (
            "http://minio:9000/insights-upload-perma"
            f"?X-Amz-Date={datetime.now().strftime('%Y%m%dT%H%M%SZ')}"
            "&X-Amz-Expires=86400"
        ),
    }


class TestHasCanonicalFacts:
    def test_true_with_insights_id(self):
        assert has_canonical_facts({"insights_id": "123"}) is True

    def test_true_with_ip_addresses(self):
        assert has_canonical_facts({"ip_addresses": "127.0.0.1"}) is True

    def test_false_with_empty_host(self):
        assert has_canonical_facts({}) is False

    def test_false_with_unrelated_keys(self):
        assert has_canonical_facts({"fqdn": "test.example.com"}) is False


class TestDownloadReport:
    def test_success(self):
        download_response = Mock()
        download_response.content = b"test_content"
        with patch(
            "src.puptoo.qpc.report_processor.requests.get",
            return_value=download_response,
        ) as mock_get:
            result = download_report({"url": "https://example.com/report.tar.gz"})
        assert result == b"test_content"
        mock_get.assert_called_once_with(
            "https://example.com/report.tar.gz", timeout=120
        )

    def test_missing_url_raises(self):
        with pytest.raises(FailDownloadException):
            download_report({})

    def test_request_failure_raises(self):
        with patch(
            "src.puptoo.qpc.report_processor.requests.get",
            side_effect=Exception("connection refused"),
        ):
            with pytest.raises(FailDownloadException):
                download_report({"url": "https://example.com/report.tar.gz"})


class TestProcessReport:
    def test_without_canonical_facts_raises(self):
        uuid1 = uuid.uuid4()
        hosts = [{"key": "value", "fqdn": "test.example.com"}]
        report_files = _make_report_files(uuid1, num_hosts=1, hosts=hosts)
        consumed_message = _make_consumed_message()
        request_obj = {"org_id": consumed_message["org_id"]}
        buf = create_tar_buffer(report_files)
        with patch("src.puptoo.qpc.report_processor.download_report", return_value=buf):
            with patch(
                "src.puptoo.qpc.report_processor.send_message", return_value=None
            ):
                with pytest.raises(QPCReportException):
                    process_report(consumed_message, request_obj)

    def test_happy_path(self):
        uuid1 = uuid.uuid4()
        report_files = _make_report_files(uuid1)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
            return_value=None,
        ) as mock_upload:
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch(
                    "src.puptoo.qpc.report_processor.send_message", return_value=None
                ):
                    process_report(consumed_message, request_obj)
        mock_upload.assert_called_once()

    def test_validation_message_sent_once_per_report(self):
        uuid1 = uuid.uuid4()
        hosts = [
            {"ip_addresses": "10.0.0.1"},
            {"ip_addresses": "10.0.0.2"},
        ]
        report_files = _make_report_files(uuid1, num_hosts=2, hosts=hosts)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
        ):
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch(
                    "src.puptoo.qpc.report_processor.send_message",
                ) as mock_send:
                    process_report(consumed_message, request_obj)
        validation_calls = [
            c
            for c in mock_send.call_args_list
            if c.args[1].get("validation") == "success"
        ]
        assert len(validation_calls) == 1

    def test_skips_when_processing_disabled(self):
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        with patch(
            "src.puptoo.qpc.report_processor.get_flag_value",
            side_effect=lambda flag, org_id: flag != "puptoo.qpc-processing-enabled",
        ):
            with patch(
                "src.puptoo.qpc.report_processor.download_report"
            ) as mock_download:
                process_report(consumed_message, request_obj)
                mock_download.assert_not_called()

    def test_uses_inventory_topic_from_config(self):
        uuid1 = uuid.uuid4()
        report_files = _make_report_files(uuid1)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch("src.puptoo.qpc.report_processor.download_report", return_value=buf):
            with patch(
                "src.puptoo.qpc.report_processor.send_message",
            ) as mock_send:
                with patch(
                    "src.puptoo.qpc.report_processor.config.INVENTORY_TOPIC",
                    "custom.inventory.topic",
                ):
                    process_report(consumed_message, request_obj)
        inventory_calls = [
            c for c in mock_send.call_args_list if c.args[0] == "custom.inventory.topic"
        ]
        assert len(inventory_calls) == 1


class TestProcessReportSliceFlags:
    def _make_slice_and_request(self):
        slice_id = str(uuid.uuid4())
        report_slice = {
            "report_slice_id": slice_id,
            "hosts": [{"ip_addresses": "10.0.0.1"}],
        }
        request_obj = {
            "org_id": "456",
            "request_id": "test-req",
            "total_host_count": 0,
            "candidate_hosts": 0,
            "hosts_without_facts": [],
            "host_inventory_upload_count": 0,
        }
        return report_slice, request_obj

    def test_skips_modifiers_when_transformation_disabled(self):
        report_slice, request_obj = self._make_slice_and_request()
        with patch(
            "src.puptoo.qpc.report_processor.get_flag_value",
            return_value=False,
        ):
            with patch(
                "src.puptoo.qpc.report_processor.get_modifiers"
            ) as mock_get_modifiers:
                with patch(
                    "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka"
                ):
                    process_report_slice(report_slice, request_obj)
                    mock_get_modifiers.assert_not_called()

    def test_runs_modifiers_when_transformation_enabled(self):
        report_slice, request_obj = self._make_slice_and_request()
        with patch(
            "src.puptoo.qpc.report_processor.get_flag_value",
            return_value=True,
        ):
            with patch(
                "src.puptoo.qpc.report_processor.get_modifiers",
                return_value=[],
            ) as mock_get_modifiers:
                with patch(
                    "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka"
                ):
                    process_report_slice(report_slice, request_obj)
                    mock_get_modifiers.assert_called_once()
