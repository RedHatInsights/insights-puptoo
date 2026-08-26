import pytest
from prometheus_client import Counter

from src.puptoo.utils import metrics

QPC_METRICS = [
    ("qpc_archive_downloaded_success", "puptoo_qpc_archive_downloaded_success"),
    ("qpc_archive_failed_to_download", "puptoo_qpc_archive_failed_to_download"),
    ("qpc_extract_report_slices_failures", "puptoo_qpc_extract_report_slices_failures"),
    ("qpc_report_processing_exceptions", "puptoo_qpc_report_processing_exceptions"),
    ("qpc_host_uploaded", "puptoo_qpc_host_uploaded"),
    ("qpc_host_upload_failures", "puptoo_qpc_host_upload_failures"),
    ("qpc_kafka_failures", "puptoo_qpc_kafka_failures"),
    ("qpc_incoming_hosts_counter", "puptoo_qpc_incoming_hosts_counter"),
]


def _metric_name(metric):
    return next(iter(metric.describe())).name


@pytest.mark.parametrize("attr,prometheus_name", QPC_METRICS)
def test_qpc_metric_exists_and_is_counter(attr, prometheus_name):
    metric = getattr(metrics, attr)
    assert isinstance(metric, Counter)
    assert _metric_name(metric) == prometheus_name


def test_qpc_incoming_hosts_counter_has_source_label():
    counter = metrics.qpc_incoming_hosts_counter
    labeled = counter.labels(source="test_src")

    def _get_value():
        samples = counter.collect()[0].samples
        matching = [s for s in samples if s.labels.get("source") == "test_src"]
        assert matching, "No sample found for source='test_src'"
        return matching[0].value

    before = _get_value()
    labeled.inc()
    assert _get_value() == before + 1


@pytest.mark.parametrize("attr,_", QPC_METRICS)
def test_qpc_metric_name_uses_puptoo_qpc_prefix(attr, _):
    metric = getattr(metrics, attr)
    assert _metric_name(metric).startswith("puptoo_qpc_")


def test_existing_puptoo_metrics_unchanged():
    assert _metric_name(metrics.kafka_consume_msg_count) == "puptoo_messages_consumed"
    assert _metric_name(metrics.msg_processed_count) == "puptoo_messages_processed"
    assert _metric_name(metrics.extract_failure) == "puptoo_failed_extractions"
    assert _metric_name(metrics.msg_produced) == "puptoo_messages_produced"
