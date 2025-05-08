from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

SUBSCRIPTION_MANAGER_SYSPURPOSE_1 = """
{
  "addons": [],
  "role": "Red Hat Enterprise Linux Server",
  "service_level_agreement": "Standard",
  "usage": "Development/Test"
}
""".strip()

SUBSCRIPTION_MANAGER_SYSPURPOSE_2 = """
{
  "addons": [],
  "role": "",
  "service_level_agreement": "",
  "usage": "Development/Test"
}
""".strip()

SUBSCRIPTION_MANAGER_SYSPURPOSE_3 = """
{
  "addons": [],
  "role": "",
  "service_level_agreement": "",
  "usage": ""
}
""".strip()


def test_system_purpose():
    input_data = InputData("test_system_purpose_with_all_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_1)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "Red Hat Enterprise Linux Server",
        "sla": "Standard",
        "usage": "Development/Test"
    }

    input_data = InputData("test_system_purpose_with_some_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_2)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "",
        "sla": "",
        "usage": "Development/Test"
    }

    input_data = InputData("test_system_purpose_with_no_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_3)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "",
        "sla": "",
        "usage": ""
    }

    input_data = InputData("test_system_purpose_without_fact")
    input_data.add(Specs.subscription_manager_syspurpose, "")
    result = run_test(system_profile, input_data)
    assert "system_purpose" not in result
