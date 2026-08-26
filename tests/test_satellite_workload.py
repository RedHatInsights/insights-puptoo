import json

from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

SATELLITE_SERVER_RPMS = """
satellite-6.19.0-1.el9sat.noarch  Wed 20 May 2026 13:37:10 UTC   1770845372
""".strip()

SATELLITE_CAPSULE_RPMS = """
satellite-capsule-6.19.0-1.el9sat.noarch  Wed 20 May 2026 13:37:10 UTC   1770845372
""".strip()

NO_SATELLITE_RPMS = """
bash-5.1.8-6.el9.x86_64  Tue 14 Jul 2025 09:25:38 AEST   1398536494
""".strip()

FOREMANCTL_RPMS = """
foremanctl-1.1.0-1.el9.noarch  Wed 20 May 2026 13:37:10 UTC   1770845372
""".strip()

FOREMAN_CONTAINER: dict = {
    "Id": "f383",
    "Image": "quay.io/foreman/foreman:3.16",
    "Names": ["foreman"],
    "State": "running",
}

FOREMAN_PROXY_CONTAINER: dict = {
    "Id": "ddd",
    "Image": "quay.io/foreman/foreman-proxy:3.16",
    "Names": ["foreman-proxy"],
    "State": "running",
}

# A realistic containerized Satellite Server: the "foreman" container shares its
# image with the "dynflow-sidekiq-*" containers, so matching must be by name -
# only "foreman" is captured, not the dynflow-sidekiq workers. This server has
# no foreman-proxy container.
SERVER_CONTAINERS: list[dict] = [
    {
        "Id": "b2b9",
        "Image": "quay.io/sclorg/postgresql-13-c9s:latest",
        "Names": ["postgresql"],
        "State": "running",
    },
    {
        "Id": "fbbf",
        "Image": "quay.io/foreman/candlepin:foreman-3.16",
        "Names": ["candlepin"],
        "State": "running",
    },
    {
        "Id": "18ce",
        "Image": "quay.io/foreman/pulp:foreman-3.16",
        "Names": ["pulp-api"],
        "State": "running",
    },
    FOREMAN_CONTAINER,
    {
        "Id": "c350",
        "Image": "quay.io/foreman/foreman:3.16",
        "Names": ["dynflow-sidekiq-orchestrator"],
        "State": "running",
    },
    {
        "Id": "db99",
        "Image": "quay.io/foreman/foreman:3.16",
        "Names": ["dynflow-sidekiq-worker"],
        "State": "running",
    },
]

# A Satellite Server that also runs a foreman-proxy container.
SERVER_WITH_PROXY_CONTAINERS: list[dict] = SERVER_CONTAINERS + [FOREMAN_PROXY_CONTAINER]

# A containerized Capsule runs only the foreman-proxy container.
CAPSULE_CONTAINERS: list[dict] = [FOREMAN_PROXY_CONTAINER]

# No foreman / foreman-proxy containers at all.
NO_FOREMAN_CONTAINERS: list[dict] = [
    {
        "Id": "b2b9",
        "Image": "quay.io/sclorg/postgresql-13-c9s:latest",
        "Names": ["postgresql"],
        "State": "running",
    },
]

EXPECTED_FOREMAN: dict = {
    "name": "foreman",
    "image": "quay.io/foreman/foreman:3.16",
    "state": "running",
}

EXPECTED_FOREMAN_PROXY: dict = {
    "name": "foreman-proxy",
    "image": "quay.io/foreman/foreman-proxy:3.16",
    "state": "running",
}


def test_satellite_server():
    input_data = InputData().add(Specs.installed_rpms, SATELLITE_SERVER_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {"type": "server", "version": "6.19.0"}


def test_satellite_capsule():
    input_data = InputData().add(Specs.installed_rpms, SATELLITE_CAPSULE_RPMS)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {"type": "capsule", "version": "6.19.0"}


def test_no_satellite():
    input_data = InputData().add(Specs.installed_rpms, NO_SATELLITE_RPMS)
    result = run_test(system_profile, input_data)
    assert "satellite" not in result.get("workloads", {})


def test_satellite_containerized_server():
    input_data = (
        InputData()
        .add(Specs.installed_rpms, FOREMANCTL_RPMS)
        .add(Specs.podman_ps_all_json, json.dumps(SERVER_CONTAINERS))
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "server",
        "foremanctl_version": "1.1.0",
        "containers": [EXPECTED_FOREMAN],
    }


def test_satellite_containerized_server_with_proxy():
    input_data = (
        InputData()
        .add(Specs.installed_rpms, FOREMANCTL_RPMS)
        .add(Specs.podman_ps_all_json, json.dumps(SERVER_WITH_PROXY_CONTAINERS))
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "server",
        "foremanctl_version": "1.1.0",
        "containers": [EXPECTED_FOREMAN, EXPECTED_FOREMAN_PROXY],
    }


def test_satellite_containerized_capsule():
    input_data = (
        InputData()
        .add(Specs.installed_rpms, FOREMANCTL_RPMS)
        .add(Specs.podman_ps_all_json, json.dumps(CAPSULE_CONTAINERS))
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "capsule",
        "foremanctl_version": "1.1.0",
        "containers": [EXPECTED_FOREMAN_PROXY],
    }


def test_satellite_containers_without_foremanctl():
    # Containerized Satellite discovered from containers alone (no foremanctl RPM)
    input_data = InputData().add(
        Specs.podman_ps_all_json, json.dumps(SERVER_CONTAINERS)
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "server",
        "containers": [EXPECTED_FOREMAN],
    }


def test_satellite_containerized_overrides_rpm_type():
    # RPM says capsule, but the containerized foreman container makes it a server
    input_data = (
        InputData()
        .add(Specs.installed_rpms, SATELLITE_CAPSULE_RPMS + "\n" + FOREMANCTL_RPMS)
        .add(Specs.podman_ps_all_json, json.dumps(SERVER_CONTAINERS))
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "server",
        "version": "6.19.0",
        "foremanctl_version": "1.1.0",
        "containers": [EXPECTED_FOREMAN],
    }


def test_satellite_foremanctl_only_keeps_rpm_type():
    # Containerized foremanctl RPM but no foreman containers: RPM type stands
    input_data = (
        InputData()
        .add(Specs.installed_rpms, SATELLITE_SERVER_RPMS + "\n" + FOREMANCTL_RPMS)
        .add(Specs.podman_ps_all_json, json.dumps(NO_FOREMAN_CONTAINERS))
    )
    result = run_test(system_profile, input_data)
    assert result["workloads"]["satellite"] == {
        "type": "server",
        "version": "6.19.0",
        "foremanctl_version": "1.1.0",
    }
