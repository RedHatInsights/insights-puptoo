from freezegun import freeze_time

from puptoo.mq import msgs

platform_metadata = {"account": "000001",
                     "request_id": "abcd-1234",
                     "principal": "123456",
                     "service": "advisor",
                     "url": "http://www.example.com",
                     "b64_identity": "somebase64",
                     "id": "1234567"}

some_facts = {"ip_addresses": ["127.0.0.1"]}


@freeze_time("2019-7-23")
def test_get_time():
    assert msgs.get_time() == "2019-07-23T00:00:00"


@freeze_time("2019-7-23")
def test_tracker_msg():

    extra = {"account": "123456", "request_id": "abcd-1234"}
    expected = {"account": "123456",
                "request_id": "abcd-1234",
                "payload_id": "abcd-1234",
                "service": "puptoo",
                "status": "received",
                "status_msg": "test_totally_worked",
                "date": "2019-07-23T00:00:00"
                }

    result = msgs.tracker_message(extra, "received", "test_totally_worked")
    assert result == expected


def test_inventory_msg():

    operation = "add_host"
    data = {"insights_id": "cdbd-2e23-cdef-1234",
            "fqdn": "something.example.com",
            "ip_addresses": ["192.168.0.1", "127.0.0.1"],
            "bios_uuid": "12335kjlj"}
    metadata = {"account": "123456",
                "request_id": "abcd-1234"
                }
    expected = {"operation": operation,
                "data": data,
                "platform_metadata": metadata}

    result = msgs.inv_message(operation, data, metadata)
    assert result == expected


def test_validation_msg():

    result = msgs.validation_message(platform_metadata, some_facts, "success")
    expected = {"validation": "success", **platform_metadata, **some_facts}
    assert result == expected
