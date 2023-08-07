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
UNAME_CENTOS_7_9 = "Linux kvm-01-guest17.lab.eng.brq2.redhat.com 3.10.0-1160.el7.x86_64 #1 SMP Mon Oct 19 16:18:59 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux"
UNAME_CENTOS_8_5 = "Linux kvm-02-guest12.rhts.eng.brq.redhat.com 4.18.0-348.7.1.el8_5.x86_64 #1 SMP Wed Dec 22 13:25:12 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux"
UNAME_CENTOS_9STR = "Linux hpe-apollo-cn99xx-15-vm-17.khw4.lab.eng.bos.redhat.com 5.14.0-316.el9.aarch64 #1 SMP PREEMPT_DYNAMIC Fri May 19 12:15:43 UTC 2023 aarch64 aarch64 aarch64 GNU/Linux"

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
OS_RELEASE_FEDORA = """
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
OS_RELEASE_CENTOS_7_9 = """
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="7"
PRETTY_NAME="CentOS Linux 7 (Core)"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:centos:centos:7"
HOME_URL="https://www.centos.org/"
BUG_REPORT_URL="https://bugs.centos.org/"

CENTOS_MANTISBT_PROJECT="CentOS-7"
CENTOS_MANTISBT_PROJECT_VERSION="7"
REDHAT_SUPPORT_PRODUCT="centos"
REDHAT_SUPPORT_PRODUCT_VERSION="7"
"""
OS_RELEASE_CENTOS_8_5 = """
NAME="CentOS Linux"
VERSION="8"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="8"
PLATFORM_ID="platform:el8"
PRETTY_NAME="CentOS Linux 8"
ANSI_COLOR="0;31"
CPE_NAME="cpe:/o:centos:centos:8"
HOME_URL="https://centos.org/"
BUG_REPORT_URL="https://bugs.centos.org/"
CENTOS_MANTISBT_PROJECT="CentOS-8"
CENTOS_MANTISBT_PROJECT_VERSION="8"
"""
OS_RELEASE_CENTOS_9STR = """
NAME="CentOS Stream"
VERSION="9"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="9"
PLATFORM_ID="platform:el9"
PRETTY_NAME="CentOS Stream 9"
ANSI_COLOR="0;31"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:centos:centos:9"
HOME_URL="https://centos.org/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux 9"
REDHAT_SUPPORT_PRODUCT_VERSION="CentOS Stream"
"""
OS_RELEASE_UNKNOWN = """
NAME="Test OS"
ID="test"
PRETTY_NAME="Test OS"
""".strip()

DMESG_CENTOS_7_9 = """
[    0.000000] Initializing cgroup subsys cpuset
[    0.000000] Initializing cgroup subsys cpu
[    0.000000] Initializing cgroup subsys cpuacct
[    0.000000] Linux version 3.10.0-1160.el7.x86_64 (mockbuild@kbuilder.bsys.centos.org) (gcc version 4.8.5 20150623 (Red Hat 4.8.5-44) (GCC) ) #1 SMP Mon Oct 19 16:18:59 UTC 2020
[    0.000000] Command line: initrd=/images/kvm-01-guest17.lab.eng.brq2.redhat.com/initrd console=ttyS0,115200 ks=http://beaker.engineering.redhat.com/kickstart/11931405 ksdevice=bootif netboot_method=pxe BOOT_IMAGE=/images/kvm-01-guest17.lab.eng.brq2.redhat.com/kernel BOOTIF=01-52-54-00-d4-b4-e6
""".strip()
DMESG_CENTOS_8_5 = """
[    0.000000] Linux version 4.18.0-240.el8.x86_64 (mockbuild@kbuilder.bsys.centos.org) (gcc version 8.4.1 20200928 (Red Hat 8.4.1-1) (GCC)) #1 SMP Tue Apr 13 16:24:22 UTC 2021
""".strip()
DMESG_CENTOS_9STR = """
[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x431f0af1]
[    0.000000] Linux version 5.14.0-316.el9.aarch64 (mockbuild@aarch64-01.stream.rdu2.redhat.com) (gcc (GCC) 11.3.1 20221121 (Red Hat 11.3.1-4), GNU ld version 2.35.2-39.el9) #1 SMP PREEMPT_DYNAMIC Fri May 19 12:15:43 UTC 2023
[    0.000000] The list of certified hardware and cloud instances for Red Hat Enterprise Linux 9 can be viewed at the Red Hat Ecosystem Catalog, https://catalog.redhat.com.
"""


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

def test_centos_7_9():
    input_data = InputData()
    input_data.add(Specs.redhat_release, REDHAT_RELEASE_CENTOS_7)
    input_data.add(Specs.uname, UNAME_CENTOS_7_9)
    input_data.add(Specs.os_release, OS_RELEASE_CENTOS_7_9)
    result = run_test(system_profile, input_data)
    assert result["os_release"] == "7.9"
    assert result["operating_system"] == {
        "major": 7,
        "minor": 9,
        "name": "CentOS",
    }
