from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

IB_FACTS = """
{
  "image-builder.insights.compliance-policy-id": "76a67c05-64c4-4d3e-a539-a48bb12bf084",
  "image-builder.insights.compliance-profile-id": "xccdf_org.ssgproject.content_profile_cis",
  "image-builder.blueprint-id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0"
}
""".strip()

IB_FACTS_WITH_EXTRA_KEYS = """
{
  "image-builder.insights.compliance-policy-id": "76a67c05-64c4-4d3e-a539-a48bb12bf084",
  "image-builder.insights.compliance-profile-id": "xccdf_org.ssgproject.content_profile_cis",
  "image-builder.blueprint-id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0",
  "extra-key": "extra-value"
}
""".strip()

IB_FACTS_EMPTY = """
{}
""".strip()

IB_FACTS_BLUEPRINT_ONLY = """
{
  "image-builder.blueprint-id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0"
}
""".strip()

def test_image_builder_facts():
    input_data = InputData().add(Specs.image_builder_facts, IB_FACTS)
    result = run_test(system_profile, input_data)
    assert result["image_builder"] == {
        "compliance_policy_id": "76a67c05-64c4-4d3e-a539-a48bb12bf084",
        "compliance_profile_id": "xccdf_org.ssgproject.content_profile_cis",
        "blueprint_id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0",
    }

    input_data = InputData().add(Specs.image_builder_facts, IB_FACTS_WITH_EXTRA_KEYS)
    result = run_test(system_profile, input_data)
    assert result["image_builder"] == {
        "compliance_policy_id": "76a67c05-64c4-4d3e-a539-a48bb12bf084",
        "compliance_profile_id": "xccdf_org.ssgproject.content_profile_cis",
        "blueprint_id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0",
    }

    input_data = InputData().add(Specs.image_builder_facts, IB_FACTS_EMPTY)
    result = run_test(system_profile, input_data)
    assert "image_builder" not in result

def test_image_builder_blueprint_id_only():
    input_data = InputData().add(Specs.image_builder_facts, IB_FACTS_BLUEPRINT_ONLY)
    result = run_test(system_profile, input_data)
    assert result["image_builder"] == {
        "blueprint_id": "d4c16228-7ynb-4e52-b4a1-592a6174e2a0",
    }
