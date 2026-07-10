import json
from unittest.mock import ANY, MagicMock, patch

from confluent_kafka import KafkaError, KafkaException

from src.puptoo.mq import produce
from src.puptoo.mq.produce import delivery_report, init_producer, send_message


@patch("src.puptoo.mq.produce.kafka_auth_config")
@patch("src.puptoo.mq.produce.Producer")
def test_init_producer_sets_module_global(mock_producer_cls, mock_auth):
    mock_producer_cls.return_value = MagicMock()
    result = init_producer()
    assert produce.producer is result
    assert produce.producer is not None
    mock_auth.assert_called_once_with(ANY)


@patch("src.puptoo.mq.produce.kafka_auth_config")
@patch("src.puptoo.mq.produce.Producer")
@patch("src.puptoo.mq.produce.config")
def test_init_producer_includes_message_max_bytes(
    mock_config, mock_producer_cls, mock_auth
):
    mock_config.BOOTSTRAP_SERVERS = ["localhost:9092"]
    mock_config.KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE = 2097152
    init_producer()
    connection_info = mock_producer_cls.call_args[0][0]
    assert connection_info["message.max.bytes"] == 2097152
    mock_auth.assert_called_once_with(ANY)


@patch("src.puptoo.mq.produce.config")
@patch("src.puptoo.mq.produce.metrics")
def test_send_message_produces_to_topic(mock_metrics, mock_config):
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_producer = MagicMock()
    produce.producer = mock_producer

    topic = "platform.payload-status"
    msg = {"operation": "add_host", "platform_metadata": {}}
    extra = {"request_id": "req-1", "account": "acct", "org_id": "org"}

    send_message(topic, msg, extra)

    mock_producer.produce.assert_called_once()
    call_args = mock_producer.produce.call_args
    assert call_args[0][0] == topic
    assert json.loads(call_args.kwargs["value"].decode("utf-8")) == msg


@patch("src.puptoo.mq.produce.config")
@patch("src.puptoo.mq.produce.metrics")
def test_send_message_uses_org_id_key_for_inventory(mock_metrics, mock_config):
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_producer = MagicMock()
    produce.producer = mock_producer

    msg = {"platform_metadata": {"org_id": "org-123"}, "data": {"system_profile": {}}}
    extra = {"request_id": "req-1"}

    send_message("inventory", msg, extra)

    call_args = mock_producer.produce.call_args
    assert call_args.kwargs["key"] == b"org-123"


@patch("src.puptoo.mq.produce.config")
@patch("src.puptoo.mq.produce.metrics")
def test_send_message_no_key_for_non_inventory(mock_metrics, mock_config):
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_producer = MagicMock()
    produce.producer = mock_producer

    msg = {"platform_metadata": {"org_id": "org-123"}}
    extra = {"request_id": "req-1"}

    send_message("platform.payload-status", msg, extra)

    call_args = mock_producer.produce.call_args
    assert call_args.kwargs["key"] is None


@patch("src.puptoo.mq.produce.config")
@patch("src.puptoo.mq.produce.metrics")
def test_send_message_handles_kafka_error(mock_metrics, mock_config):
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_producer = MagicMock()
    mock_producer.produce.side_effect = KafkaException(
        KafkaError(KafkaError._MSG_TIMED_OUT)
    )
    produce.producer = mock_producer

    msg = {"platform_metadata": {}}
    extra = {"request_id": "req-1"}

    send_message("some-topic", msg, extra)

    mock_metrics.msg_send_failure.labels.assert_called_with("some-topic")
    mock_metrics.msg_send_failure.labels("some-topic").inc.assert_called()


@patch("src.puptoo.mq.produce.config")
@patch("src.puptoo.mq.produce.metrics")
def test_send_message_strips_system_profile_for_inventory(mock_metrics, mock_config):
    mock_config.INVENTORY_TOPIC = "inventory"
    mock_producer = MagicMock()
    produce.producer = mock_producer

    msg = {
        "platform_metadata": {"org_id": "org-1"},
        "system_profile": True,
        "data": {"system_profile": {"cpu_count": 4}, "other": "value"},
    }
    extra = {"request_id": "req-1"}

    send_message("inventory", msg, extra)

    assert "system_profile" not in msg["data"]
    assert msg["data"]["other"] == "value"


@patch("src.puptoo.mq.produce.metrics")
def test_delivery_report_success(mock_metrics):
    mock_msg = MagicMock()
    mock_msg.topic.return_value = "inventory"
    mock_msg.partition.return_value = 0
    extra = {"request_id": "req-1"}

    delivery_report(None, msg=mock_msg, extra=extra)

    mock_metrics.msg_produced.labels.assert_called_with("inventory")
    mock_metrics.msg_produced.labels("inventory").inc.assert_called()


@patch("src.puptoo.mq.produce.metrics")
def test_delivery_report_failure(mock_metrics):
    mock_msg = MagicMock()
    mock_msg.topic.return_value = "inventory"
    extra = {"request_id": "req-1"}
    err = KafkaError(KafkaError._MSG_TIMED_OUT)

    delivery_report(err, msg=mock_msg, extra=extra)

    mock_metrics.msg_send_failure.labels.assert_called_with("inventory")
    mock_metrics.msg_send_failure.labels("inventory").inc.assert_called()


@patch("src.puptoo.mq.produce.logger")
@patch("src.puptoo.mq.produce.metrics")
def test_delivery_report_failure_format_args_order(mock_metrics, mock_logger):
    mock_msg = MagicMock()
    mock_msg.topic.return_value = "test-topic"
    extra = {"request_id": "req-42"}
    err = KafkaError(KafkaError._MSG_TIMED_OUT)

    delivery_report(err, msg=mock_msg, extra=extra)

    call_args = mock_logger.error.call_args[0]
    assert call_args[1] == "test-topic"
    assert call_args[2] == "req-42"
    assert call_args[3] is err
