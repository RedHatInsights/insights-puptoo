import os
from unittest.mock import MagicMock, mock_open, patch

from src.puptoo.mq.auth import CACERT_PATH, kafka_auth_config, write_kafka_cert


@patch("src.puptoo.mq.auth.config")
def test_kafka_auth_config_with_sasl(mock_config):
    mock_config.KAFKA_BROKER = MagicMock()
    mock_config.KAFKA_BROKER.cacert = "some-cert"
    mock_config.KAFKA_BROKER.sasl.username = "user"
    mock_config.KAFKA_BROKER.sasl.password = "pass"
    mock_config.KAFKA_BROKER.sasl.securityProtocol = "SASL_SSL"
    mock_config.KAFKA_BROKER.sasl.saslMechanism = "SCRAM-SHA-512"

    info = {"bootstrap.servers": "localhost:9092"}
    result = kafka_auth_config(info)

    assert result is info
    assert result["ssl.ca.location"] == CACERT_PATH
    assert result["security.protocol"] == "SASL_SSL"
    assert result["sasl.mechanisms"] == "SCRAM-SHA-512"
    assert result["sasl.username"] == "user"
    assert result["sasl.password"] == "pass"


@patch("src.puptoo.mq.auth.config")
def test_kafka_auth_config_without_broker(mock_config):
    mock_config.KAFKA_BROKER = None

    info = {"bootstrap.servers": "localhost:9092"}
    result = kafka_auth_config(info)

    assert result == {"bootstrap.servers": "localhost:9092"}


@patch("src.puptoo.mq.auth.config")
def test_kafka_auth_config_cacert_only(mock_config):
    mock_config.KAFKA_BROKER = MagicMock()
    mock_config.KAFKA_BROKER.cacert = "some-cert"
    mock_config.KAFKA_BROKER.sasl = None

    info = {"bootstrap.servers": "localhost:9092"}
    result = kafka_auth_config(info)

    assert result["ssl.ca.location"] == CACERT_PATH
    assert "security.protocol" not in result
    assert "sasl.mechanisms" not in result


@patch("src.puptoo.mq.auth.config")
def test_kafka_auth_config_no_cacert_no_sasl(mock_config):
    mock_config.KAFKA_BROKER = MagicMock()
    mock_config.KAFKA_BROKER.cacert = None
    mock_config.KAFKA_BROKER.sasl = None

    info = {"bootstrap.servers": "localhost:9092"}
    result = kafka_auth_config(info)

    assert "ssl.ca.location" not in result
    assert "security.protocol" not in result


@patch("src.puptoo.mq.auth.config")
def test_write_kafka_cert_writes_file_with_restricted_permissions(mock_config):
    mock_config.KAFKA_BROKER = MagicMock()
    mock_config.KAFKA_BROKER.cacert = (
        "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
    )

    m = mock_open()
    fake_fd = 42
    with (
        patch("src.puptoo.mq.auth.os.open", return_value=fake_fd) as mock_os_open,
        patch("src.puptoo.mq.auth.os.fdopen", m),
    ):
        write_kafka_cert()

    mock_os_open.assert_called_once_with(
        CACERT_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    m.assert_called_once_with(fake_fd, "w")
    m().__enter__().write.assert_called_once_with(mock_config.KAFKA_BROKER.cacert)


@patch("src.puptoo.mq.auth.config")
def test_write_kafka_cert_noop_without_broker(mock_config):
    mock_config.KAFKA_BROKER = None

    with patch("src.puptoo.mq.auth.os.open") as mock_os_open:
        write_kafka_cert()

    mock_os_open.assert_not_called()


@patch("src.puptoo.mq.auth.config")
def test_write_kafka_cert_noop_without_cacert(mock_config):
    mock_config.KAFKA_BROKER = MagicMock()
    mock_config.KAFKA_BROKER.cacert = None

    with patch("src.puptoo.mq.auth.os.open") as mock_os_open:
        write_kafka_cert()

    mock_os_open.assert_not_called()
