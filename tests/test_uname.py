from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

UNAME_1 = """
Linux server1.example.com 2.6.32-504.el6.x86_64 #1 SMP Tue Sep 16 01:56:35 EDT 2014 x86_64 x86_64 x86_64 GNU/Linux
""".strip()


def test_uname():
    input_data = InputData().add(Specs.uname, UNAME_1)
    result = run_test(system_profile, input_data)
    assert result["arch"] == "x86_64"
