from src.puptoo.modifiers.qpc.transform_ip_addresses import TransformIPAddress


def test_remove_empty_ip_addresses():
    host = {"ip_addresses": []}
    transformed_obj = {"removed": []}
    TransformIPAddress().run(host, transformed_obj)
    assert not host
    assert "empty ip_addresses" in transformed_obj["removed"]


def test_do_not_remove_set_ip_addresses():
    host = {"ip_addresses": ["192.168.10.10"]}
    transformed_obj = {"removed": []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {"ip_addresses": ["192.168.10.10"]}
    assert len(transformed_obj["removed"]) == 0


def test_ip_addresses_field():
    host = {}
    transformed_obj = {"removed": []}
    TransformIPAddress().run(host, transformed_obj)
    assert len(transformed_obj["removed"]) == 0
    assert not host


def test_remove_duplicate_ip_addresses():
    host = {"ip_addresses": ["192.168.10.10", "192.168.10.10"]}
    transformed_obj = {"modified": []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {"ip_addresses": ["192.168.10.10"]}
    assert transformed_obj["modified"]


def test_remove_blank_items_in_ip_addresses():
    host = {"ip_addresses": ["192.168.10.10", "", "192.168.10.11"]}
    transformed_obj = {"modified": []}
    TransformIPAddress().run(host, transformed_obj)
    assert host == {"ip_addresses": ["192.168.10.10", "192.168.10.11"]}
    assert transformed_obj["modified"]


def test_drop_ip_addresses_with_all_blank_items():
    host = {"ip_addresses": ["   ", ""], "key_error": "value"}
    transformed_obj = {"removed": []}
    TransformIPAddress().run(host, transformed_obj)
    assert "ip_addresses" not in host
    assert len(transformed_obj["removed"]) == 1
    assert "empty ip_addresses" in transformed_obj["removed"]
