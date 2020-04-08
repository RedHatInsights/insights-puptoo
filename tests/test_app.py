from puptoo import app
from freezegun import freeze_time


@freeze_time("2019-7-23")
def test_get_staletime():
    assert app.get_staletime() == "1563948000"


def test_get_extra():

    expected = {"account": "123456", "request_id": "abdc-1234"}
    assert expected == app.get_extra("123456", "abdc-1234")
    expected = {"account": "unknown", "request_id": "unknown"}
    assert expected == app.get_extra()
