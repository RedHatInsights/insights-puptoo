from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import KafkaError
from freezegun import freeze_time

from src.puptoo import app
from src.puptoo.exceptions import (
    FailExtractException,
    FailUploadException,
    RetryExhaustedException,
)
from src.puptoo.handlers.base import FactsHandler, _get_staletime


@freeze_time("2019-7-23")
def test_get_staletime():
    dtz = datetime.fromtimestamp(1563944400).astimezone()
    assert _get_staletime() == dtz.isoformat()


def test_get_extra():

    expected = {"account": "123456", "org_id": "654321", "request_id": "abdc-1234"}
    assert expected == app.get_extra("123456", "654321", "abdc-1234")
    expected = {"account": "unknown", "org_id": "unknown", "request_id": "unknown"}
    assert expected == app.get_extra()


# --- handle_retries ---


def test_handle_retries_skips_when_redis_is_none():
    assert app.handle_retries(None, "req-1") is None


def test_handle_retries_increments_on_first_call():
    redis = MagicMock()
    redis.get.return_value = None
    app.handle_retries(redis, "req-1")
    redis.set.assert_called_once_with("req-1", 1, ex=3600)


def test_handle_retries_increments_existing_count():
    redis = MagicMock()
    redis.get.return_value = b"1"
    app.handle_retries(redis, "req-1")
    redis.set.assert_called_once_with("req-1", 2, ex=3600)


def test_handle_retries_raises_at_max_retries():
    redis = MagicMock()
    redis.get.return_value = b"3"
    with pytest.raises(RetryExhaustedException, match="req-1"):
        app.handle_retries(redis, "req-1")
    redis.set.assert_not_called()


# --- consume counter labeling ---


def _setup_consumer_one_shot(mock_consume, mock_msg):
    """Wire mock consumer to deliver exactly one message then stop the loop."""
    mock_consumer = MagicMock()
    mock_consume.init_consumer.return_value = mock_consumer

    def one_shot(timeout):
        app.running = False
        return mock_msg

    mock_consumer.poll.side_effect = one_shot
    return mock_consumer


@pytest.mark.parametrize(
    "scenario", ["success", "extraction", "validation", "optional_upload"]
)
def test_consumer_span_preserves_handled_failure(monkeypatch, scenario):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from opentelemetry.trace import StatusCode

    from src.puptoo.handlers import base

    class Handler(FactsHandler):
        def process(self, msg, extra):
            if scenario == "extraction":
                raise FailExtractException("extraction failed")
            profile = (
                {"yum_updates": {"pkg": "1.0"}} if scenario == "optional_upload" else {}
            )
            return {"fqdn": "host.example.com", "system_profile": profile}

        def build_hbi_messages(self, facts, msg):
            return [{"data": facts}]

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(app, "tracer", provider.get_tracer(__name__))
    config = MagicMock(
        DISABLE_REDIS=True,
        DISABLE_PROMETHEUS=True,
        KAFKA_AUTO_COMMIT=False,
        DISABLE_S3_UPLOAD=False,
        TRACKER_TOPIC="tracker",
        INVENTORY_TOPIC="inventory",
        VALIDATION_TOPIC="validation",
    )
    monkeypatch.setattr(app, "config", config)
    monkeypatch.setattr(base, "config", config)
    monkeypatch.setattr(
        base.validators,
        "validateCanonicalFacts",
        lambda facts: scenario != "validation",
    )
    monkeypatch.setattr(base, "_get_owner", lambda identity: None)
    monkeypatch.setattr(
        base,
        "upload_object",
        MagicMock(side_effect=FailUploadException("upload failed")),
    )
    for name in (
        "init_otel",
        "instrument_outbound_http",
        "write_kafka_cert",
        "init_producer",
        "instrument_kafka_producer",
        "send_message",
    ):
        monkeypatch.setattr(app, name, MagicMock())
    monkeypatch.setattr(app, "extract_context_from_kafka_message", lambda msg: None)
    monkeypatch.setattr(app, "get_handler", lambda service: Handler())
    monkeypatch.setattr(app, "consume", MagicMock())
    msg = MagicMock()
    msg.error.return_value = None
    msg.headers.return_value = [("service", b"advisor")]
    msg.value.return_value = b'{"metadata": {}, "org_id": "org", "request_id": "req", "b64_identity": "e30="}'
    consumer = _setup_consumer_one_shot(app.consume, msg)
    monkeypatch.setattr(app, "running", True)
    try:
        app.main()
        span = next(
            s
            for s in exporter.get_finished_spans()
            if s.name == "puptoo.handle_message"
        )
        failed = scenario in ("extraction", "validation")
        assert span.status.status_code == (
            StatusCode.ERROR if failed else StatusCode.UNSET
        )
        assert any(e.name == "exception" for e in span.events) == failed
        topics = [call.args[0] for call in app.send_message.call_args_list]
        assert ("inventory" in topics) == (not failed)
        consumer.commit.assert_called_once_with()
    finally:
        provider.shutdown()


@patch("src.puptoo.app.get_handler", return_value=None)
@patch("src.puptoo.app.init_otel")
@patch("src.puptoo.app.instrument_outbound_http")
@patch("src.puptoo.app.instrument_kafka_producer", side_effect=lambda p: p)
@patch("src.puptoo.app.init_producer")
@patch("src.puptoo.app.write_kafka_cert")
@patch("src.puptoo.app.produce_mod")
@patch("src.puptoo.app.metrics")
@patch("src.puptoo.app.consume")
@patch("src.puptoo.app.config")
def test_consume_counter_labels_with_app_name_not_message_service(
    mock_config,
    mock_consume,
    mock_metrics,
    mock_produce_mod,
    mock_write_cert,
    mock_init_producer,
    mock_instrument,
    mock_outbound,
    mock_init_otel,
    mock_get_handler,
):
    """kafka_consume_msg_count must use APP_NAME (pod identity), not the
    Kafka message's service header. Both consumer groups receive every message,
    so labeling by message type would double-count every consume event."""
    mock_config.APP_NAME = "insights-puptoo"
    mock_config.DISABLE_REDIS = True
    mock_config.DISABLE_PROMETHEUS = True
    mock_config.KAFKA_AUTO_COMMIT = False

    # QPC message arriving at the advisor pod — header says "qpc"
    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.headers.return_value = [("service", b"qpc")]

    counter_series = MagicMock()
    mock_metrics.kafka_consume_msg_count.labels.return_value = counter_series

    _setup_consumer_one_shot(mock_consume, mock_msg)
    app.running = True
    app.main()

    mock_metrics.kafka_consume_msg_count.labels.assert_called_once_with(
        "insights-puptoo"
    )
    counter_series.inc.assert_called_once()


@patch("src.puptoo.app.os")
@patch("src.puptoo.app.init_otel")
@patch("src.puptoo.app.instrument_outbound_http")
@patch("src.puptoo.app.instrument_kafka_producer", side_effect=lambda p: p)
@patch("src.puptoo.app.init_producer")
@patch("src.puptoo.app.write_kafka_cert")
@patch("src.puptoo.app.produce_mod")
@patch("src.puptoo.app.metrics")
@patch("src.puptoo.app.consume")
@patch("src.puptoo.app.config")
def test_consume_failure_counter_labels_with_app_name(
    mock_config,
    mock_consume,
    mock_metrics,
    mock_produce_mod,
    mock_write_cert,
    mock_init_producer,
    mock_instrument,
    mock_outbound,
    mock_init_otel,
    mock_os,
):
    """kafka_consume_msg_failure_count must also use APP_NAME, not message type."""
    mock_config.APP_NAME = "insights-puptoo"
    mock_config.DISABLE_REDIS = True
    mock_config.DISABLE_PROMETHEUS = True
    mock_config.KAFKA_AUTO_COMMIT = False
    mock_os._exit.side_effect = SystemExit

    mock_msg = MagicMock()
    mock_msg.error.return_value = KafkaError(KafkaError._ALL_BROKERS_DOWN)

    failure_series = MagicMock()
    mock_metrics.kafka_consume_msg_failure_count.labels.return_value = failure_series

    _setup_consumer_one_shot(mock_consume, mock_msg)
    app.running = True
    with pytest.raises(SystemExit):
        app.main()

    mock_metrics.kafka_consume_msg_failure_count.labels.assert_called_once_with(
        "insights-puptoo"
    )
    failure_series.inc.assert_called_once()
