import app

import pytest

def test_get_extra():

    expected = {"account": "123456", "request_id": "abdc-1234"}
    assert expected == app.get_extra("123456", "abdc-1234")
    expected = {"account": "unknown", "request_id": "unknown"}
    assert expected == app.get_extra()
