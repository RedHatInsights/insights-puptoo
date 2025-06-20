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

SUBSCRIPTION_MANAGER_SYSPURPOSE_4 = """
{
  "addons": [],
  "role": "RHEL Server",
  "service_level_agreement": "Dev-Professional",
  "usage": "glb8_ready"
}
""".strip()

SUBSCRIPTION_MANAGER_SYSPURPOSE_5 = """
{
  "addons": [],
  "role": "RHEL Server",
  "service_level_agreement": "None",
  "usage": "glb8_ready"
}
""".strip()

SUBSCRIPTION_MANAGER_SYSPURPOSE_6 = """
{
  "addons": [],
  "role": null,
  "service_level_agreement": "",
  "usage": null
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

    input_data = InputData("test_system_purpose_with_not_validlisted_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_4)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "RHEL Server",
        "sla": "Dev-Professional",
        "usage": "glb8_ready"
    }

    input_data = InputData("test_system_purpose_with_valid_listed_none_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_5)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "RHEL Server",
        "sla": "None",
        "usage": "glb8_ready"
    }

    input_data = InputData("test_system_purpose_with_valid_listed_wo_values")
    input_data.add(Specs.subscription_manager_syspurpose, SUBSCRIPTION_MANAGER_SYSPURPOSE_6)
    result = run_test(system_profile, input_data)
    assert result["system_purpose"] == {
        "role": "",
        "sla": "",
        "usage": ""
    }
