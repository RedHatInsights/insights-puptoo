from datetime import datetime
from unittest.mock import patch

import pytest

from src.puptoo.exceptions import QPCKafkaMsgException
from src.puptoo.qpc.validators import check_if_url_expired, validate_qpc_message
from src.puptoo.utils.config import ANNOUNCE_TOPIC

PAYLOAD_URL = (
    "http://minio:9000/insights-upload-perma"
    f"?X-Amz-Date={datetime.now().strftime('%Y%m%dT%H%M%SZ')}"
    "&X-Amz-Expires=86400"
)
B64_IDENTITY = (
    "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiAic3lzYWNjb3VudCIsICJ0eXBlIjogIlN5c3R"
    "lbSIsICJhdXRoX3R5cGUiOiAiY2VydC1hdXRoIiwgInN5c3RlbSI6IHsiY24iOiAiMWIzNmIyMGYtN2"
    "ZhMC00NDU0LWE2ZDItMDA4Mjk0ZTA2Mzc4IiwgImNlcnRfdHlwZSI6ICJzeXN0ZW0ifSwgImludGVyb"
    "mFsIjogeyJvcmdfaWQiOiAiMzM0MDg1MSIsICJhdXRoX3RpbWUiOiA2MzAwfX19"
)


def test_validate_qpc_message():
    qpc_msg = {
        "url": PAYLOAD_URL,
        "account": "123",
        "org_id": "123",
        "request_id": "234332",
        "b64_identity": B64_IDENTITY,
        "topic": ANNOUNCE_TOPIC,
    }
    result = validate_qpc_message(qpc_msg)
    assert result.items() <= qpc_msg.items()


def test_validate_qpc_message_without_org_id():
    qpc_msg = {
        "url": PAYLOAD_URL,
        "request_id": "234332",
        "account": "123",
        "b64_identity": B64_IDENTITY,
        "topic": ANNOUNCE_TOPIC,
    }
    with pytest.raises(QPCKafkaMsgException):
        validate_qpc_message(qpc_msg)


def test_qpc_message_without_topic():
    qpc_msg = {
        "url": PAYLOAD_URL,
        "request_id": "234332",
        "b64_identity": B64_IDENTITY,
    }
    with patch("src.puptoo.qpc.validators.LOG.error") as mock:
        validate_qpc_message(qpc_msg)
    mock.assert_called_once_with("Message not found on topic: %s", ANNOUNCE_TOPIC)


def test_check_if_url_expired():
    url = (
        "http://minio:9000/insights-upload-perma"
        "?X-Amz-Date=20200928T063623Z&X-Amz-Expires=86400"
    )
    with pytest.raises(QPCKafkaMsgException):
        check_if_url_expired(url, "123456")


def test_check_if_url_expired_bypass():
    url = (
        "http://minio:9000/insights-upload-perma"
        "?X-Amz-Date=20200928T063623Z&X-Amz-Expires=86400"
    )
    qpc_msg = {
        "url": url,
        "request_id": "123456",
        "b64_identity": B64_IDENTITY,
    }
    with patch("src.puptoo.qpc.validators.LOG.error") as mock:
        with patch("src.puptoo.qpc.validators.BYPASS_PAYLOAD_EXPIRATION", True):
            validate_qpc_message(qpc_msg)
    mock.assert_called_once_with("Message not found on topic: %s", ANNOUNCE_TOPIC)
