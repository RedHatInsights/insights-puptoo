from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile


REDHAT_RELEASE_8_0 = """Red Hat Enterprise Linux release 8.0"""
OS_RELEASE_8_0 = """
NAME="Red Hat Enterprise Linux"
VERSION="8.0 (Ootpa)"
ID="rhel"
PRETTY_NAME="Red Hat Enterprise Linux 8.1 (Ootpa)"
""".strip()

REDHAT_RELEASE_7_2 = """Red Hat Enterprise Linux Server release 7.2 (Maipo)"""
OS_RELEASE_7_2 = """
NAME="Red Hat Enterprise Linux"
VERSION="7.2.0 (Ootpa)"
ID="rhel"
PRETTY_NAME="Red Hat Enterprise Linux 7.2 (Ootpa)"
""".strip()

# REDHAT_RELEASE_CENTOS_7_6 = """CentOS Linux release 7.6.1810 (Core)"""

REDHAT_RELEASE_CENTOS_7_9 = "CentOS Linux release 7.9.2009 (Core)"
OS_RELEASE_CENTOS_7_9 = """
NAME="CentOS Linux"
ID="centos"
PRETTY_NAME="CentOS Linux 7 (Core)"
""".strip()

REDHAT_RELEASE_CENTOS_9 = "CentOS Stream release 9"
OS_RELEASE_CENTOS_9 = """
NAME="CentOS Stream"
ID="centos"
PRETTY_NAME="CentOS Stream 9"
""".strip()

REDHAT_RELEASE_SERVER_7_9 = "Red Hat Enterprise Linux Server release 7.9 (Maipo)"
OS_RELEASE_ORACLE_7_9 = """
NAME="Oracle Linux Server"
VERSION="7.9"
ID="ol"
PRETTY_NAME="Red Hat Enterprise Linux"
""".strip()

REDHAT_RELEASE = """
Red Hat Enterprise Linux Server release 7.9 (Maipo)
# This is a "SLES Expanded Support platform release 7.9"
# The above "Red Hat Enterprise Linux Server" string is only used to 
# keep software compatibility.
""".strip()
OS_RELEASE_SUSE_7_9 = """
NAME="Red Hat Enterprise Linux Server"
VERSION="7.9 (Maipo)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="7.9"
PRETTY_NAME="Red Hat Enterprise Linux Server 7.9"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:redhat:enterprise_linux:7.9:GA:server"
HOME_URL="https://www.redhat.com/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"

REDHAT_BUGZILLA_PRODUCT="Red Hat Enterprise Linux 7"
REDHAT_BUGZILLA_PRODUCT_VERSION=7.9
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux"
REDHAT_SUPPORT_PRODUCT_VERSION=7.9
# This is a "SLES Expanded Support platform release 7.9"
# The above "Red Hat Enterprise Linux Server" string is only used to
# keep software compatibility.
""".strip()


def test_os_release():

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_8_0)
    input_data.add(Specs.os_release, OS_RELEASE_8_0)
    result = run_test(system_profile, input_data)
    expected_result = {
        "major": 8,
        "minor": 0,
        "name": "RHEL"
    }
    assert result["os_release"] == "8.0"
    assert result["system_update_method"] == "dnf"
    assert result["operating_system"] == expected_result

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_7_2)
    input_data.add(Specs.os_release, OS_RELEASE_7_2)
    result = run_test(system_profile, input_data)
    expected_result = {
        "major": 7,
        "minor": 2,
        "name": "RHEL"
    }
    assert result["os_release"] == "7.2"
    assert result["system_update_method"] == "yum"
    assert result["operating_system"] == expected_result

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_CENTOS_7_9)
    input_data.add(Specs.os_release, OS_RELEASE_CENTOS_7_9)
    result = run_test(system_profile, input_data)
    expected_result = {
        "major": 7,
        "minor": 9,
        "name": "CentOS Linux"
    }
    assert result["os_release"] == "7.9"
    assert result["system_update_method"] == "yum"
    assert result["operating_system"] == expected_result

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_CENTOS_9)
    input_data.add(Specs.os_release, OS_RELEASE_CENTOS_9)
    result = run_test(system_profile, input_data)
    expected_result = {
        "major": 9,
        "minor": 0,
        "name": "CentOS Stream"
    }
    assert result["os_release"] == "9.0"
    assert result["system_update_method"] == "yum"
    assert result["operating_system"] == expected_result

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_SERVER_7_9)
    input_data.add(Specs.os_release, OS_RELEASE_ORACLE_7_9)
    result = run_test(system_profile, input_data)
    # TODO: add assertions after updating insights-core to 3.2.9

    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE)
    input_data.add(Specs.os_release, OS_RELEASE_SUSE_7_9)
    result = run_test(system_profile, input_data)
    # TODO: add assertions