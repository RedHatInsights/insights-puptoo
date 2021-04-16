from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

AZURE_PLAN_1 = """
{"name": "RHEL", "product": "RHEL7", "publisher": "Red Hat"}
""".strip()

AZURE_PLAN_2 = """
{"name": "", "product": "", "publisher": "Red Hat"}
""".strip()


def test_azure_instance_plan():
    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_1)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_2)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.azure_instance_plan, None)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is None
