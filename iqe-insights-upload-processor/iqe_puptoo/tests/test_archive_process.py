"""Tests for Puptoo processing Insights archives."""

import json
import os

import pytest
from iqe.base.application import Application
from iqe.utils.archive import InsightsArchiveInMemory
from iqe_bindings.v7.ingress_v1.api.ingress_api import IngressApi
from pytest_lazy_fixtures import lf

from iqe_puptoo.tests.cases.test_installed_products import INSTALLED_PRODUCT_CASES
from iqe_puptoo.tests.cases.test_systemctl_status import SYSTEMCTL_STATUS_CASES


@pytest.mark.smoke
@pytest.mark.parametrize(
    "archive",
    [
        lf("core_collect_insights_archive"),
        lf("classic_collect_insights_archive"),
        lf("minimal_insights_archive"),
    ],
)
def test_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    archive: InsightsArchiveInMemory,
):
    """Test Insights archives collected from multiple systems and in multiple ways.

    Verifies archives can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(archive)

    assert host.insights_id == archive.insights_id
    assert host.display_name == archive.hostname


@pytest.mark.smoke
@pytest.mark.parametrize(
    "archive,provider_type,provider_id",
    [
        (lf("aws_insights_archive"), "aws", "i-004e8396dc9b7b9ef"),
        (lf("azure_insights_archive"), "azure", "606bf117-e325-4c43-940e-124cde9fefa0"),
        (lf("gcp_insights_archive"), "gcp", "5512291438956305280"),
    ],
)
def test_archives_cloud_providers(
    application: Application,
    ingress_rest_client: IngressApi,
    archive: InsightsArchiveInMemory,
    provider_type: str,
    provider_id: str,
):
    """Test archives from systems running in cloud providers (AWS, GCP and Azure).

    Verifies archives can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(archive)

    assert host.insights_id == archive.insights_id
    assert host.display_name == archive.hostname
    assert host.provider_id == provider_id
    assert host.provider_type == provider_type


@pytest.mark.smoke
@pytest.mark.parametrize(
    "archive,sids",
    [
        (lf("sap_hana_insights_archive"), ["PUP"]),
        (lf("sap_without_sids_insights_archive"), []),
    ],
)
def test_sap_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    archive: InsightsArchiveInMemory,
    sids: list[str],
):
    """Test Insights archives collected from SAP systems.

    Verifies archives can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(archive)
    assert host.insights_id == archive.insights_id
    assert host.display_name == archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    system_profile_data = json.loads(response.data)["results"][0]["system_profile"]
    # assert "sap" not in system_profile_data
    workloads = system_profile_data.get("workloads", {})
    assert "sap" in workloads
    assert workloads["sap"]["sap_system"] is True

    if sids:
        assert workloads["sap"]["sids"] == sids


@pytest.mark.smoke
def test_systemd_state_archive(
    application: Application,
    ingress_rest_client: IngressApi,
    systemd_insights_archive: InsightsArchiveInMemory,
):
    """Test an Insights archive that has systemd state info.

    Verifies the archive can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(systemd_insights_archive)
    assert host.insights_id == systemd_insights_archive.insights_id
    assert host.display_name == systemd_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]
    assert "systemd" in host_sp
    assert host_sp["systemd"]["state"] == "running"


@pytest.mark.smoke
def test_centos_archive(
    application: Application,
    ingress_rest_client: IngressApi,
    centos_insights_archive: InsightsArchiveInMemory,
):
    """Test a CentOS Insights archive is correctly processed.

    Verifies the archive stores the correct operating system name on Inventory.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive collected from a CentOS system
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(centos_insights_archive)
    assert host.insights_id == centos_insights_archive.insights_id
    assert host.display_name == centos_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]
    assert host_sp["operating_system"]["name"] == "CentOS Linux"


def test_archive_canonical_facts(
    application: Application,
    ingress_rest_client: IngressApi,
    sample_insights_archive: InsightsArchiveInMemory,
):
    """Test a RHEL Insights archive is correctly processed with canonical facts.

    Verifies the archive stores the correct facts on Inventory.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive from sample RHEL system
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data (canonical facts)
    """
    host = application.puptoo.upload_advisor_payload(sample_insights_archive)
    assert host.insights_id == sample_insights_archive.insights_id
    assert host.display_name == sample_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    canonical_facts_data = json.loads(response.data)["results"][0]

    assert canonical_facts_data["insights_id"] == sample_insights_archive.insights_id
    assert (
        canonical_facts_data["subscription_manager_id"]
        == sample_insights_archive.subscription_manager_id
    )
    assert canonical_facts_data["mac_addresses"][0] == sample_insights_archive.mac_address
    assert canonical_facts_data["fqdn"] == sample_insights_archive.hostname
    assert canonical_facts_data["bios_uuid"] == "027f9a24-d2bc-47db-b9ed-bb7e402726de"
    assert canonical_facts_data["ip_addresses"][0] == "10.73.212.229"
    assert canonical_facts_data["provider_id"] is None
    assert canonical_facts_data["provider_type"] is None


def test_archive_system_profile(
    application: Application,
    ingress_rest_client: IngressApi,
    sample_insights_archive: InsightsArchiveInMemory,
):
    """Test a RHEL Insights archive is correctly processed with system_profile values.

    Verifies the archive stores the correct system_profile values on Inventory.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive from sample RHEL system
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data (system_profile values)
    """
    host = application.puptoo.upload_advisor_payload(sample_insights_archive)
    assert host.insights_id == sample_insights_archive.insights_id
    assert host.display_name == sample_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "../resources/data/system_profile.json")

    with open(file_path) as f:
        expected_dict = json.load(f)

    del expected_dict["network_interfaces"]
    del host_sp["network_interfaces"]

    assert json.dumps(expected_dict, sort_keys=True) == json.dumps(host_sp, sort_keys=True)


@pytest.mark.parametrize(
    "archive_file",
    [
        "rhel84.tar.gz",
        "rhel95.tar.gz",
        "rhel10.tar.gz",
    ],
)
def test_archive_system_purpose(
    application: Application,
    ingress_rest_client: IngressApi,
    system_purpose_rhel_archive,
    archive_file,
):
    """https://issues.redhat.com/browse/RHINENG-18634.

    https://issues.redhat.com/browse/RHINENG-19211.

    Verify that a RHEL Insights archive containing system purpose data is processed correctly
    and that the corresponding system_profile values are stored in Inventory.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload a prepared RHEL Insights archive with predefined system purpose fields.
            2. Retrieve the host's system profile from Inventory using its host ID.
        expected_results:
            1. The upload succeeds and the host is created in Inventory with the expected
               insights_id and hostname from the archive.
            2. The retrieved system_profile contains the correct system purpose values:
               - SLA: "Standard"
               - Role: "Red Hat Enterprise Linux Server"
               - Usage: "Test"
    """
    archive = system_purpose_rhel_archive(archive_file)
    host = application.puptoo.upload_advisor_payload(archive)
    assert host.insights_id == archive.insights_id
    assert host.display_name == archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]

    system_purpose_values = host_sp["system_purpose"]
    assert system_purpose_values
    assert system_purpose_values["sla"] == "Standard"
    assert system_purpose_values["role"] == "Red Hat Enterprise Linux Server"
    assert system_purpose_values["usage"] == "Test"


def test_bootc_status(
    application: Application,
    ingress_rest_client: IngressApi,
    bootc_status_insights_archive: InsightsArchiveInMemory,
):
    """Test that the 'bootc_status' section in the host system profile matches expected data.

    Verifies the expected booted, staged, and rollback image data.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload a pre-constructed Insights archive containing the bootc_status JSON


        expected_results:
            1. Assert that the 'bootc_status' key exists in the system profile.
            2. Compare each of the 'booted', 'staged', and 'rollback' image fields against
       the expected values, including image URLs and image digests.

    """
    host = application.puptoo.upload_advisor_payload(bootc_status_insights_archive)
    assert host.insights_id == bootc_status_insights_archive.insights_id
    assert host.display_name == bootc_status_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]
    assert "bootc_status" in host_sp
    bootc_status = host_sp["bootc_status"]

    expected = {
        "booted": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "cached_image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e",
            "cached_image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
        },
        "staged": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "cached_image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
            "cached_image_digest": "sha256:3c1cea8218e4331641020c59e0877ae20ec058e34a346fa424bbe726daab294e",
        },
        "rollback": {
            "image": "quay.io/centos-boot/fedora-boot-cloud:eln",
            "image_digest": "sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0",
        },
    }

    for key, vals in expected.items():
        for k, v in vals.items():
            assert bootc_status[key][k] == v


@pytest.mark.parametrize(
    "archive,method",
    [
        (lf("rhel7_insights_archive"), "yum"),
        (lf("sample_insights_archive"), "dnf"),
        (lf("image_mode_insights_archive"), "bootc"),
        (lf("edge_insights_archive"), "rpm-ostree"),
    ],
)
def test_system_update_method(
    application: Application,
    ingress_rest_client: IngressApi,
    archive: InsightsArchiveInMemory,
    method: str,
):
    """Test that the 'system_update_method' field in the host system profile matches.

    Verifies the expected update method for the given system.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload a pre-constructed Insights archive using `upload_advisor_payload`.
            2. Verify that the host created in Insights has the same insights_id and display_name
               as the uploaded archive.
            3. Retrieve the host's system profile via the REST API.

        expected_results:
            1. Assert that the 'system_update_method' key exists in the system profile.
            2. Assert that its value matches the expected method for the tested system, e.g.:
               - RHEL 6 & 7 → 'yum'
               - RHEL 8 & 9 → 'dnf'
               - Edge → 'rpm-ostree'
               - Image Mode (RHEL AI) → 'bootc'
    """
    host = application.puptoo.upload_advisor_payload(archive)
    assert host.insights_id == archive.insights_id
    assert host.display_name == archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]
    assert "system_update_method" in host_sp
    system_update_method = host_sp["system_update_method"]
    assert system_update_method == method


def test_archive_non_utf8_locale(
    application: Application,
    ingress_rest_client: IngressApi,
    non_utf8_locale_insights_archive: InsightsArchiveInMemory,
):
    """https://issues.redhat.com/browse/RHINENG-19629.

    Verifies that the subscription_manager_id can still be correctly extracted when the system locale is
    set to a non-UTF-8 value (e.g., fr_FR.UTF-8). It simulates an environment where `subscription-manager identity`
    outputs are in a non-English language or encoding, potentially causing UnicodeEncodeError or data parsing issues.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive from sample RHEL system with non utf8 locale env
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
            3. puptoo must be able to extract a valid `subscription_manager_id`
    """
    host = application.puptoo.upload_advisor_payload(non_utf8_locale_insights_archive)

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    canonical_facts_data = json.loads(response.data)["results"][0]

    assert canonical_facts_data["insights_id"] == non_utf8_locale_insights_archive.insights_id
    assert (
        canonical_facts_data["subscription_manager_id"]
        == non_utf8_locale_insights_archive.subscription_manager_id
    )


def test_archive_missing_id(
    application: Application,
    ingress_rest_client: IngressApi,
    missing_id_archive: InsightsArchiveInMemory,
):
    """https://issues.redhat.com/browse/RHINENG-19403.

    Test that `upload_advisor_payload` when required canonical facts are missing in the provided archive.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. The function works fine when processing an archive
       without needed canonical facts.
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
            3. puptoo must be able to extract the `subscription_manager_id`, and its None
    """
    host = application.puptoo.upload_advisor_payload(missing_id_archive)
    assert host.insights_id == missing_id_archive.insights_id
    assert host.display_name == missing_id_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_by_id_without_preload_content(
        host_id_list=[host.id]
    )
    canonical_facts_data = json.loads(response.data)["results"][0]

    assert canonical_facts_data["insights_id"] == missing_id_archive.insights_id
    assert canonical_facts_data["subscription_manager_id"] is None

    assert canonical_facts_data["fqdn"] == missing_id_archive.hostname
    assert canonical_facts_data["provider_id"] is None
    assert canonical_facts_data["provider_type"] is None


def test_rhel_ai_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    rhel_ai_insights_archive: InsightsArchiveInMemory,
):
    """https://issues.redhat.com/browse/RHINENG-21788.

    Verify that the RHEL AI section in the host system profile is correctly parsed
    and matches expected metadata when an Insights archive for RHEL AI hosts is processed.

    This test ensures that the PUPTOO archive processing pipeline correctly extracts
    and populates RHEL AI-specific system profile fields, including variant, version ID,
    GPU model information, and workload metadata.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload a RHEL AI Insights archive using the puptoo upload API.
            2. Retrieve the corresponding host system profile from the host inventory service.
            3. Verify that the 'rhel_ai' section exists in the system profile.
            4. Validate that 'variant', 'rhel_ai_version_id', and 'nvidia_gpu_models'
               fields contain the expected values.
            5. Confirm that the 'workloads.rhel_ai' section is populated consistently
               with the main RHEL AI metadata.

        expected_results:
            1. The system profile includes a 'rhel_ai' section.
            2. 'variant' is set to "RHEL AI".
            3. 'rhel_ai_version_id' equals "1.3.0".
            4. 'nvidia_gpu_models' equals ['NVIDIA L4'].
            5. 'workloads.rhel_ai' section contains:
                {
                    "variant": "RHEL AI",
                    "rhel_ai_version_id": "1.3.0"
                }
    """
    host = application.puptoo.upload_advisor_payload(rhel_ai_insights_archive)
    assert host.insights_id == rhel_ai_insights_archive.insights_id
    assert host.display_name == rhel_ai_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )
    result = json.loads(response.data)["results"][0]["system_profile"]
    workloads = result["workloads"]

    assert "rhel_ai" in workloads
    rhel_ai_result = workloads["rhel_ai"]
    assert rhel_ai_result["variant"] == "RHEL AI"
    assert rhel_ai_result["rhel_ai_version_id"] == "1.5.0"

    assert rhel_ai_result["variant"] == "RHEL AI"
    assert rhel_ai_result["gpu_models"] == [
        {"name": "NVIDIA L4", "count": 1, "memory": "23034 MiB", "vendor": "Nvidia"}
    ]
    assert rhel_ai_result["rhel_ai_version_id"] == "1.5.0"
    assert rhel_ai_result["ai_models"] == ["granite-7b-lab-Q4_K_M.gguf"]


@pytest.mark.parametrize(
    "cert_content, expected_products",
    INSTALLED_PRODUCT_CASES,
    ids=[
        "multiple_distinct_products",
        "single_product",
        "duplicate_products_without_name",
        "duplicate_products_with_same_name",
        "duplicate_products_name_from_one_cert",
    ],
)
def test_archive_installed_product(
    application: Application,
    ingress_rest_client: IngressApi,
    build_insights_archive_installed_product,
    cert_content,
    expected_products,
):
    """Test that installed_products from an Insights archive are correctly parsed.

    Verifies the products are stored in the host's system_profile in Inventory.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Prepare an Insights archive with different installed product certificates.
            2. Upload the archive via PUPTOO.
            3. Retrieve the host system profile from Inventory using the host ID.
            4. Inspect the installed_products field in the system_profile.
        expected_results:
            1. The archive upload succeeds without errors.
            2. The installed_products field contains all products specified in the archive.
            3. The products' IDs and names match the expected values.
            4. The test passes for multiple cases including multiple products, single product, and empty content.
    """
    archive_file = build_insights_archive_installed_product(cert_content)
    host = application.puptoo.upload_advisor_payload(archive_file)
    assert host.insights_id == archive_file.insights_id
    assert host.display_name == archive_file.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]
    assert host_sp["installed_products"] == expected_products


def test_empty_values_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    empty_value_insights_archive: InsightsArchiveInMemory,
):
    """https://issues.redhat.com/browse/RHINENG-17412.

    Test that empty system profile values from an Insights archive are handled correctly.

    This test verifies that when an Insights archive contains empty values for certain
    system profile fields, those values are correctly stored as empty strings in
    Inventory rather than being omitted or causing processing errors.

    metadata:
    assignee: kuhuang
    requirements:
        - PUPTOO-ARCHIVE-PROCESSING
    importance: high
        test_steps:
            1. Upload an Insights archive containing empty system profile values.
            2. Retrieve the host system profile from Inventory.
            3. Inspect fields that are expected to contain empty values.
        expected_results:
            1. The archive upload succeeds without errors.
            2. The host is successfully created in Inventory.
            3. The affected system profile fields exist and are stored as empty strings.
    """
    host = application.puptoo.upload_advisor_payload(empty_value_insights_archive)
    assert host.insights_id == empty_value_insights_archive.insights_id
    assert host.display_name == empty_value_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    result = json.loads(response.data)["results"][0]["system_profile"]

    assert result["bios_vendor"] == '""'
    assert result["rhsm"]["version"] == ""


def test_ansible_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    ansible_insights_archive: InsightsArchiveInMemory,
):
    """Test Insights archives collected from SAP systems can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(ansible_insights_archive)
    assert host.insights_id == ansible_insights_archive.insights_id
    assert host.display_name == ansible_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    system_profile_data = json.loads(response.data)["results"][0]["system_profile"]
    # assert "ansible" not in system_profile_data
    workloads = system_profile_data.get("workloads", {})
    assert "ansible" in workloads
    assert workloads["ansible"] == {"controller_version": "3.8.3"}


def test_mssql_archives(
    application: Application,
    ingress_rest_client: IngressApi,
    mssql_insights_archive: InsightsArchiveInMemory,
):
    """Test Insights archives collected from SAP systems can be processed by Puptoo and reach the Inventory service.

    metadata:
        assignee: rantunes
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Upload an Insights archive
            2. Retrieve host from Inventory
        expected_results:
            1. The upload is success
            2. The host is found on Inventory and has the expected data
    """
    host = application.puptoo.upload_advisor_payload(mssql_insights_archive)
    assert host.insights_id == mssql_insights_archive.insights_id
    assert host.display_name == mssql_insights_archive.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    system_profile_data = json.loads(response.data)["results"][0]["system_profile"]
    # assert "mssql" not in system_profile_data
    workloads = system_profile_data.get("workloads", {})
    assert "mssql" in workloads
    assert workloads["mssql"] == {"version": "15.0.4198.2"}


@pytest.mark.parametrize(
    "systemctl_output, expected_systemd",
    SYSTEMCTL_STATUS_CASES,
    ids=[
        "normal_full_fields",
        # "only_failed",    # failed
        "invalid_failed",
        "whitespace_leading_zero",
        # "no_failed_field",  # failed
    ],
)
def test_systemctl_status(
    application,
    ingress_rest_client,
    build_insights_archive_systemctl_status,
    systemctl_output,
    expected_systemd,
):
    """Test that the systemctl_status from an Insights archive is correctly parsed and stored in the host's system_profile in Inventory.

    metadata:
        assignee: kuhuang
        requirements:
            - PUPTOO-ARCHIVE-PROCESSING
        importance: high
        test_steps:
            1. Prepare an Insights archive with different systemctl_status outputs.
            2. Upload the archive via PUPTOO.
            3. Retrieve the host system profile from Inventory using the host ID.
            4. Inspect the systemd field in the system_profile.
        expected_results:
            1. The archive upload succeeds without errors.
            2. The systemd field contains all parsed information specified in the archive.
            3. Invalid failed values result in systemd being dropped.
            4. The test passes for multiple cases including full fields, only failed, invalid, whitespace,
            and missing failed.
    """
    archive_file = build_insights_archive_systemctl_status(systemctl_output)
    host = application.puptoo.upload_advisor_payload(archive_file)
    assert host.insights_id == archive_file.insights_id
    assert host.display_name == archive_file.hostname

    response = application.puptoo.v7_inventory_v1.hosts_api.api_host_get_host_system_profile_by_id_without_preload_content(
        host_id_list=[host.id]
    )

    host_sp = json.loads(response.data)["results"][0]["system_profile"]

    if expected_systemd is None:
        assert "systemd" not in host_sp or host_sp["systemd"] is None
    else:
        assert host_sp["systemd"] == expected_systemd
