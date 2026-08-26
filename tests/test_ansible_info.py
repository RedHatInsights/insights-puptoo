from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
ansible-tower-1.0.0-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
catalog-worker-1.0.2-1.x86_64    Tue 14 Jul 2015 09:25:40 AEST   1390535634
automation-hub-1.0.3-1.x86_64       Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-controller-1.0.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_CONTROLLER_ONLY = """
ansible-tower-1.0.0-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
""".strip()

NO_ANSIBLE_RPMS = """
bash-5.1.8-6.el9.x86_64  Tue 14 Jul 2025 09:25:38 AEST   1398536494
""".strip()


def test_ansible_info():
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "hub_version": "1.0.3",
        "catalog_worker_version": "1.0.2",
        "controller_version": "1.0.0",
    }
    assert "sso_version" not in result["workloads"]["ansible"]


def test_ansible_info_sends_null_for_missing_versions():
    input_data = InputData().add(Specs.installed_rpms, RPMS_CONTROLLER_ONLY)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "controller_version": "1.0.0",
        "hub_version": None,
        "catalog_worker_version": None,
    }
    assert "sso_version" not in result["workloads"]["ansible"]


def test_ansible_info_null_when_no_ansible_packages():
    input_data = InputData().add(Specs.installed_rpms, NO_ANSIBLE_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] is None


def test_ansible_info_omitted_when_rpms_not_collected():
    result = run_test(system_profile, InputData())
    assert "ansible" not in result.get("workloads", {})
