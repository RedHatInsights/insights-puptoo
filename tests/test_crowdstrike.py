from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

FALCONCTL_AID = """
aid="44e3b7d20b434a2bb2815d9808fa3a8b".
""".strip()

FALCONCTL_BACKEND = """
backend=kernel.
""".strip()

FALCONCTL_VERSION = """
version = 7.14.16703.0
""".strip()


def test_crowdstrike():

    # ### test_crowdstrike_has_three_facts

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    input_data.add(Specs.falconctl_version, FALCONCTL_VERSION)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
        "falcon_version": "7.14.16703.0",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
        "falcon_version": "7.14.16703.0",
    }

    # ### test_crowdstrike_has_two_facts

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    input_data.add(Specs.falconctl_version, "")
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
        "falcon_backend": "kernel",
    }

    # ### test_crowdstrike_has_one_facts

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, FALCONCTL_AID)
    input_data.add(Specs.falconctl_backend, "")
    input_data.add(Specs.falconctl_version, "")
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_aid": "44e3b7d20b434a2bb2815d9808fa3a8b",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_backend": "kernel",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_backend": "kernel",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, FALCONCTL_BACKEND)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_backend": "kernel",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_backend": "kernel",
    }

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, "")
    input_data.add(Specs.falconctl_version, FALCONCTL_VERSION)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["crowdstrike"] == {
        "falcon_version": "7.14.16703.0",
    }
    assert result["workloads"]["crowdstrike"] == {
        "falcon_version": "7.14.16703.0",
    }

    # ### test_crowdstrike_has_no_facts
    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, "")
    input_data.add(Specs.falconctl_version, "")
    result = run_test(system_profile, input_data)
    assert "workloads" not in result

    input_data = InputData()
    input_data.add(Specs.falconctl_aid, "")
    input_data.add(Specs.falconctl_backend, "")
    result = run_test(system_profile, input_data)
    assert "workloads" not in result
