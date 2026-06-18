from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

# ============================================================================
# Test Data for Azure Instance Plan (Legacy Parser - Backward Compatibility)
# ============================================================================

AZURE_PLAN_1 = """
{"name": "RHEL", "product": "RHEL7", "publisher": "Red Hat"}
""".strip()

AZURE_PLAN_2 = """
{"name": "", "product": "", "publisher": "Red Hat"}
""".strip()

AZURE_PLAN_3 = """
{"name": "", "product": "", "publisher": ""}
""".strip()

AZURE_PLAN_4 = """
{"name":"rhel-lvm77", "product":"rhel-byos", "publisher":"redhat"}
""".strip()

# ============================================================================
# Test Data for Azure Instance Compute Metadata (Current Parser)
# ============================================================================

# True - PAYG - is_marketplace = True
AZURE_INSTANCE_COMPUTE_METADATA_1 = """
{
    "isHostCompatibilityLayerVm": "false",
    "licenseType": "",
    "offer": "RHEL",
    "plan": {
        "name": "",
        "product": "",
        "publisher": ""
    }
}
""".strip()

# False - BYOS - is_marketplace = False
AZURE_INSTANCE_COMPUTE_METADATA_2 = """
{
    "isHostCompatibilityLayerVm": "true",
    "licenseType": "RHEL_BYOS",
    "offer": "RHEL",
    "plan": {
        "name": "",
        "product": "",
        "publisher": ""
    }
}
""".strip()

# False - BYOS - is_marketplace = False
AZURE_INSTANCE_COMPUTE_METADATA_3 = """
{
  "licenseType": "",
  "offer": "",
  "osType": "Linux",
  "plan": {
    "name": "rhel-lvm95",
    "product": "rhel-byos",
    "publisher": "redhat"
  }
}
""".strip()

# True - PAYG - is_marketplace = True
AZURE_INSTANCE_COMPUTE_METADATA_4 = """
{
  "licenseType": "",
  "offer": "",
  "plan": {
    "name": "",
    "product": "",
    "publisher": ""
  }
}
""".strip()

# False - BYOS - is_marketplace = False
AZURE_INSTANCE_COMPUTE_METADATA_5 = """
{
    "isHostCompatibilityLayerVm": "true",
    "licenseType": "",
    "offer": "RHEL_BYOS",
    "plan": {
        "name": "",
        "product": "",
        "publisher": ""
    }
}
""".strip()

# True - PAYG - is_marketplace = True
AZURE_INSTANCE_COMPUTE_METADATA_6 = """
{
  "licenseType": "",
  "offer": "",
  "osType": "Linux",
  "plan": {
    "name": "rhel-lvm95",
    "product": "some-value-other-than-rhel-byos",
    "publisher": "redhat"
  }
}
""".strip()


def test_azure_instance_plan():
    """
    Test azure_instance_plan:
     - Compatibility for customers with old insights-core version
     - To remove this after most customers have updated to insights-core 3.7.6+
    """
    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_1)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_2)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_3)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData().add(Specs.azure_instance_plan, None)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData().add(Specs.azure_instance_plan, AZURE_PLAN_4)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False


def test_azure_is_marketplace():
    """Test azure_is_marketplace"""
    input_data = InputData("on_value_fallback_to_payg")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_1)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is True

    input_data = InputData("on_license_type_byos")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_2)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData("on_product_plan_byos")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_3)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData("on_value_fallback_to_payg")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_4)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is True

    input_data = InputData("on_offer_byos")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_5)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData("on_product_plan_not_byos")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_6)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is True

    input_data = InputData("fallback_to_default")
    input_data.add(Specs.azure_instance_compute_metadata, None)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    # Compatibility test: test with both azure_instance_compute_metadata and azure_instance_plan
    input_data = InputData("use_azure_instance_compute_metadata_first")
    input_data.add(Specs.azure_instance_compute_metadata, AZURE_INSTANCE_COMPUTE_METADATA_2)
    input_data.add(Specs.azure_instance_plan, AZURE_PLAN_3)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False
