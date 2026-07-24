"""Pytest fixtures for IQE Puptoo plugin."""

import json
import logging
import uuid
from collections.abc import Callable, Iterator
from os import remove
from os.path import isfile

import pytest
from iqe.base.application import Application
from iqe.utils.archive import InsightsArchiveInMemory, get_insights_archive
from iqe_bindings.v7.ingress_v1.api.ingress_api import IngressApi

from iqe_puptoo.utils.archive_utils import get_archive_path

logger = logging.getLogger(__name__)


@pytest.fixture
def ingress_rest_client(application: Application) -> IngressApi:
    """Return an Ingress API rest client."""
    ingress_api = application.puptoo.v7_ingress_v1.ingress_api

    if application.puptoo.config.env_for_dynaconf == "clowder_smoke":
        ingress_api.api_client.default_headers["x-rh-insights-request-id"] = str(
            uuid.uuid4()
        ).replace("-", "")

    return ingress_api


@pytest.fixture
def puptoo_insights_archive() -> Iterator[InsightsArchiveInMemory]:
    """Yield an Insights archive in memory with randomized data."""
    ia: InsightsArchiveInMemory | None = None

    def _puptoo_insights_archive(
        archive_name: str | None = None,
        archive_base_dir: str = "puptoo",
        *,
        core_collect: bool | None = True,
    ) -> InsightsArchiveInMemory:
        archive_path = None
        if archive_name:
            archive_path = get_archive_path(archive_name, archive_base_dir)

        nonlocal ia
        ia = get_insights_archive(
            filename=archive_path,
            in_memory=True,
            dump=True,
            hostname=f"rhiqe-puptoo-{uuid.uuid4()!s}.test",
            subscription_manager_id=str(uuid.uuid4()),
            core_collect_default_structure=core_collect,
        )

        return ia

    yield _puptoo_insights_archive

    if ia and isfile(ia.filename):
        logger.info(f"Deleting archive: {ia.filename}")
        remove(ia.filename)


@pytest.fixture
def minimal_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive in memory with minimal files."""
    return puptoo_insights_archive()


@pytest.fixture
def classic_collect_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive collected with the flag core_collect=False."""
    return puptoo_insights_archive("rhel84_classic_collect.tar.gz", core_collect=False)


@pytest.fixture
def core_collect_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive collected with the flag core_collect=True."""
    return puptoo_insights_archive("rhel84_core_collect.tar.gz")


@pytest.fixture
def sap_hana_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive collected from a SAP system."""
    ia = puptoo_insights_archive("sap_core_collect.tar.gz")
    ia.add_sids(["PUP"])
    return ia


@pytest.fixture
def sap_without_sids_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive collected from a SAP system without adding instances."""
    return puptoo_insights_archive("sap_core_collect.tar.gz")


@pytest.fixture
def aws_insights_archive(puptoo_insights_archive: Callable) -> InsightsArchiveInMemory:
    """Return an Insights archive collected from a system running on AWS."""
    return puptoo_insights_archive("rhel_92_aws.tar.gz")


@pytest.fixture
def azure_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive collected from a system running on Azure."""
    return puptoo_insights_archive("rhel_86_azure.tar.gz")


@pytest.fixture
def gcp_insights_archive(puptoo_insights_archive: Callable) -> InsightsArchiveInMemory:
    """Return an Insights archive collected from a system running on GCP."""
    return puptoo_insights_archive("rhel_86_gcp.tar.gz")


@pytest.fixture
def systemd_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a systemd file."""
    return puptoo_insights_archive("systemd_archive.tar.gz", "puptoo")


@pytest.fixture
def centos_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a systemd file."""
    return puptoo_insights_archive("centos_8_archive.tar.gz", "puptoo")


@pytest.fixture
def sample_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a systemd file."""
    return puptoo_insights_archive("sample_archive_rhel.tar.gz", "puptoo")


@pytest.fixture
def rhel7_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that from rhel7.8 system."""
    return puptoo_insights_archive("rhel78.tar.gz", "puptoo")


@pytest.fixture
def rhel_ai_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that from RHEL_AI system."""
    return puptoo_insights_archive("rhel_ai_with_nvidia_gpu.tar.gz", "puptoo")


@pytest.fixture
def ansible_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a systemd file."""
    return puptoo_insights_archive("sample_archive_ansible.tar.gz", "puptoo")


@pytest.fixture
def mssql_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a systemd file."""
    return puptoo_insights_archive("sample_archive_mssql.tar.gz", "puptoo")


@pytest.fixture
def missing_id_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has the missing id."""
    ia = puptoo_insights_archive("missing_id_fact.gz", "puptoo")
    subman_path = "/insights_commands/subscription-manager_identity"
    ia.removefile(subman_path)
    ia.subscription_manager_id = None
    return ia


@pytest.fixture
def non_utf8_locale_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a French output."""
    ia = puptoo_insights_archive("french-output.tar.gz", "puptoo")

    # Simulated French output from `subscription-manager identity`
    ia.subscription_manager_id = "e7469b00-5d39-4ae1-8f1a-bdee58d0789f"
    french_output = (
        f"identité du système : {ia.subscription_manager_id}\n"  # noqa: RUF001
        "nom : SRVSNA44\n"
        "nom de l'organisation : 5027709\n"
        "ID de l'organisation : 5027709\n"  # noqa: RUF001
    )
    files = {"data/insights_commands/subscription-manager_identity": french_output}

    ia.changefile(files)

    return ia


@pytest.fixture
def system_purpose_rhel_archive(
    puptoo_insights_archive: Callable,
) -> Callable[[str], InsightsArchiveInMemory]:
    """Return an Insights archive that has a realistic syspurpose output."""

    def _create(archive_filename: str) -> InsightsArchiveInMemory:
        ia = puptoo_insights_archive(archive_filename, "puptoo")

        # Simulate the real output of `subscription-manager syspurpose --show`
        system_purpose_content = """
            {\n
            "addons":[],\n
            "role": "Red Hat Enterprise Linux Server",\n
            "service_level_agreement": "Standard",\n
            "usage": "Test"\n
            }\n
            """
        file = {
            "data/insights_commands/subscription-manager_syspurpose_--show": system_purpose_content
        }
        ia.changefile(file)

        system_purpose_content_json = """
            {"name": "insights.specs.Specs.subscription_manager_syspurpose",
            "exec_time": 0.0002918243408203125,
            "errors": [],
            "results": {"type": "insights.core.spec_factory.CommandOutputProvider",
            "object": {"rc": null, "cmd": "/usr/sbin/subscription-manager syspurpose --show",
            "args": null, "relative_path": "insights_commands/subscription-manager_syspurpose_--show"}},
            "ser_time": 2.20603346824646}"""
        file = {
            "meta_data/insights.specs.Specs.subscription_manager_syspurpose.json": system_purpose_content_json
        }
        ia.changefile(file)

        return ia

    return _create


@pytest.fixture
def image_mode_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that from Image Mode (RHEL AI) system."""
    return puptoo_insights_archive("image_mode_insights_archive.tar.gz", "puptoo")


@pytest.fixture
def edge_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that from Edge system."""
    return puptoo_insights_archive("edge_insights_archive.tar.gz", "puptoo")


@pytest.fixture
def bootc_status_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has a bootc_status_--json file."""
    ia = puptoo_insights_archive("sample_archive_rhel.tar.gz", "puptoo")

    bootc_status_dict = {
        "apiVersion": "org.containers.bootc/v1alpha1",
        "kind": "BootcHost",
        "metadata": {"name": "host"},
        "spec": {
            "image": {
                "image": "192.168.122.1:5000/bootc-insights:latest",
                "transport": "registry",
            }
        },
        "status": {
            "staged": {
                "image": {
                    "image": {
                        "image": "192.168.122.1:5000/bootc-insights:latest",
                        "transport": "registry",
                    },
                    "version": "9.20240325.0",
                    "timestamp": None,
                    "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
                },
                "cachedUpdate": {
                    "image": {
                        "image": "192.168.122.1:5000/bootc-insights:latest",
                        "transport": "registry",
                    },
                    "version": "9.20240325.0",
                    "timestamp": None,
                    "imageDigest": "sha256:3c1cea8218e4331641020c59e0877ae20ec058e34a346fa424bbe726daab294e",
                },
                "incompatible": False,
                "pinned": False,
                "ostree": {
                    "checksum": "91aeb5bdff14917ff7e6b525d2253b40c0ab632e3aa16de72592603acffe592d",
                    "deploySerial": 0,
                },
            },
            "booted": {
                "image": {
                    "image": {
                        "image": "192.168.122.1:5000/bootc-insights:latest",
                        "transport": "registry",
                    },
                    "version": "9.20240325.0",
                    "timestamp": None,
                    "imageDigest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e",
                },
                "cachedUpdate": {
                    "image": {
                        "image": "192.168.122.1:5000/bootc-insights:latest",
                        "transport": "registry",
                    },
                    "version": "9.20240325.0",
                    "timestamp": None,
                    "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
                },
                "incompatible": False,
                "pinned": False,
                "ostree": {
                    "checksum": "759c97c3b3f7e9198b0f6e6f2b0fcd3c668bb39810742f207f85cfb0b2b398fd",
                    "deploySerial": 0,
                },
            },
            "rollback": {
                "image": {
                    "image": {
                        "image": "quay.io/centos-boot/fedora-boot-cloud:eln",
                        "transport": "registry",
                    },
                    "version": "39.20231109.3",
                    "timestamp": None,
                    "imageDigest": "sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0",
                },
                "incompatible": False,
                "pinned": False,
                "ostree": {
                    "checksum": "56612a5982b7f12530988c970d750f89b0489f1f9bebf9c2a54244757e184dd8",
                    "deploySerial": 0,
                },
            },
            "type": "bootcHost",
        },
    }

    bootc_status_json = json.dumps(bootc_status_dict, indent=2)
    json_file = {"data/insights_commands/bootc_status_--json": bootc_status_json}
    ia.changefile(json_file)

    bootc_status_spec_dict = {
        "name": "insights.specs.Specs.bootc_status",
        "exec_time": 3.0994415283203125e-05,
        "errors": [],
        "results": {
            "type": "insights.core.spec_factory.CommandOutputProvider",
            "object": {
                "rc": None,
                "cmd": "/usr/bin/bootc status --json",
                "args": None,
                "relative_path": "insights_commands/bootc_status_--json",
            },
        },
        "ser_time": 0.00862431526184082,
    }

    bootc_status_json_spec = json.dumps(bootc_status_spec_dict, indent=2)
    ia.changefile({"meta_data/insights.specs.Specs.bootc_status.json": bootc_status_json_spec})

    return ia


@pytest.fixture
def tags_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that has the tag file."""
    ia = puptoo_insights_archive("sample_archive_rhel.tar.gz", "puptoo")

    tags_dict = [
        {"key": "oOIkf", "namespace": "WPPbJ", "value": "NZqaX"},
        {"key": "yajSI", "namespace": "wZcvvi", "value": "gtCEfPRcuA"},
        {"key": "GwgKZyrlqs", "namespace": "fdyXeLM", "value": "CSRSJ"},
        {"key": "UGJPhiG", "namespace": "xHqwe", "value": "RZeCFZ"},
        {"key": "ySqCh", "namespace": "crcPNLnTlI", "value": "UqUIQStxs"},
    ]

    tags_json = json.dumps(tags_dict, indent=2)
    json_file = {"data/tags.json": tags_json}
    ia.changefile(json_file)

    tags_spec_dict = {
        "name": "insights.specs.Specs.tags",
        "exec_time": 2.9325485229492188e-05,
        "errors": [],
        "results": {
            "type": "insights.core.spec_factory.DatasourceProvider",
            "object": {"relative_path": "data/tags.json"},
        },
        "ser_time": 6.246566772460938e-05,
    }

    tags_json_spec = json.dumps(tags_spec_dict, indent=2)
    ia.changefile({"meta_data/insights.specs.Specs.tags.json": tags_json_spec})

    return ia


@pytest.fixture
def generate_unique_archive():
    """Take an existing insights archive and tweak uuid's/hostnames/etc. to make it a unique report."""

    def _gen(
        archive_name: str | None = None,
        archive_base_dir: str = "puptoo",
        *,
        core_collect: bool | None = True,
    ):
        archive_path = None
        if archive_name:
            archive_path = get_archive_path(archive_name, archive_base_dir)
        return get_insights_archive(
            filename=archive_path,
            in_memory=True,
            dump=True,
            hostname=f"rhiqe-puptoo-{uuid.uuid4()!s}.test",
            subscription_manager_id=str(uuid.uuid4()),
            core_collect_default_structure=core_collect,
        )

    return _gen


@pytest.fixture
def build_insights_archive_installed_product(puptoo_insights_archive: Callable):
    """Fixture to build an Insights archive in memory with customized installed product certificates.

    This fixture returns a factory function `_build` that allows tests to inject
    different `cert_content` into a base Insights archive. The resulting archive
    can then be uploaded via PUPTOO and inspected in Inventory for validation.

    purpose:
        - Enable tests to create customized Insights archives
        - Support multiple installed product scenarios (single, multiple, duplicate)

    Returns:
        Callable[[str], InsightsArchiveInMemory]: A factory function that accepts
        `cert_content` as a string and returns an in-memory Insights archive
        containing that content.
    """

    def _build(cert_content: str) -> InsightsArchiveInMemory:
        ia = puptoo_insights_archive("sample_archive_rhel.tar.gz", "puptoo")

        file_name = (
            "data/insights_commands/"
            "find_.etc.pki.product-default._.etc.pki.product._-name_pem_-exec_rct_cat-cert_--no-content"
        )

        ia.changefile({file_name: cert_content})
        return ia

    return _build


@pytest.fixture
def empty_value_insights_archive(
    puptoo_insights_archive: Callable,
) -> InsightsArchiveInMemory:
    """Return an Insights archive that have several empty values."""
    return puptoo_insights_archive("sample_empty_values.tar.gz", "puptoo")


@pytest.fixture
def build_insights_archive_systemctl_status(puptoo_insights_archive: Callable):
    """Fixture to build an Insights archive in memory with customized systemctl_status output.

    Returns a factory function `_build` that accepts a string content for
    'systemctl_status_--all' and creates an in-memory archive with:
      1. data/insights_commands/systemctl_status_--all
      2. dev/test-archives/core-base/meta_data/insights.specs.Specs.systemctl_status_all.json
    """

    def _build(systemctl_status_content: str) -> "InsightsArchiveInMemory":
        ia = puptoo_insights_archive("sample_archive_rhel.tar.gz", "puptoo")

        # systemctl_status_--all
        file_name = "data/insights_commands/systemctl_status_--all"
        ia.changefile({file_name: systemctl_status_content})

        # meta_data JSON
        meta_file_name = "meta_data/insights.specs.Specs.systemctl_status_all.json"

        meta_content = {
            "name": "insights.specs.Specs.systemctl_status_all",
            "exec_time": 0.0,
            "errors": [],
            "results": {
                "type": "insights.core.spec_factory.CommandOutputProvider",
                "object": {
                    "rc": None,
                    "cmd": "/bin/systemctl status --all",
                    "args": None,
                    "save_as": False,
                    "relative_path": "insights_commands/systemctl_status_--all",
                },
            },
            "ser_time": 0.0,
        }

        ia.changefile({meta_file_name: json.dumps(meta_content, indent=4)})

        return ia

    return _build
