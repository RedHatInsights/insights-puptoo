import pytest
import datetime

from freezegun import freeze_time

import tracker

@freeze_time("2019-7-23")
def test_get_time():
    assert tracker.get_time() == "2019-07-23T00:00:00"

@freeze_time("2019-7-23")
def test_tracker_msg():

    extra = {"account": "123456", "request_id": "abcd-1234"}
    expected = {"topic": "platform.payload-status",
                "msg": {"account": "123456",
                        "request_id": "abcd-1234",
                        "payload_id": "abcd-1234",
                        "service": "puptoo",
                        "status": "received",
                        "status_msg": "test_totally_worked",
                        "date": "2019-07-23T00:00:00"
                        },
                "extra": {"account": "123456",
                          "request_id": "abcd-1234"}
                }

    result = tracker.tracker_msg(extra, "received", "test_totally_worked")
    assert result == expected
