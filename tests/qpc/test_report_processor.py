import io
import json
import tarfile
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.puptoo.exceptions import (
    FailDownloadException,
    FailExtractException,
    QPCReportException,
)
from src.puptoo.qpc.report_processor import (
    _log_report_summary,
    _upload_to_host_inventory_via_kafka,
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
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

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
            side_effect=lambda flag, _org_id: flag != "puptoo.qpc-processing-enabled",
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


class TestUploadToHostInventoryViaKafka:
    def _make_host_and_request(self):
        host = {
            "fqdn": "test.example.com",
            "ip_addresses": ["10.0.0.1"],
            "subscription_manager_id": "abc-123",
            "system_unique_id": "sys-unique-001",
        }
        request_obj = {
            "request_id": "req-001",
            "account": "12345",
            "org_id": "000001",
            "b64_identity": "dGVzdA==",
            "host_inventory_upload_count": 0,
        }
        return host, request_obj

    def test_sets_org_id_on_host_data(self):
        host, request_obj = self._make_host_and_request()
        with patch("src.puptoo.qpc.report_processor.send_message"):
            _upload_to_host_inventory_via_kafka(host, request_obj)
        assert host["org_id"] == "000001"

    def test_sets_account_on_host_data(self):
        host, request_obj = self._make_host_and_request()
        with patch("src.puptoo.qpc.report_processor.send_message"):
            _upload_to_host_inventory_via_kafka(host, request_obj)
        assert host["account"] == "12345"

    def test_message_data_contains_org_id_and_account(self):
        host, request_obj = self._make_host_and_request()
        with patch("src.puptoo.qpc.report_processor.send_message") as mock_send:
            _upload_to_host_inventory_via_kafka(host, request_obj)
        msg = mock_send.call_args.args[1]
        assert msg["data"]["org_id"] == "000001"
        assert msg["data"]["account"] == "12345"

    def test_platform_metadata_contains_org_id(self):
        host, request_obj = self._make_host_and_request()
        with patch("src.puptoo.qpc.report_processor.send_message") as mock_send:
            _upload_to_host_inventory_via_kafka(host, request_obj)
        msg = mock_send.call_args.args[1]
        assert msg["platform_metadata"]["org_id"] == "000001"
        assert msg["platform_metadata"]["b64_identity"] == "dGVzdA=="

    def test_increments_upload_count(self):
        host, request_obj = self._make_host_and_request()
        with patch("src.puptoo.qpc.report_processor.send_message"):
            _upload_to_host_inventory_via_kafka(host, request_obj)
        assert request_obj["host_inventory_upload_count"] == 1

    def test_handles_missing_account_gracefully(self):
        host, request_obj = self._make_host_and_request()
        del request_obj["account"]
        with patch("src.puptoo.qpc.report_processor.send_message") as mock_send:
            _upload_to_host_inventory_via_kafka(host, request_obj)
        msg = mock_send.call_args.args[1]
        assert msg["data"]["account"] is None
        assert msg["data"]["org_id"] == "000001"


class TestOrgMigrationFiltering:
    """Tests for the org migration gating logic in process_report (lines 164-174)."""

    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def _run_process_report(self, org_id="000001"):
        uuid1 = uuid.uuid4()
        report_files = _make_report_files(uuid1)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": org_id,
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
        ) as mock_upload:
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch(
                    "src.puptoo.qpc.report_processor.send_message",
                ):
                    process_report(consumed_message, request_obj)
        return mock_upload

    def test_skips_when_org_not_in_migration_list(self, monkeypatch):
        monkeypatch.setenv("QPC_ORG_MIGRATION_ENABLED", "true")
        monkeypatch.setattr(
            "src.puptoo.qpc.report_processor.config.QPC_ORG_MIGRATION_LIST",
            frozenset(["999999"]),
        )
        mock_upload = self._run_process_report(org_id="000001")
        mock_upload.assert_not_called()

    def test_proceeds_when_org_in_migration_list(self, monkeypatch):
        monkeypatch.setenv("QPC_ORG_MIGRATION_ENABLED", "true")
        monkeypatch.setattr(
            "src.puptoo.qpc.report_processor.config.QPC_ORG_MIGRATION_LIST",
            frozenset(["000001"]),
        )
        mock_upload = self._run_process_report(org_id="000001")
        mock_upload.assert_called_once()

    def test_proceeds_when_migration_disabled(self, monkeypatch):
        monkeypatch.setenv("QPC_ORG_MIGRATION_ENABLED", "false")
        monkeypatch.setattr(
            "src.puptoo.qpc.report_processor.config.QPC_ORG_MIGRATION_LIST",
            frozenset(["999999"]),
        )
        mock_upload = self._run_process_report(org_id="000001")
        mock_upload.assert_called_once()

    def test_proceeds_when_migration_list_is_none(self, monkeypatch):
        monkeypatch.setenv("QPC_ORG_MIGRATION_ENABLED", "true")
        monkeypatch.setattr(
            "src.puptoo.qpc.report_processor.config.QPC_ORG_MIGRATION_LIST",
            None,
        )
        mock_upload = self._run_process_report(org_id="000001")
        mock_upload.assert_called_once()


class TestMultiSliceReport:
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def test_processes_multiple_slices(self):
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()
        metadata_json = {
            "report_id": 1,
            "host_inventory_api_version": "1.0.0",
            "source": "qpc",
            "source_metadata": {},
            "report_slices": {
                str(uuid1): {"number_hosts": 1},
                str(uuid2): {"number_hosts": 1},
            },
        }
        report_files = {
            "metadata.json": metadata_json,
            f"{uuid1}.json": {
                "report_slice_id": str(uuid1),
                "hosts": [{"ip_addresses": "10.0.0.1"}],
            },
            f"{uuid2}.json": {
                "report_slice_id": str(uuid2),
                "hosts": [{"ip_addresses": "10.0.0.2"}],
            },
        }
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
        ) as mock_upload:
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch("src.puptoo.qpc.report_processor.send_message"):
                    process_report(consumed_message, request_obj)
        assert mock_upload.call_count == 2


class TestMetadataSliceMismatch:
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def test_skips_slice_when_id_mismatches_metadata(self):
        meta_uuid = uuid.uuid4()
        wrong_uuid = uuid.uuid4()
        report_files = {
            "metadata.json": {
                "report_id": 1,
                "host_inventory_api_version": "1.0.0",
                "source": "qpc",
                "source_metadata": {},
                "report_slices": {str(meta_uuid): {"number_hosts": 1}},
            },
            f"{meta_uuid}.json": {
                "report_slice_id": str(wrong_uuid),
                "hosts": [{"ip_addresses": "10.0.0.1"}],
            },
        }
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
        ) as mock_upload:
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch("src.puptoo.qpc.report_processor.send_message"):
                    with pytest.raises(QPCReportException):
                        process_report(consumed_message, request_obj)
        mock_upload.assert_not_called()

    def test_skips_slice_when_host_count_mismatches(self):
        slice_uuid = uuid.uuid4()
        report_files = {
            "metadata.json": {
                "report_id": 1,
                "host_inventory_api_version": "1.0.0",
                "source": "qpc",
                "source_metadata": {},
                "report_slices": {str(slice_uuid): {"number_hosts": 5}},
            },
            f"{slice_uuid}.json": {
                "report_slice_id": str(slice_uuid),
                "hosts": [{"ip_addresses": "10.0.0.1"}],
            },
        }
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        buf = create_tar_buffer(report_files)
        with patch(
            "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
        ) as mock_upload:
            with patch(
                "src.puptoo.qpc.report_processor.download_report", return_value=buf
            ):
                with patch("src.puptoo.qpc.report_processor.send_message"):
                    with pytest.raises(QPCReportException):
                        process_report(consumed_message, request_obj)
        mock_upload.assert_not_called()


class TestCorruptedArchive:
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def test_invalid_tar_raises_fail_extract(self):
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        with patch(
            "src.puptoo.qpc.report_processor.download_report",
            return_value=b"not a tar file",
        ):
            with patch("src.puptoo.qpc.report_processor.send_message"):
                with pytest.raises(FailExtractException):
                    process_report(consumed_message, request_obj)


class TestUnicodeDecodeError:
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def test_bad_encoding_skips_slice_and_raises(self):
        slice_uuid = uuid.uuid4()
        metadata_json = {
            "report_id": 1,
            "host_inventory_api_version": "1.0.0",
            "source": "qpc",
            "source_metadata": {},
            "report_slices": {str(slice_uuid): {"number_hosts": 1}},
        }
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
            meta_bytes = json.dumps(metadata_json).encode("utf-8")
            info = tarfile.TarInfo(name="metadata.json")
            info.size = len(meta_bytes)
            tar_file.addfile(tarinfo=info, fileobj=io.BytesIO(meta_bytes))
            bad_bytes = b"\x80\x81\x82\x83"
            info2 = tarfile.TarInfo(name=f"{slice_uuid}.json")
            info2.size = len(bad_bytes)
            tar_file.addfile(tarinfo=info2, fileobj=io.BytesIO(bad_bytes))
        tar_buffer.seek(0)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        with patch(
            "src.puptoo.qpc.report_processor.download_report",
            return_value=tar_buffer.getvalue(),
        ):
            with patch("src.puptoo.qpc.report_processor.send_message"):
                with pytest.raises(QPCReportException):
                    process_report(consumed_message, request_obj)


class TestNoMetadataJson:
    @pytest.fixture(autouse=True)
    def _enable_qpc_processing(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    def test_archive_without_metadata_does_not_process(self):
        slice_uuid = uuid.uuid4()
        report_json = {
            "report_slice_id": str(slice_uuid),
            "hosts": [{"ip_addresses": "10.0.0.1"}],
        }
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
            data = json.dumps(report_json).encode("utf-8")
            info = tarfile.TarInfo(name=f"{slice_uuid}.json")
            info.size = len(data)
            tar_file.addfile(tarinfo=info, fileobj=io.BytesIO(data))
        tar_buffer.seek(0)
        consumed_message = _make_consumed_message()
        request_obj = {
            "request_id": consumed_message["request_id"],
            "org_id": consumed_message["org_id"],
        }
        with patch(
            "src.puptoo.qpc.report_processor.download_report",
            return_value=tar_buffer.getvalue(),
        ):
            with patch(
                "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
            ) as mock_upload:
                with patch("src.puptoo.qpc.report_processor.send_message"):
                    process_report(consumed_message, request_obj)
            mock_upload.assert_not_called()


class TestLogReportSummary:
    def test_raises_when_zero_candidates(self):
        request_obj = {
            "candidate_hosts": 0,
            "hosts_without_facts": [],
            "total_host_count": 0,
            "host_inventory_upload_count": 0,
            "request_id": "req-001",
        }
        with pytest.raises(QPCReportException):
            _log_report_summary(request_obj)

    def test_sends_tracker_message_on_success(self):
        request_obj = {
            "candidate_hosts": 2,
            "hosts_without_facts": [],
            "total_host_count": 2,
            "host_inventory_upload_count": 2,
            "request_id": "req-001",
            "org_id": "000001",
            "account": "12345",
        }
        with patch("src.puptoo.qpc.report_processor.send_message") as mock_send:
            _log_report_summary(request_obj)
        tracker_calls = [
            c for c in mock_send.call_args_list if c.args[1].get("status") == "success"
        ]
        assert len(tracker_calls) == 1


class TestTransformationRequiredForHBI:
    """QPC_HOSTS_TRANSFORMATION_ENABLED must be true when QPC_PROCESSING_ENABLED
    is true, otherwise raw QPC host data reaches HBI with invalid types
    (e.g. string ip_addresses, invalid bios_uuid, string MTU) and fails
    HBI schema validation.
    """

    @pytest.fixture(autouse=True)
    def _enable_qpc(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")

    @staticmethod
    def _raw_qpc_host():
        return {
            "ip_addresses": "10.0.0.1",
            "bios_uuid": "not-a-valid-uuid",
            "mac_addresses": ["AA:BB:CC:DD:EE:FF", "AA:BB:CC:DD:EE:FF"],
            "system_profile": {
                "network_interfaces": [
                    {
                        "name": "eth0",
                        "mtu": "1500",
                        "ipv4_addresses": ["192.168.1.1/24"],
                    },
                ],
                "os_release": "Red Hat Enterprise Linux Server release 7.9 (Maipo)",
            },
        }

    def test_raw_host_sent_untransformed_when_disabled(self):
        """Without transformation, raw QPC data (string ip_addresses, invalid
        bios_uuid, string MTU) is sent directly to HBI and will be rejected."""
        host = self._raw_qpc_host()
        slice_id = str(uuid.uuid4())
        report_slice = {
            "report_slice_id": slice_id,
            "hosts": [host],
        }
        request_obj = {
            "org_id": "456",
            "request_id": "test-req",
            "total_host_count": 0,
            "candidate_hosts": 0,
            "hosts_without_facts": [],
            "host_inventory_upload_count": 0,
        }
        with patch(
            "src.puptoo.qpc.report_processor.get_flag_value",
            return_value=False,
        ):
            with patch(
                "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
            ) as mock_upload:
                process_report_slice(report_slice, request_obj)
                uploaded_host = mock_upload.call_args.args[0]
                assert isinstance(uploaded_host["ip_addresses"], str)
                assert uploaded_host["bios_uuid"] == "not-a-valid-uuid"
                sp = uploaded_host["system_profile"]
                assert sp["network_interfaces"][0]["mtu"] == "1500"

    def test_host_properly_transformed_when_enabled(self):
        """With transformation enabled, modifiers clean the data so HBI accepts it."""
        host = self._raw_qpc_host()
        slice_id = str(uuid.uuid4())
        report_slice = {
            "report_slice_id": slice_id,
            "hosts": [host],
        }
        request_obj = {
            "org_id": "456",
            "request_id": "test-req",
            "total_host_count": 0,
            "candidate_hosts": 0,
            "hosts_without_facts": [],
            "host_inventory_upload_count": 0,
        }
        with patch(
            "src.puptoo.qpc.report_processor.get_flag_value",
            return_value=True,
        ):
            with patch(
                "src.puptoo.qpc.report_processor._upload_to_host_inventory_via_kafka",
            ) as mock_upload:
                process_report_slice(report_slice, request_obj)
                uploaded_host = mock_upload.call_args.args[0]
                assert "bios_uuid" not in uploaded_host
                assert isinstance(
                    uploaded_host["system_profile"]["network_interfaces"][0]["mtu"],
                    int,
                )
                assert (
                    uploaded_host["system_profile"]["network_interfaces"][0][
                        "ipv4_addresses"
                    ][0]
                    == "192.168.1.1"
                )
