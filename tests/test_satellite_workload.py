from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

SATELLITE_SERVER_RPMS = """
satellite-6.19.0-1.el9sat.noarch  Wed 20 May 2026 13:37:10 UTC   1770845372
""".strip()

SATELLITE_CAPSULE_RPMS = """
satellite-capsule-6.19.0-1.el9sat.noarch  Wed 20 May 2026 13:37:10 UTC   1770845372
""".strip()

NO_SATELLITE_RPMS = """
bash-5.1.8-6.el9.x86_64  Tue 14 Jul 2025 09:25:38 AEST   1398536494
""".strip()


def test_satellite_server():
    input_data = InputData().add(Specs.installed_rpms, SATELLITE_SERVER_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {"type": "server"}


def test_satellite_capsule():
    input_data = InputData().add(Specs.installed_rpms, SATELLITE_CAPSULE_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {"type": "capsule"}


def test_no_satellite():
    input_data = InputData().add(Specs.installed_rpms, NO_SATELLITE_RPMS)
    result = run_test(system_profile, input_data)
    assert "satellite" not in result.get("workloads", {})
