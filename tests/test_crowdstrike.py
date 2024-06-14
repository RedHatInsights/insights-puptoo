from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

FALCONCTL_AID = """
aid="44e3b7d20b434a2bb2815d9808fa3a8b".
""".strip()

FALCONCTL_BACKEND = """
backend=kernel.
""".strip()


def test_crowdstrike():
    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    result = run_test(system_profile, input_data)
    assert result["third_party_services"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, "")
    result = run_test(system_profile, input_data)
    assert result["third_party_services"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    result = run_test(system_profile, input_data)
    assert result["third_party_services"]["crowdstrike"] == {
        "falcon_backend": "kernel",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, "")
    result = run_test(system_profile, input_data)
    assert "third_party_services" not in result
