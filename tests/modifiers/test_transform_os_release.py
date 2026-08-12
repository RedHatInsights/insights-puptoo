from src.puptoo.modifiers.qpc.transform_os_release import TransformOsRelease


def test_transform_os_release():
    host = {
        "system_profile": {
            "os_release": "Red Hat Enterprise Linux Server 6.10 (Santiago)"
        }
    }
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host["system_profile"]["os_release"] == "6.10"
    assert (
        "os_release from 'Red Hat Enterprise Linux Server 6.10 (Santiago)' to '6.10'"
        in transformed_obj["modified"]
    )


def test_do_not_transform_when_only_version():
    host = {"system_profile": {"os_release": "7"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host["system_profile"]["os_release"] == "7"
    assert "operating system info for os release '7'" in transformed_obj["missing_data"]


def test_remove_os_release_when_no_version():
    host = {"system_profile": {"os_release": "Red Hat Enterprise Linux Server"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host == {"system_profile": {}}
    assert "empty os_release" in transformed_obj["removed"]


def test_remove_os_release_when_no_version_with_parentheses():
    host = {"system_profile": {"os_release": "  ()"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host == {"system_profile": {}}
    assert "empty os_release" in transformed_obj["removed"]


def test_remove_os_release_when_only_string_in_parentheses():
    host = {"system_profile": {"os_release": "  (Core)"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host == {"system_profile": {}}
    assert "empty os_release" in transformed_obj["removed"]


def test_remove_os_release_when_empty_string():
    host = {"system_profile": {"os_release": ""}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host == {"system_profile": {}}
    assert "empty os_release" in transformed_obj["removed"]


def test_transform_os_release_when_non_rhel_os():
    host = {"system_profile": {"os_release": "CentOS Linux 7 (Core)"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host["system_profile"]["os_release"] == "7"
    assert (
        "os_release from 'CentOS Linux 7 (Core)' to '7'" in transformed_obj["modified"]
    )


def test_transform_os_release_when_centos():
    host = {"system_profile": {"os_release": "CentOS Linux 7 (Core)"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformOsRelease().run(host, transformed_obj)
    assert host == {
        "system_profile": {
            "operating_system": {
                "major": "7",
                "minor": "0",
                "name": "CentOS",
            },
            "os_release": "7",
        }
    }
    assert (
        "os_release from 'CentOS Linux 7 (Core)' to '7'" in transformed_obj["modified"]
    )


def test_match_regex_and_find_os_details():
    host = {"system_profile": {"os_release": "Red Hat Enterprise Linux Server 7"}}
    host_os_version = "7"
    os_version = TransformOsRelease().match_regex_and_find_os_details(
        host["system_profile"]["os_release"]
    )
    assert host_os_version == os_version["major"]
