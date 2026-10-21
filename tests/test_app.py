from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import KafkaError
from freezegun import freeze_time
from datetime import datetime

from src.puptoo import app
from src.puptoo.exceptions import RetryExhaustedException
from src.puptoo.handlers.base import _get_staletime


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
