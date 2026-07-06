"""Tests for OpenTelemetry helpers in src.puptoo.telemetry."""

import importlib
from unittest.mock import MagicMock, patch

import pytest

from src.puptoo.telemetry import _outbound_request_hook


def _reload_telemetry(monkeypatch, env_overrides):
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)
    import src.puptoo.telemetry as telemetry_mod

    importlib.reload(telemetry_mod)
    return telemetry_mod


def _cleanup_telemetry(monkeypatch):
    monkeypatch.setenv("OTEL_ENABLED", "false")
    import src.puptoo.telemetry as telemetry_mod

    importlib.reload(telemetry_mod)


# --- config defaults ---


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("-1", 0.0),
        ("2.0", 1.0),
        ("not_a_number", 1.0),
    ],
)
def test_otel_sampling_rate_clamping(monkeypatch, env_value, expected):
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_SAMPLING_RATE", env_value)

    import src.puptoo.telemetry as telemetry_mod

    importlib.reload(telemetry_mod)

    assert telemetry_mod.OTEL_SAMPLING_RATE == expected

    _cleanup_telemetry(monkeypatch)


def test_config_defaults_without_env_vars(monkeypatch):
    for var in [
        "OTEL_ENABLED",
        "OTEL_HTTP_OUTBOUND_ENABLED",
        "OTEL_MQ_ENABLED",
        "OTEL_SAMPLING_RATE",
        "OTEL_BSP_MAX_QUEUE_SIZE",
        "OTEL_BSP_MAX_EXPORT_BATCH_SIZE",
        "OTEL_BSP_SCHEDULE_DELAY",
        "OTEL_BSP_EXPORT_TIMEOUT",
        "OTEL_EXPORTER_OTLP_COMPRESSION",
        "OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT",
        "OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT",
    ]:
        monkeypatch.delenv(var, raising=False)

    telemetry_mod = _reload_telemetry(monkeypatch, {})

    assert telemetry_mod.OTEL_ENABLED is False
    assert telemetry_mod.OTEL_HTTP_OUTBOUND_ENABLED is True
    assert telemetry_mod.OTEL_MQ_ENABLED is True
    assert telemetry_mod.OTEL_SAMPLING_RATE == 1.0
    assert telemetry_mod.OTEL_BSP_MAX_QUEUE_SIZE == 8192
    assert telemetry_mod.OTEL_BSP_MAX_EXPORT_BATCH_SIZE == 256
    assert telemetry_mod.OTEL_BSP_SCHEDULE_DELAY == 2000
    assert telemetry_mod.OTEL_BSP_EXPORT_TIMEOUT == 10000
    assert telemetry_mod.OTEL_EXPORTER_OTLP_COMPRESSION == "gzip"
    assert telemetry_mod.OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT == 64
    assert telemetry_mod.OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT == 1024


# --- init_otel ---


def test_init_otel_skips_when_disabled(monkeypatch):
    telemetry_mod = _reload_telemetry(monkeypatch, {"OTEL_ENABLED": "false"})

    with patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider:
        telemetry_mod._otel_initialized = False
        telemetry_mod.init_otel(service_name="test")
        mock_provider.assert_not_called()
        assert telemetry_mod._otel_initialized is True


def test_init_otel_idempotent(monkeypatch):
    telemetry_mod = _reload_telemetry(monkeypatch, {"OTEL_ENABLED": "true"})

    with (
        patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider_cls,
        patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
    ):
        mock_provider_cls.return_value = MagicMock()
        telemetry_mod._otel_initialized = False
        telemetry_mod.init_otel(service_name="test")
        telemetry_mod.init_otel(service_name="test")
        assert mock_provider_cls.call_count == 1

    _cleanup_telemetry(monkeypatch)


def test_sampling_rate_applied_in_init_otel(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_SAMPLING_RATE": "0.25"}
    )

    with patch.object(telemetry_mod, "_otel_initialized", False):
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

        with (
            patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider_cls,
            patch(
                "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
            ),
        ):
            mock_provider_cls.return_value = MagicMock()
            telemetry_mod.init_otel(service_name="test")

            call_kwargs = mock_provider_cls.call_args[1]
            sampler = call_kwargs["sampler"]
            assert isinstance(sampler, TraceIdRatioBased)
            assert sampler.rate == 0.25

    _cleanup_telemetry(monkeypatch)


def test_bsp_params_passed_to_batch_span_processor(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch,
        {
            "OTEL_ENABLED": "true",
            "OTEL_BSP_MAX_QUEUE_SIZE": "4096",
            "OTEL_BSP_MAX_EXPORT_BATCH_SIZE": "128",
            "OTEL_BSP_SCHEDULE_DELAY": "3000",
            "OTEL_BSP_EXPORT_TIMEOUT": "5000",
        },
    )

    with patch.object(telemetry_mod, "_otel_initialized", False):
        with (
            patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as mock_bsp,
            patch(
                "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
            ),
        ):
            mock_bsp.return_value = MagicMock()
            telemetry_mod.init_otel(service_name="test")

            _, kwargs = mock_bsp.call_args
            assert kwargs["max_queue_size"] == 4096
            assert kwargs["max_export_batch_size"] == 128
            assert kwargs["schedule_delay_millis"] == 3000
            assert kwargs["export_timeout_millis"] == 5000

    _cleanup_telemetry(monkeypatch)


@pytest.mark.parametrize(
    "env_value,expected_compression",
    [
        ("gzip", "Gzip"),
        ("GZIP", "Gzip"),
        ("deflate", "Deflate"),
        ("none", "NoCompression"),
        ("foobar", "NoCompression"),
    ],
)
def test_exporter_compression_mapping(monkeypatch, env_value, expected_compression):
    from opentelemetry.exporter.otlp.proto.http import Compression

    telemetry_mod = _reload_telemetry(
        monkeypatch,
        {"OTEL_ENABLED": "true", "OTEL_EXPORTER_OTLP_COMPRESSION": env_value},
    )

    with patch.object(telemetry_mod, "_otel_initialized", False):
        with patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
        ) as mock_exporter:
            mock_exporter.return_value = MagicMock()
            telemetry_mod.init_otel(service_name="test")
            expected_enum = getattr(Compression, expected_compression)
            mock_exporter.assert_called_once_with(compression=expected_enum)

    _cleanup_telemetry(monkeypatch)


def test_span_limits_applied_to_tracer_provider(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch,
        {
            "OTEL_ENABLED": "true",
            "OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT": "32",
            "OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT": "512",
        },
    )

    with patch.object(telemetry_mod, "_otel_initialized", False):
        with (
            patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider_cls,
            patch(
                "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
            ),
        ):
            mock_provider_cls.return_value = MagicMock()
            telemetry_mod.init_otel(service_name="test")

            call_kwargs = mock_provider_cls.call_args[1]
            span_limits = call_kwargs["span_limits"]
            assert span_limits.max_attributes == 32
            assert span_limits.max_attribute_length == 512

    _cleanup_telemetry(monkeypatch)


# --- HTTP instrumentation ---


def test_http_instrumentation_skipped_when_disabled(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_HTTP_OUTBOUND_ENABLED": "false"}
    )

    with patch(
        "opentelemetry.instrumentation.requests.RequestsInstrumentor"
    ) as mock_instrumentor:
        telemetry_mod.instrument_outbound_http()
        mock_instrumentor.assert_not_called()

    _cleanup_telemetry(monkeypatch)


def test_http_instrumentation_runs_when_enabled(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_HTTP_OUTBOUND_ENABLED": "true"}
    )

    with patch(
        "opentelemetry.instrumentation.requests.RequestsInstrumentor"
    ) as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        telemetry_mod.instrument_outbound_http()
        instance.instrument.assert_called_once()

    _cleanup_telemetry(monkeypatch)


def test_http_instrumentation_import_error_is_handled(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_HTTP_OUTBOUND_ENABLED": "true"}
    )

    with patch.dict("sys.modules", {"opentelemetry.instrumentation.requests": None}):
        telemetry_mod.instrument_outbound_http()

    _cleanup_telemetry(monkeypatch)


# --- Kafka instrumentation ---


def test_kafka_instrumentation_helpers_skip_when_otel_disabled(monkeypatch):
    telemetry_mod = _reload_telemetry(monkeypatch, {"OTEL_ENABLED": "false"})
    producer = MagicMock()
    consumer = MagicMock()

    assert telemetry_mod.instrument_kafka_producer(producer) is producer
    assert telemetry_mod.instrument_kafka_consumer(consumer) is consumer


def test_kafka_instrumentation_helpers_skip_when_mq_disabled(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_MQ_ENABLED": "false"}
    )
    producer = MagicMock()
    consumer = MagicMock()

    assert telemetry_mod.instrument_kafka_producer(producer) is producer
    assert telemetry_mod.instrument_kafka_consumer(consumer) is consumer

    _cleanup_telemetry(monkeypatch)


def test_kafka_instrumentation_helpers_wrap_when_enabled(monkeypatch):
    telemetry_mod = _reload_telemetry(
        monkeypatch, {"OTEL_ENABLED": "true", "OTEL_MQ_ENABLED": "true"}
    )
    producer = MagicMock()
    consumer = MagicMock()
    tracer_provider = MagicMock()
    wrapped_producer = MagicMock()
    wrapped_consumer = MagicMock()

    with (
        patch("opentelemetry.trace.get_tracer_provider", return_value=tracer_provider),
        patch(
            "opentelemetry.instrumentation.confluent_kafka.ConfluentKafkaInstrumentor"
        ) as mock_instrumentor,
    ):
        mock_instrumentor.instrument_producer.return_value = wrapped_producer
        mock_instrumentor.instrument_consumer.return_value = wrapped_consumer

        assert telemetry_mod.instrument_kafka_producer(producer) is wrapped_producer
        assert telemetry_mod.instrument_kafka_consumer(consumer) is wrapped_consumer

        mock_instrumentor.instrument_producer.assert_called_once_with(
            producer, tracer_provider=tracer_provider
        )
        mock_instrumentor.instrument_consumer.assert_called_once_with(
            consumer, tracer_provider=tracer_provider
        )

    _cleanup_telemetry(monkeypatch)


# --- outbound request hook ---


def test_outbound_request_hook_updates_span_name():
    span = MagicMock()
    span.is_recording.return_value = True
    request = MagicMock()
    request.method = "GET"
    request.path_url = "/api/v1/archives"

    _outbound_request_hook(span, request)

    span.update_name.assert_called_once_with("GET /api/v1/archives")


def test_outbound_request_hook_strips_query_from_path_url():
    span = MagicMock()
    span.is_recording.return_value = True
    request = MagicMock()
    request.method = "GET"
    request.path_url = "/api/v1/archives?format=tar&limit=10"

    _outbound_request_hook(span, request)

    span.update_name.assert_called_once_with("GET /api/v1/archives")


def test_outbound_request_hook_noop_when_not_recording():
    span = MagicMock()
    span.is_recording.return_value = False
    request = MagicMock()

    _outbound_request_hook(span, request)

    span.update_name.assert_not_called()


def test_outbound_request_hook_uses_slash_when_path_empty():
    span = MagicMock()
    span.is_recording.return_value = True
    request = MagicMock()
    request.method = "GET"
    request.path_url = ""

    _outbound_request_hook(span, request)

    span.update_name.assert_called_once_with("GET /")


# --- PlatformAttributeSpanProcessor ---


def test_platform_attribute_span_processor_stamps_threadctx(monkeypatch):
    telemetry_mod = _reload_telemetry(monkeypatch, {"OTEL_ENABLED": "true"})

    from src.puptoo.utils.puptoo_logging import threadctx

    threadctx.org_id = "123456"
    threadctx.request_id = "req-abc"
    threadctx.service = "advisor"

    with patch.object(telemetry_mod, "_otel_initialized", False):
        with (
            patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider_cls,
            patch(
                "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
            ),
        ):
            mock_provider = MagicMock()
            mock_provider_cls.return_value = mock_provider
            telemetry_mod.init_otel(service_name="test")

            processors = [
                call.args[0] for call in mock_provider.add_span_processor.call_args_list
            ]
            platform_proc = processors[0]

            span = MagicMock()
            span.is_recording.return_value = True
            platform_proc.on_start(span)

            span.set_attribute.assert_any_call("rh.org_id", "123456")
            span.set_attribute.assert_any_call("rh.request_id", "req-abc")
            span.set_attribute.assert_any_call("rh.service", "advisor")

    del threadctx.org_id
    del threadctx.request_id
    del threadctx.service
    _cleanup_telemetry(monkeypatch)


def test_platform_attribute_span_processor_skips_when_not_recording(monkeypatch):
    telemetry_mod = _reload_telemetry(monkeypatch, {"OTEL_ENABLED": "true"})

    with patch.object(telemetry_mod, "_otel_initialized", False):
        with (
            patch("opentelemetry.sdk.trace.TracerProvider") as mock_provider_cls,
            patch(
                "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
            ),
        ):
            mock_provider = MagicMock()
            mock_provider_cls.return_value = mock_provider
            telemetry_mod.init_otel(service_name="test")

            processors = [
                call.args[0] for call in mock_provider.add_span_processor.call_args_list
            ]
            platform_proc = processors[0]

            span = MagicMock()
            span.is_recording.return_value = False
            platform_proc.on_start(span)

            span.set_attribute.assert_not_called()

    _cleanup_telemetry(monkeypatch)
