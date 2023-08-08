from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

REDHAT_RELEASE_8_0 = """Red Hat Enterprise Linux release 8.0"""
REDHAT_RELEASE_7_2 = """Red Hat Enterprise Linux Server release 7.2 (Maipo)"""
REDHAT_RELEASE_CENTOS_7_6 = "CentOS Linux release 7.6.1810 (Core)"


def test_os_release():

    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_8_0)
    result = run_test(system_profile, input_data)
    assert result["operating_system"]["name"] == "RHEL"

    input_data = InputData().add(Specs.redhat_release, REDHAT_RELEASE_7_2)
    result = run_test(system_profile, input_data)
    assert result["operating_system"]["name"] == "RHEL"
