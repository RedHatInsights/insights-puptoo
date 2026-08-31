import json

import pytest
from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
ansible-tower-1.0.0-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
catalog-worker-1.0.2-1.x86_64    Tue 14 Jul 2015 09:25:40 AEST   1390535634
automation-hub-1.0.3-1.x86_64       Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-controller-1.0.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
receptor-1.4.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
ansible-runner-2.3.4-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-eda-controller-1.0.5-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-gateway-2.5.0-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_EXECUTION_NODE = """
receptor-1.4.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
ansible-runner-2.3.4-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_RECEPTOR_ONLY = """
receptor-1.4.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_RUNNER_ONLY = """
ansible-runner-2.3.4-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_EDA_ONLY = """
automation-eda-controller-1.0.5-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

RPMS_GATEWAY_ONLY = """
automation-gateway-2.5.0-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()

# Raw podman container jsons for a containerized AAP deployment. The postgresql
# container is not part of AAP (its image lacks the marker) and must be ignored.
AAP_CONTAINERS: list[dict] = [
    {
        "Id": "pg",
        "Image": "registry.redhat.io/rhel9/postgresql-15:latest",
        "Names": ["postgresql"],
        "State": "running",
    },
    {
        "Id": "gw",
        "Image": "registry.redhat.io/ansible-automation-platform-27/gateway-rhel9:latest",
        "Names": ["automation-gateway"],
        "State": "running",
    },
    {
        "Id": "rc",
        "Image": "registry.redhat.io/ansible-automation-platform-27/receptor-rhel9:latest",
        "Names": ["receptor"],
        "State": "stopped",
    },
]

NO_AAP_CONTAINERS: list[dict] = [
    {
        "Id": "pg",
        "Image": "registry.redhat.io/rhel9/postgresql-15:latest",
        "Names": ["postgresql"],
        "State": "running",
    },
]

EXPECTED_AAP_CONTAINERS: list[dict] = [
    {
        "name": "automation-gateway",
        "image": "registry.redhat.io/ansible-automation-platform-27/gateway-rhel9:latest",
        "state": "running",
    },
    {
        "name": "receptor",
        "image": "registry.redhat.io/ansible-automation-platform-27/receptor-rhel9:latest",
        "state": "stopped",
    },
]


def _add_containers(input_data: InputData, containers: list[dict]) -> InputData:
    return input_data.add(Specs.podman_ps_all_json, json.dumps(containers))


def test_ansible_info():
    # RPM data only, the podman spec was not collected -> no "containers" key.
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "hub_version": "1.0.3",
        "catalog_worker_version": "1.0.2",
        "controller_version": "1.0.0",
        "receptor_version": "1.4.1",
        "runner_version": "2.3.4",
        "eda_controller_version": "1.0.5",
        "gateway_version": "2.5.0",
    }


def test_ansible_info_execution_node():
    input_data = InputData().add(Specs.installed_rpms, RPMS_EXECUTION_NODE)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "receptor_version": "1.4.1",
        "runner_version": "2.3.4",
    }


def test_ansible_info_receptor_only():
    input_data = InputData().add(Specs.installed_rpms, RPMS_RECEPTOR_ONLY)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "receptor_version": "1.4.1",
    }


def test_ansible_info_runner_only():
    input_data = InputData().add(Specs.installed_rpms, RPMS_RUNNER_ONLY)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "runner_version": "2.3.4",
    }


def test_ansible_info_eda_only():
    input_data = InputData().add(Specs.installed_rpms, RPMS_EDA_ONLY)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "eda_controller_version": "1.0.5",
    }


def test_ansible_info_gateway_only():
    input_data = InputData().add(Specs.installed_rpms, RPMS_GATEWAY_ONLY)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "gateway_version": "2.5.0",
    }


def test_ansible_containers():
    input_data = _add_containers(InputData(), AAP_CONTAINERS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"]["containers"] == EXPECTED_AAP_CONTAINERS


def test_ansible_info_and_containers():
    input_data = _add_containers(
        InputData().add(Specs.installed_rpms, RPMS), AAP_CONTAINERS
    )
    result = run_test(system_profile, input_data)
    ansible = result["workloads"]["ansible"]
    assert ansible["controller_version"] == "1.0.0"
    assert ansible["containers"] == EXPECTED_AAP_CONTAINERS


@pytest.mark.parametrize("containers", [NO_AAP_CONTAINERS, []])
def test_ansible_info_and_no_containers_collected(containers):
    # RPM data present, podman collected but no AAP containers found -> the empty
    # "containers" list is kept to signal "collected, none found". An empty
    # podman list behaves the same as a list without AAP containers.
    input_data = _add_containers(
        InputData().add(Specs.installed_rpms, RPMS), containers
    )
    result = run_test(system_profile, input_data)
    ansible = result["workloads"]["ansible"]
    assert ansible["controller_version"] == "1.0.0"
    assert ansible["containers"] == []


def test_no_ansible_containers():
    # podman collected but no AAP containers, and no ansible RPM data -> the
    # whole ansible workload is absent.
    input_data = _add_containers(InputData(), NO_AAP_CONTAINERS)
    result = run_test(system_profile, input_data)
    assert "ansible" not in result.get("workloads", {})
