"""OpenTelemetry initialization for Puptoo.

Provides centralized tracing setup following the pattern established in
insights-host-inventory (app/telemetry.py). Every knob is configurable
via environment variables so stage and prod can run independent
configurations without code changes.

Usage:
    from .telemetry import init_otel, instrument_outbound_http

    init_otel(service_name="insights-puptoo")
    instrument_outbound_http()
"""

import logging
import os
from urllib.parse import urlparse

from .utils import config
from .utils.puptoo_logging import threadctx

logger = logging.getLogger(config.APP_NAME)

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
OTEL_HTTP_OUTBOUND_ENABLED = (
    os.getenv("OTEL_HTTP_OUTBOUND_ENABLED", "true").lower() == "true"
)
OTEL_MQ_ENABLED = os.getenv("OTEL_MQ_ENABLED", "true").lower() == "true"

_raw_sampling_rate = os.getenv("OTEL_SAMPLING_RATE", "1.0")
try:
    _sampling_rate = float(_raw_sampling_rate)
except ValueError:
    logger.warning(
        "Invalid OTEL_SAMPLING_RATE=%r; falling back to 1.0",
        _raw_sampling_rate,
    )
    _sampling_rate = 1.0

OTEL_SAMPLING_RATE = min(max(_sampling_rate, 0.0), 1.0)

OTEL_BSP_MAX_QUEUE_SIZE = int(os.getenv("OTEL_BSP_MAX_QUEUE_SIZE", "8192"))
OTEL_BSP_MAX_EXPORT_BATCH_SIZE = int(os.getenv("OTEL_BSP_MAX_EXPORT_BATCH_SIZE", "256"))
OTEL_BSP_SCHEDULE_DELAY = int(os.getenv("OTEL_BSP_SCHEDULE_DELAY", "2000"))
OTEL_BSP_EXPORT_TIMEOUT = int(os.getenv("OTEL_BSP_EXPORT_TIMEOUT", "10000"))

OTEL_EXPORTER_OTLP_COMPRESSION = os.getenv(
    "OTEL_EXPORTER_OTLP_COMPRESSION", "gzip"
).lower()
OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT = int(
    os.getenv("OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT", "64")
)
OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT = int(
    os.getenv("OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT", "1024")
)

_otel_initialized = False


def get_tracer(name):
    from opentelemetry import trace

    return trace.get_tracer(name)


def init_otel(service_name, service_version="unknown"):
    global _otel_initialized

    if _otel_initialized:
        return

    if not OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled (OTEL_ENABLED != 'true')")
        _otel_initialized = True
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http import Compression
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import SpanLimits, SpanProcessor, TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

    resource = Resource.create(
        attributes={
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": os.getenv("NAMESPACE", "development"),
        }
    )

    sampler = ParentBased(root=TraceIdRatioBased(OTEL_SAMPLING_RATE))
    span_limits = SpanLimits(
        max_attributes=OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT,
        max_attribute_length=OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT,
    )
    provider = TracerProvider(
        resource=resource, sampler=sampler, span_limits=span_limits
    )

    _compression_map = {"gzip": Compression.Gzip, "deflate": Compression.Deflate}
    compression = _compression_map.get(
        OTEL_EXPORTER_OTLP_COMPRESSION, Compression.NoCompression
    )
    exporter = OTLPSpanExporter(compression=compression)

    class PlatformAttributeSpanProcessor(SpanProcessor):
        def on_start(self, span, parent_context=None):
            if not span.is_recording():
                return
            span.set_attribute("rh.service", "puptoo")
            for attr, field in (
                ("rh.org_id", "org_id"),
                ("rh.request_id", "request_id"),
            ):
                value = getattr(threadctx, field, None)
                if value:
                    span.set_attribute(attr, value)

    provider.add_span_processor(PlatformAttributeSpanProcessor())
    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
            max_queue_size=OTEL_BSP_MAX_QUEUE_SIZE,
            max_export_batch_size=OTEL_BSP_MAX_EXPORT_BATCH_SIZE,
            schedule_delay_millis=OTEL_BSP_SCHEDULE_DELAY,
            export_timeout_millis=OTEL_BSP_EXPORT_TIMEOUT,
        )
    )

    trace.set_tracer_provider(provider)
    _otel_initialized = True
    logger.info(
        "OpenTelemetry initialized for service=%s version=%s",
        service_name,
        service_version,
    )
    logger.info(
        "OpenTelemetry config: sampling=%.2f http_outbound=%s mq=%s "
        "bsp_queue=%d bsp_batch=%d bsp_delay=%dms bsp_timeout=%dms "
        "compression=%s attr_limit=%d attr_len_limit=%d",
        OTEL_SAMPLING_RATE,
        OTEL_HTTP_OUTBOUND_ENABLED,
        OTEL_MQ_ENABLED,
        OTEL_BSP_MAX_QUEUE_SIZE,
        OTEL_BSP_MAX_EXPORT_BATCH_SIZE,
        OTEL_BSP_SCHEDULE_DELAY,
        OTEL_BSP_EXPORT_TIMEOUT,
        OTEL_EXPORTER_OTLP_COMPRESSION,
        OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT,
        OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT,
    )


def instrument_kafka_consumer(consumer):
    if not OTEL_ENABLED or not OTEL_MQ_ENABLED:
        return consumer

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.confluent_kafka import (
            ConfluentKafkaInstrumentor,
        )
    except ImportError:
        logger.warning(
            "Kafka consumer instrumentation unavailable; continuing without consumer spans"
        )
        return consumer

    return ConfluentKafkaInstrumentor.instrument_consumer(
        consumer, tracer_provider=trace.get_tracer_provider()
    )


def instrument_kafka_producer(producer):
    if not OTEL_ENABLED or not OTEL_MQ_ENABLED:
        return producer

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.confluent_kafka import (
            ConfluentKafkaInstrumentor,
        )
    except ImportError:
        logger.warning(
            "Kafka producer instrumentation unavailable; continuing without producer spans"
        )
        return producer

    return ConfluentKafkaInstrumentor.instrument_producer(
        producer, tracer_provider=trace.get_tracer_provider()
    )


def instrument_outbound_http():
    if not OTEL_ENABLED or not OTEL_HTTP_OUTBOUND_ENABLED:
        return

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        logger.warning(
            "HTTP instrumentation unavailable; continuing without outbound HTTP spans"
        )
        return

    RequestsInstrumentor().instrument(request_hook=_outbound_request_hook)
    logger.info("Outbound HTTP (requests library) instrumented with OpenTelemetry")


def _outbound_request_hook(span, request, *_args, **_kwargs):
    if not span or not span.is_recording():
        return
    parsed = urlparse(request.path_url)
    path = parsed.path or "/"
    span.update_name(f"{request.method} {path}")
