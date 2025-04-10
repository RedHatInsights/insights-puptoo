from insights.specs import Specs
from insights.tests import InputData, run_test
from tests.test_bootc_status import BOOTC_STATUS, BOOTC_STATUS_SPECIAL_DATA
from tests.test_host_type import DATA_0

from src.puptoo.process.profile import system_profile

REDHAT_RELEASE_1 = """Red Hat Enterprise Linux release 8.0"""
REDHAT_RELEASE_2 = """Red Hat Enterprise Linux release 7.8"""
REDHAT_RELEASE_3 = """Red Hat Enterprise Linux release 9.4"""
REDHAT_RELEASE_4 = """Red Hat Enterprise Linux release 10.0"""


def test_system_update_method():
    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_1)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "dnf"

    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_2)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "yum"


def test_edge_system():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_0)
    result = run_test(system_profile, input_data)
    assert result["host_type"] == "edge"
    assert "system_update_method" not in result

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_3)
    input_data.add(Specs.rpm_ostree_status, DATA_0)
    result = run_test(system_profile, input_data)
    assert result["host_type"] == "edge"
    assert result["system_update_method"] == "rpm-ostree"

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_3)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "dnf"


def test_bootc_system():
    input_data = InputData("only_rhrls")
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_4)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "dnf"

    input_data = InputData("only_bootc")
    input_data.add(Specs.bootc_status, BOOTC_STATUS)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "bootc"

    input_data = InputData("both_rhrls_and_bootc_false")
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_4)
    input_data.add(Specs.bootc_status, BOOTC_STATUS_SPECIAL_DATA)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "dnf"

    input_data = InputData("both_rhrls_and_bootc_true")
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_4)
    input_data.add(Specs.bootc_status, BOOTC_STATUS)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "bootc"

    input_data = InputData("three_rhrls_and_edge_and_bootc_false")
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_4)
    input_data.add(Specs.rpm_ostree_status, DATA_0)
    input_data.add(Specs.bootc_status, BOOTC_STATUS_SPECIAL_DATA)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "rpm-ostree"

    input_data = InputData("three_rhrls_and_edge_and_bootc_true")
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_4)
    input_data.add(Specs.rpm_ostree_status, DATA_0)
    input_data.add(Specs.bootc_status, BOOTC_STATUS)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "bootc"
