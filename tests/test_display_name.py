from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

DISPLAY_NAME_1 = """
foo-bar
""".strip()


def test_display_name():
    input_data = InputData().add(Specs.display_name, DISPLAY_NAME_1)
    result = run_test(system_profile, input_data)
    assert result["display_name"] == "foo-bar"
