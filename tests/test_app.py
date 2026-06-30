from unittest.mock import MagicMock

import pytest
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
