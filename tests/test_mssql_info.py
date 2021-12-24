from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
mssql-server-1.0.4-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
""".strip()


def test_mssql_info():
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["mssql"]["version"] == "1.0.4"
