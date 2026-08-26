from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
mssql-server-1.0.4-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
""".strip()

NO_MSSQL_RPMS = """
bash-5.1.8-6.el9.x86_64  Tue 14 Jul 2025 09:25:38 AEST   1398536494
""".strip()


def test_mssql_info():
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["mssql"] == {"version": "1.0.4"}


def test_mssql_null_when_package_absent():
    input_data = InputData().add(Specs.installed_rpms, NO_MSSQL_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["mssql"] is None


def test_mssql_omitted_when_rpms_not_collected():
    result = run_test(system_profile, InputData())
    assert "mssql" not in result.get("workloads", {})
