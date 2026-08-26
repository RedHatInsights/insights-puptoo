import json
from collections.abc import Callable

import pytest
from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
ansible-tower-1.0.0-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
catalog-worker-1.0.2-1.x86_64    Tue 14 Jul 2015 09:25:40 AEST   1390535634
automation-hub-1.0.3-1.x86_64       Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-controller-1.0.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
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


def _rootless(containers: list[dict], user: str = "aap") -> str:
    """Build rootless content: a list of ``{"user", "containers"}`` groups."""
    return json.dumps([{"user": user, "containers": containers}])


# Containerized AAP is almost always deployed rootless, so rootless is the
# primary case; the rootful spec is exercised too for completeness.
def _add_rootless(input_data: InputData, containers: list[dict]) -> InputData:
    return input_data.add(Specs.podman_ps_all_json_rootless, _rootless(containers))


def _add_rootful(input_data: InputData, containers: list[dict]) -> InputData:
    return input_data.add(Specs.podman_ps_all_json, json.dumps(containers))


AddContainers = Callable[[InputData, list[dict]], InputData]

ADD_CONTAINERS: list = [
    pytest.param(_add_rootless, id="rootless"),
    pytest.param(_add_rootful, id="rootful"),
]


def test_ansible_info():
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"] == {
        "hub_version": "1.0.3",
        "catalog_worker_version": "1.0.2",
        "controller_version": "1.0.0",
    }


@pytest.mark.parametrize("add_containers", ADD_CONTAINERS)
def test_ansible_containers(add_containers: AddContainers):
    input_data = add_containers(InputData(), AAP_CONTAINERS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ansible"]["containers"] == EXPECTED_AAP_CONTAINERS


@pytest.mark.parametrize("add_containers", ADD_CONTAINERS)
def test_ansible_info_and_containers(add_containers: AddContainers):
    input_data = add_containers(
        InputData().add(Specs.installed_rpms, RPMS), AAP_CONTAINERS
    )
    result = run_test(system_profile, input_data)
    ansible = result["workloads"]["ansible"]
    assert ansible["controller_version"] == "1.0.0"
    assert ansible["containers"] == EXPECTED_AAP_CONTAINERS


@pytest.mark.parametrize("add_containers", ADD_CONTAINERS)
def test_no_ansible_containers(add_containers: AddContainers):
    input_data = add_containers(InputData(), NO_AAP_CONTAINERS)
    result = run_test(system_profile, input_data)
    assert "ansible" not in result.get("workloads", {})
