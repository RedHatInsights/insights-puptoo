import json
from unittest.mock import MagicMock, patch

import pytest

from src.puptoo.exceptions import FailExtractException, FailUploadException
from src.puptoo.handlers import get_handler, handler, register, _REGISTRY
from src.puptoo.handlers.base import BaseHandler, FactsHandler


class DummyHandler(FactsHandler):
    def process(self, msg: dict, extra: dict) -> dict:  # noqa: ARG002
        return {"dummy": True}

    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:  # noqa: ARG002
        return [{"operation": "add_host", "data": facts}]


class FailingHandler(FactsHandler):
    def process(self, msg: dict, extra: dict) -> dict:  # noqa: ARG002
        raise FailExtractException("extraction failed")

    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:  # noqa: ARG002
        return []


class YumHandler(FactsHandler):
    def process(self, msg: dict, extra: dict) -> dict:  # noqa: ARG002
        return {
            "insights_id": "abc",
            "fqdn": "test.example.com",
            "system_profile": {"yum_updates": {"pkg": "1.0"}},
        }

    def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:  # noqa: ARG002
        return [{"operation": "add_host", "data": facts}]


@pytest.fixture(autouse=True)
def clean_registry():
    saved = dict(_REGISTRY)
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()
    _REGISTRY.update(saved)


# --- Registry basics ---


def test_get_handler_returns_none_for_unknown():
    assert get_handler("unknown") is None


def test_get_handler_returns_none_when_empty():
    assert get_handler("advisor") is None


def test_register_and_get_handler():
    register("test-service", DummyHandler)
    h = get_handler("test-service")
    assert h is not None
    assert isinstance(h, DummyHandler)


def test_get_handler_returns_new_instance_each_call():
    register("test-service", DummyHandler)
    h1 = get_handler("test-service")
    h2 = get_handler("test-service")
    assert h1 is not h2


# --- @handler decorator ---


def test_handler_decorator_registers():
    @handler("my-service")
    class MyHandler(FactsHandler):
        def process(self, msg: dict, extra: dict) -> dict:
            return {}

        def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
            return []

    assert _REGISTRY["my-service"] is MyHandler
    h = get_handler("my-service")
    assert isinstance(h, MyHandler)


def test_handler_decorator_returns_class_unchanged():
    @handler("svc")
    class H(FactsHandler):
        def process(self, msg: dict, extra: dict) -> dict:
            return {}

        def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
            return []

    assert H.__name__ == "H"


# --- Abstract interface ---


def test_handler_process():
    h = DummyHandler()
    result = h.process({}, {})
    assert result == {"dummy": True}


def test_handler_build_hbi_messages():
    h = DummyHandler()
    facts = {"fqdn": "test.example.com"}
    result = h.build_hbi_messages(facts, {})
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["data"] == facts


def test_base_handler_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseHandler()  # type: ignore[reportAbstractUsage]


# --- Concrete handlers ---


@pytest.fixture()
def populated_registry():
    from src.puptoo.handlers import advisor, compliance  # noqa: F401
    from src.puptoo.handlers.qpc import QPCHandler

    register("advisor", advisor.AdvisorHandler)
    register("compliance", compliance.ComplianceHandler)
    register("malware-detection", compliance.MalwareDetectionHandler)
    register("qpc", QPCHandler)


def test_dispatch_advisor(populated_registry):
    from src.puptoo.handlers.advisor import AdvisorHandler

    h = get_handler("advisor")
    assert isinstance(h, AdvisorHandler)


def test_dispatch_compliance(populated_registry):
    from src.puptoo.handlers.compliance import ComplianceHandler

    h = get_handler("compliance")
    assert isinstance(h, ComplianceHandler)


def test_dispatch_malware_detection(populated_registry):
    from src.puptoo.handlers.compliance import MalwareDetectionHandler

    h = get_handler("malware-detection")
    assert isinstance(h, MalwareDetectionHandler)


def test_dispatch_qpc_returns_handler(populated_registry):
    from src.puptoo.handlers.qpc import QPCHandler

    h = get_handler("qpc")
    assert isinstance(h, QPCHandler)


def test_dispatch_unknown_returns_none(populated_registry):
    assert get_handler("unknown") is None


def test_malware_detection_is_subclass_of_compliance():
    from src.puptoo.handlers.compliance import (
        ComplianceHandler,
        MalwareDetectionHandler,
    )

    assert issubclass(MalwareDetectionHandler, ComplianceHandler)


def test_compliance_handler_process_returns_metadata():
    from src.puptoo.handlers.compliance import ComplianceHandler

    h = ComplianceHandler()
    msg = {"metadata": {"fqdn": "host.example.com"}}
    result = h.process(msg, {})
    assert result == {"fqdn": "host.example.com"}


def test_compliance_handler_process_returns_empty_on_missing_metadata():
    from src.puptoo.handlers.compliance import ComplianceHandler

    h = ComplianceHandler()
    result = h.process({}, {})
    assert result == {}


# --- Template method (handle) ---


@patch("src.puptoo.handlers.base.upload_object")
@patch("src.puptoo.handlers.base.msgs")
@patch("src.puptoo.handlers.base.validators")
@patch("src.puptoo.handlers.base.config")
@patch("src.puptoo.handlers.base.metrics")
def test_handle_success_path(
    mock_metrics, mock_config, mock_validators, mock_msgs, mock_upload
):
    mock_validators.validateCanonicalFacts.return_value = True
    mock_config.TRACKER_TOPIC = "tracker"
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_config.DISABLE_S3_UPLOAD = True

    send = MagicMock()
    h = DummyHandler()
    msg = {"metadata": {}}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    h.handle(msg, "test", extra, send_message=send)

    topics = [call.args[0] for call in send.call_args_list]
    assert topics[0] == "tracker"
    assert "inventory" in topics
    assert topics[-1] == "tracker"
    mock_metrics.msg_processed_success.labels.assert_called_with("test")


@patch("src.puptoo.handlers.base.upload_object")
@patch("src.puptoo.handlers.base.msgs")
@patch("src.puptoo.handlers.base.validators")
@patch("src.puptoo.handlers.base.config")
@patch("src.puptoo.handlers.base.metrics")
def test_handle_error_path(
    mock_metrics, mock_config, mock_validators, mock_msgs, mock_upload
):
    mock_validators.validateCanonicalFacts.return_value = False
    mock_config.TRACKER_TOPIC = "tracker"
    mock_config.VALIDATION_TOPIC = "validation"

    send = MagicMock()
    h = DummyHandler()
    msg = {"metadata": {}}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    h.handle(msg, "test", extra, send_message=send)

    topics = [call.args[0] for call in send.call_args_list]
    assert "tracker" in topics
    assert "validation" in topics
    mock_metrics.msg_processed_failure.labels.assert_called_with("test")
    error_calls = [
        c for c in mock_msgs.tracker_message.call_args_list if c.args[1] == "error"
    ]
    assert any("Missing canonical fact(s)." in str(c) for c in error_calls)


@patch("src.puptoo.handlers.base.upload_object")
@patch("src.puptoo.handlers.base.msgs")
@patch("src.puptoo.handlers.base.validators")
@patch("src.puptoo.handlers.base.config")
@patch("src.puptoo.handlers.base.metrics")
def test_handle_empty_facts_triggers_error_path(
    mock_metrics, mock_config, mock_validators, mock_msgs, mock_upload
):
    mock_config.TRACKER_TOPIC = "tracker"
    mock_config.VALIDATION_TOPIC = "validation"

    class EmptyHandler(FactsHandler):
        def process(self, msg: dict, extra: dict) -> dict:
            return {}

        def build_hbi_messages(self, facts: dict, msg: dict) -> list[dict]:
            return []

    send = MagicMock()
    h = EmptyHandler()
    msg = {"metadata": {}}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    h.handle(msg, "test", extra, send_message=send)

    mock_metrics.msg_processed_failure.labels.assert_called_with("test")
    error_calls = [
        c for c in mock_msgs.tracker_message.call_args_list if c.args[1] == "error"
    ]
    assert any("Empty facts extracted." in str(c) for c in error_calls)


@patch("src.puptoo.handlers.base.upload_object")
@patch("src.puptoo.handlers.base.msgs")
@patch("src.puptoo.handlers.base.validators")
@patch("src.puptoo.handlers.base.config")
@patch("src.puptoo.handlers.base.metrics")
def test_handle_fail_extract_exception_type(
    mock_metrics, mock_config, mock_validators, mock_msgs, mock_upload
):
    mock_config.TRACKER_TOPIC = "tracker"
    mock_config.VALIDATION_TOPIC = "validation"

    send = MagicMock()
    h = FailingHandler()
    msg = {"metadata": {}}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    h.handle(msg, "test", extra, send_message=send)

    mock_metrics.msg_processed_failure.labels.assert_called_with("test")
    error_calls = [
        c for c in mock_msgs.tracker_message.call_args_list if c.args[1] == "error"
    ]
    assert any("extraction failed" in str(c) for c in error_calls)


@patch("src.puptoo.handlers.base._get_owner", return_value=None)
@patch("src.puptoo.handlers.base.upload_object")
@patch("src.puptoo.handlers.base.msgs")
@patch("src.puptoo.handlers.base.validators")
@patch("src.puptoo.handlers.base.config")
@patch("src.puptoo.handlers.base.metrics")
def test_handle_catches_fail_upload_and_continues(
    mock_metrics, mock_config, mock_validators, mock_msgs, mock_upload, mock_owner
):
    mock_validators.validateCanonicalFacts.return_value = True
    mock_config.TRACKER_TOPIC = "tracker"
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_config.DISABLE_S3_UPLOAD = False

    mock_upload.side_effect = FailUploadException("upload boom")

    send = MagicMock()
    h = YumHandler()
    msg = {"metadata": {}, "b64_identity": "e30="}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    h.handle(msg, "test", extra, send_message=send)

    mock_upload.assert_called_once()
    mock_metrics.msg_processed_success.labels.assert_called_with("test")
    topics = [call.args[0] for call in send.call_args_list]
    assert "inventory" in topics


# --- ENABLED_HANDLERS gating ---


@pytest.fixture()
def all_four_registered():
    """Register all four handlers (advisor, compliance, malware-detection, qpc)."""
    from src.puptoo.handlers.advisor import AdvisorHandler
    from src.puptoo.handlers.compliance import (
        ComplianceHandler,
        MalwareDetectionHandler,
    )
    from src.puptoo.handlers.qpc import QPCHandler

    register("advisor", AdvisorHandler)
    register("compliance", ComplianceHandler)
    register("malware-detection", MalwareDetectionHandler)
    register("qpc", QPCHandler)


@patch("src.puptoo.handlers.config")
def test_gating_none_serves_all(mock_config, all_four_registered):
    """ENABLED_HANDLERS=None (unset) → all four handlers available."""
    mock_config.ENABLED_HANDLERS = None
    for svc in ("advisor", "compliance", "malware-detection", "qpc"):
        assert get_handler(svc) is not None, f"{svc} should be served when unset"


@patch("src.puptoo.handlers.config")
def test_gating_filters_to_listed_handlers(mock_config, all_four_registered):
    """ENABLED_HANDLERS=["advisor", "qpc"] → only those two served."""
    mock_config.ENABLED_HANDLERS = ["advisor", "qpc"]
    assert get_handler("advisor") is not None
    assert get_handler("qpc") is not None
    assert get_handler("compliance") is None
    assert get_handler("malware-detection") is None


@patch("src.puptoo.handlers.config")
def test_gating_single_handler(mock_config, all_four_registered):
    """ENABLED_HANDLERS=["qpc"] → only qpc served."""
    mock_config.ENABLED_HANDLERS = ["qpc"]
    assert get_handler("qpc") is not None
    assert get_handler("advisor") is None
    assert get_handler("compliance") is None
    assert get_handler("malware-detection") is None


@patch("src.puptoo.handlers.config")
def test_gating_unknown_service_still_returns_none(mock_config, all_four_registered):
    """Unknown service returns None regardless of gating config."""
    mock_config.ENABLED_HANDLERS = ["advisor", "qpc"]
    assert get_handler("unknown") is None


@patch("src.puptoo.handlers.config")
def test_gating_does_not_mutate_registry(mock_config, all_four_registered):
    """Filtering happens at dispatch time, not by removing from _REGISTRY."""
    mock_config.ENABLED_HANDLERS = ["qpc"]
    assert get_handler("advisor") is None
    # Switch back to unset: advisor should reappear
    mock_config.ENABLED_HANDLERS = None
    assert get_handler("advisor") is not None


# --- QPCHandler ---


@pytest.fixture()
def qpc_registered():
    """Register the QPCHandler via its module import."""
    from src.puptoo.handlers import qpc  # noqa: F401
    from src.puptoo.handlers.qpc import QPCHandler

    register("qpc", QPCHandler)


def test_dispatch_qpc(qpc_registered):
    h = get_handler("qpc")
    assert h is not None


def test_qpc_handler_is_base_handler(qpc_registered):
    from src.puptoo.handlers.qpc import QPCHandler

    h = get_handler("qpc")
    assert isinstance(h, BaseHandler)
    assert isinstance(h, QPCHandler)
    assert not isinstance(h, FactsHandler)


@patch("src.puptoo.handlers.qpc.process_report")
@patch("src.puptoo.handlers.qpc.validate_qpc_message")
def test_qpc_handle_calls_validate_and_process(
    mock_validate, mock_process, qpc_registered
):
    from src.puptoo.handlers.qpc import QPCHandler

    request_obj = {"request_id": "req-1", "org_id": "org-1"}
    mock_validate.return_value = request_obj

    h = QPCHandler()
    msg = {"topic": "announce", "org_id": "org-1"}
    send = MagicMock()

    h.handle(msg, "qpc", {}, send_message=send)

    mock_validate.assert_called_once_with(msg)
    mock_process.assert_called_once_with(msg, request_obj)


# ---------- 2.9: QPCHandler exception→metric wiring ----------


@patch("src.puptoo.handlers.qpc.metrics")
@patch("src.puptoo.handlers.qpc.process_report")
@patch("src.puptoo.handlers.qpc.validate_qpc_message")
def test_qpc_handle_json_decode_error_no_metric(
    mock_validate, mock_process, mock_metrics, qpc_registered
):
    """JSONDecodeError is caught and logged, but no metric is incremented."""
    from src.puptoo.handlers.qpc import QPCHandler

    mock_validate.side_effect = json.JSONDecodeError("bad", "doc", 0)

    h = QPCHandler()
    h.handle({"topic": "announce"}, "qpc", {}, send_message=MagicMock())

    mock_metrics.qpc_kafka_failures.inc.assert_not_called()
    mock_metrics.qpc_extract_report_slices_failures.inc.assert_not_called()
    mock_metrics.qpc_report_processing_exceptions.inc.assert_not_called()


@patch("src.puptoo.handlers.qpc.metrics")
@patch("src.puptoo.handlers.qpc.process_report")
@patch("src.puptoo.handlers.qpc.validate_qpc_message")
def test_qpc_handle_kafka_msg_exception_increments_metric(
    mock_validate, mock_process, mock_metrics, qpc_registered
):
    """QPCKafkaMsgException increments qpc_kafka_failures."""
    from src.puptoo.exceptions import QPCKafkaMsgException
    from src.puptoo.handlers.qpc import QPCHandler

    mock_validate.side_effect = QPCKafkaMsgException("bad msg")

    h = QPCHandler()
    h.handle({"topic": "announce"}, "qpc", {}, send_message=MagicMock())

    mock_metrics.qpc_kafka_failures.inc.assert_called_once()


@patch("src.puptoo.handlers.qpc.metrics")
@patch("src.puptoo.handlers.qpc.process_report")
@patch("src.puptoo.handlers.qpc.validate_qpc_message")
def test_qpc_handle_fail_extract_exception_increments_metric(
    mock_validate, mock_process, mock_metrics, qpc_registered
):
    """FailExtractException increments qpc_extract_report_slices_failures."""
    from src.puptoo.exceptions import FailExtractException
    from src.puptoo.handlers.qpc import QPCHandler

    mock_process.side_effect = FailExtractException("extract fail")
    mock_validate.return_value = {"request_id": "r1", "org_id": "o1"}

    h = QPCHandler()
    h.handle({"topic": "announce"}, "qpc", {}, send_message=MagicMock())

    mock_metrics.qpc_extract_report_slices_failures.inc.assert_called_once()


@patch("src.puptoo.handlers.qpc.metrics")
@patch("src.puptoo.handlers.qpc.process_report")
@patch("src.puptoo.handlers.qpc.validate_qpc_message")
def test_qpc_handle_unexpected_exception_increments_metric(
    mock_validate, mock_process, mock_metrics, qpc_registered
):
    """Catch-all Exception increments qpc_report_processing_exceptions."""
    from src.puptoo.handlers.qpc import QPCHandler

    mock_process.side_effect = RuntimeError("something broke")
    mock_validate.return_value = {"request_id": "r1", "org_id": "o1"}

    h = QPCHandler()
    h.handle({"topic": "announce"}, "qpc", {}, send_message=MagicMock())

    mock_metrics.qpc_report_processing_exceptions.inc.assert_called_once()
