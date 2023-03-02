from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

REDHAT_RELEASE_1 = """Red Hat Enterprise Linux release 8.0"""
REDHAT_RELEASE_2 = """Red Hat Enterprise Linux release 7.8"""


def test_system_update_method():
    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_1)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "dnf"

    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_2)
    result = run_test(system_profile, input_data)
    assert result["system_update_method"] == "yum"

    