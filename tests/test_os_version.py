from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

REDHAT_RELEASE_6_7 = "Red Hat Enterprise Linux Server release 6.7 (Santiago)"
REDHAT_RELEASE_7_2 = "Red Hat Enterprise Linux Server release 7.2 (Maipo)"
REDHAT_RELEASE_7_5 = "Red Hat Enterprise Linux release 7.5-0.14"
REDHAT_RELEASE_RHVH_RHV40 = "Red Hat Enterprise Linux release 7.3"
REDHAT_RELEASE_RHEVH_RHEV35 = "Red Hat Enterprise Virtualization Hypervisor release 6.7 (20160219.0.el6ev)"
REDHAT_RELEASE_FEDORA = "Fedora release 23 (Twenty Three)"
REDHAT_RELEASE_8_2 = "Red Hat Enterprise Linux release 8.2 (Ootpa)"
REDHAT_RELEASE_6_10 = "Red Hat Enterprise Linux Server release 6.10(Santiago)"
REDHAT_RELEASE_BETA = "Red Hat Enterprise Linux Server release 8.5 Beta (Ootpa)"
REDHAT_RELEASE_CENTOS_STREAM = "CentOS Stream release 8"
REDHAT_RELEASE_CENTOS_7 = "CentOS Linux release 7.6.1810 (Core)"
REDHAT_RELEASE_9_ALPHA = "Red Hat Enterprise Linux release 9.0 Alpha (Plow)"
REDHAT_RELEASE_8_CONTAINER = "Red Hat Enterprise Linux Server release 8.6 (Ootpa)"

UNAME_EL6_6 = "Linux foo.example.com 2.6.32-504.el6.x86_64 #1 SMP Tue Sep 16 01:56:35 EDT 2014 x86_64 x86_64 x86_64 GNU/Linux"
UNAME_EL7_2 = "Linux rhel7box 3.10.0-327.el7.x86_64 #1 SMP Mon Mar 3 13:32:45 EST 2014 x86_64 x86_64 x86_64 GNU/Linux"
UNAME_EL7_4_ALT = "Linux foo.example.com 4.11.0-44.el7.x86_64 #1 SMP Thu Jan 29 18:37:38 EST 2015 x86_64 x86_64 x86_64 GNU/Linux"

OS_RELEASE_RHEL_7_2 = """
NAME="Red Hat Enterprise Linux Server"
VERSION="7.2 (Maipo)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="7.2"
PRETTY_NAME="Employee SKU"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:redhat:enterprise_linux:7.2:GA:server"
HOME_URL="https://www.redhat.com/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"

REDHAT_BUGZILLA_PRODUCT="Red Hat Enterprise Linux 7"
REDHAT_BUGZILLA_PRODUCT_VERSION=7.2
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="7.2"
""".strip()
OS_RELEASE_RHEVH_RHV40 = """
NAME="Red Hat Enterprise Linux"
VERSION="7.3"
VERSION_ID="7.3"
ID="rhel"
ID_LIKE="fedora"
VARIANT="Red Hat Virtualization Host"
VARIANT_ID="ovirt-node"
PRETTY_NAME="Red Hat Virtualization Host 4.0 (el7.3)"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:redhat:enterprise_linux:7.3:GA:hypervisor"
HOME_URL="https://www.redhat.com/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
""".strip()
FEDORA_OS_RELEASE = """
NAME=Fedora
VERSION="24 (Server Edition)"
ID=fedora
VERSION_ID=24
PRETTY_NAME="Fedora 24 (Server Edition)"
ANSI_COLOR="0;34"
CPE_NAME="cpe:/o:fedoraproject:fedora:24"
HOME_URL="https://fedoraproject.org/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_BUGZILLA_PRODUCT="Fedora"
REDHAT_BUGZILLA_PRODUCT_VERSION=24
REDHAT_SUPPORT_PRODUCT="Fedora"
REDHAT_SUPPORT_PRODUCT_VERSION=24
PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy
VARIANT="Server Edition"
VARIANT_ID=server
""".strip()


def test_rhel_7_2():
    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_7_2)
    input_data.add(Specs.uname, UNAME_EL7_2)
    input_data.add(Specs.os_release, OS_RELEASE_RHEL_7_2)
    result = run_test(system_profile, input_data)
    assert result["os_release"] == "7.2"
    assert result["operating_system"] == {
        "major": 7,
        "minor": 2,
        "name": "RHEL",
    }
