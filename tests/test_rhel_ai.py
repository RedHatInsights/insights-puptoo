from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile


OS_RELEASE_RHEL_AI = """
NAME="Red Hat Enterprise Linux"
VERSION="9.20240630.0.4 (Plow)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="9.4"
PLATFORM_ID="platform:el9"
PRETTY_NAME="Red Hat Enterprise Linux 9.20240630.0.4 (Plow)"
ANSI_COLOR="0;31"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:redhat:enterprise_linux:9::baseos"
HOME_URL="https://www.redhat.com/"
DOCUMENTATION_URL="https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_BUGZILLA_PRODUCT="Red Hat Enterprise Linux 9"
REDHAT_BUGZILLA_PRODUCT_VERSION=9.4
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="9.4"
OSTREE_VERSION='9.20240630.0'
VARIANT_ID=rhel_ai
VARIANT="RHEL AI"
BUILD_ID='v1.1.3'
""".strip()

OS_RELEASE_RHEL = """
NAME="Red Hat Enterprise Linux"
VERSION="9.1 (Plow)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="9.1"
PLATFORM_ID="platform:el9"
PRETTY_NAME="Red Hat Enterprise Linux 9.1 (Plow)"
ANSI_COLOR="0;31"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:redhat:enterprise_linux:9::baseos"
HOME_URL="https://www.redhat.com/"
DOCUMENTATION_URL="https://access.redhat.com/documentation/red_hat_enterprise_linux/9/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"

REDHAT_BUGZILLA_PRODUCT="Red Hat Enterprise Linux 9"
REDHAT_BUGZILLA_PRODUCT_VERSION=9.1
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="9.1"
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

NVIDIA_SMI_L = """
GPU 0: NVIDIA T1000 (UUID: GPU-c05fe28c-5935-1c6d-3633-2fc61d26b6d4)
GPU 1: Tesla V100-PCIE-16GB (UUID: GPU-b08ecee0-0ea5-7b07-d459-baa5b95f5e89)
""".strip()


def test_rhel_ai():

    # As a RHEL AI system, with nvidia_gpu_models
    input_data = InputData()
    input_data.add(Specs.os_release, OS_RELEASE_RHEL_AI)
    input_data.add(Specs.nvidia_smi_l, NVIDIA_SMI_L)
    result = run_test(system_profile, input_data)
    assert result["rhel_ai"]["variant"] == "RHEL AI"
    assert result["rhel_ai"]["rhel_ai_version_id"] == "v1.1.3"
    assert len(result["rhel_ai"]["nvidia_gpu_models"]) == 2
    assert result["rhel_ai"]["nvidia_gpu_models"] == ["NVIDIA T1000", "Tesla V100-PCIE-16GB"]

    # As a RHEL AI system, without nvidia_gpu_models
    input_data = InputData()
    input_data.add(Specs.os_release, OS_RELEASE_RHEL_AI)
    input_data.add(Specs.nvidia_smi_l, "")
    result = run_test(system_profile, input_data)
    assert result["rhel_ai"]["variant"] == "RHEL AI"
    assert result["rhel_ai"]["rhel_ai_version_id"] == "v1.1.3"
    assert "nvidia_gpu_models" not in result["rhel_ai"]

    # Not a "RHEL AI" system - RHEL
    input_data = InputData()
    input_data.add(Specs.os_release, OS_RELEASE_RHEL)
    input_data.add(Specs.nvidia_smi_l, NVIDIA_SMI_L)
    result = run_test(system_profile, input_data)
    assert "rhel_ai" not in result

    # Not a "RHEL AI" system - Fedora
    input_data = InputData()
    input_data.add(Specs.os_release, OS_RELEASE_FEDORA)
    input_data.add(Specs.nvidia_smi_l, NVIDIA_SMI_L)
    result = run_test(system_profile, input_data)
    assert "rhel_ai" not in result
