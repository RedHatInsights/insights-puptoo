from src.puptoo import app
from freezegun import freeze_time
from datetime import datetime


@freeze_time("2019-7-23")
def test_get_staletime():
    dtz = datetime.fromtimestamp(1563944400).astimezone()
    assert app.get_staletime() == dtz.isoformat()


def test_get_extra():

    expected = {"account": "123456", "org_id": "654321", "request_id": "abdc-1234"}
    assert expected == app.get_extra("123456", "654321", "abdc-1234")
    expected = {"account": "unknown", "org_id": "unknown", "request_id": "unknown"}
    assert expected == app.get_extra()
