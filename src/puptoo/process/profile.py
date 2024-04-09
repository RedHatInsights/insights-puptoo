import datetime
import json
import logging
import os
import re

from insights import make_metadata, rule, run
from insights.combiners.cloud_provider import CloudProvider
from insights.combiners.redhat_release import RedHatRelease
from insights.parsers.redhat_release import RedhatRelease
from insights.combiners.os_release import OSRelease
from insights.parsers.rhsm_releasever import RhsmReleaseVer
from insights.combiners.virt_what import VirtWhat
from insights.combiners.sap import Sap
from insights.combiners.ansible_info import AnsibleInfo
from insights.core import dr
from insights.parsers.aws_instance_id import AWSInstanceIdDoc, AWSPublicIpv4Addresses, AWSPublicHostnames
from insights.parsers.azure_instance import AzureInstancePlan, AzurePublicIpv4Addresses
from insights.parsers.bootc import BootcStatus
from insights.parsers.cpuinfo import CpuInfo
from insights.parsers.date import DateUTC
from insights.parsers.dmidecode import DMIDecode
from insights.parsers.dnf_modules import DnfModules
from insights.parsers.dnf_module import DnfModuleList
from insights.parsers.gcp_license_codes import GCPLicenseCodes
from insights.parsers.gcp_network_interfaces import GCPNetworkInterfaces
from insights.parsers.greenboot_status import GreenbootStatus
from insights.parsers.sap_hdb_version import HDBVersion
from insights.parsers.installed_product_ids import InstalledProductIDs
from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.ip import IpAddr
from insights.parsers.iris import IrisCpf, IrisList
from insights.parsers.lsmod import LsMod
from insights.parsers.lscpu import LsCPU
from insights.parsers.meminfo import MemInfo
from insights.parsers.pmlog_summary import PmLogSummary, PmLogSummaryPcpZeroConf
from insights.parsers.ps import PsAuxcww
from insights.parsers.ros_config import RosConfig
from insights.parsers.rpm_ostree_status import RpmOstreeStatus
from insights.parsers.sestatus import SEStatus
from insights.parsers.systemd.unitfiles import UnitFiles, ListUnits
from insights.parsers.tuned import Tuned
from insights.parsers.uname import Uname
from insights.parsers.uptime import Uptime
from insights.parsers.yum_repos_d import YumReposD
from insights.parsers.branch_info import BranchInfo
from insights.parsers.tags import Tags
from insights.parsers.systemctl_status_all import SystemctlStatusAll
from insights.parsers.eap_json_reports import EAPJSONReports
from insights.specs import Specs
from insights.specs.datasources.pcp import ros_collect as ds_ros_collect

from ..utils import config, metrics, puptoo_logging

logger = logging.getLogger(config.APP_NAME)

dr.log.setLevel(config.FACT_EXTRACT_LOGLEVEL)


MAC_REGEX = '^([A-Fa-f0-9]{2}[:-]){5}[A-Fa-f0-9]{2}$|^([A-Fa-f0-9]{4}[.]){2}[A-Fa-f0-9]{4}$|^[A-Fa-f0-9]{12}$|^([A-Fa-f0-9]{2}[:-]){19}[A-Fa-f0-9]{2}$|^[A-Fa-f0-9]{40}$'


def catch_error(parser, error):
    log_msg = "System Profile failed due to %s encountering an error: %s"
    logger.error(log_msg, parser, error)


# GCP_CONFIRMED_CODES are the available marketplace license codes available
# from the Google Compute Platform. These may need to be updated regularly.
GCP_CONFIRMED_CODES = [
    "601259152637613565",
    "1176308840663243801",
    "1000002",
    "1000006",
    "601259152637613565",
    "8555687517154622919",
    "1270685562947480748",
]


@rule(
    optional=[
        Specs.hostname,
        AnsibleInfo,
        AWSInstanceIdDoc,
        AWSPublicHostnames,
        AWSPublicIpv4Addresses,
        AzureInstancePlan,
        AzurePublicIpv4Addresses,
        BootcStatus,
        CpuInfo,
        VirtWhat,
        MemInfo,
        IpAddr,
        DMIDecode,
        RedhatRelease,
        RedHatRelease,
        OSRelease,
        RhsmReleaseVer,
        Uname,
        LsMod,
        LsCPU,
        Sap,
        SEStatus,
        Tuned,
        GCPLicenseCodes,
        GCPNetworkInterfaces,
        GreenbootStatus,
        HDBVersion,
        InstalledRpms,
        UnitFiles,
        ListUnits,
        PmLogSummary,
        PmLogSummaryPcpZeroConf,
        PsAuxcww,
        DateUTC,
        Uptime,
        YumReposD,
        DnfModules,
        DnfModuleList,
        CloudProvider,
        Specs.display_name,
        Specs.ansible_host,
        Specs.version_info,
        InstalledProductIDs,
        BranchInfo,
        Tags,
        SystemctlStatusAll,
        RpmOstreeStatus,
        RosConfig,
        ds_ros_collect,
        Specs.pcp_raw_data,
        Specs.yum_updates,
        IrisCpf,
        IrisList,
        EAPJSONReports
    ]
)
def system_profile(
    hostname,
    ansible_info,
    aws_instance_id,
    aws_public_hostnames,
    aws_public_ipv4_addresses,
    azure_instance_plan,
    azure_public_ipv4_addresses,
    bootc_status,
    cpu_info,
    virt_what,
    meminfo,
    ip_addr,
    dmidecode,
    redhat_release_parser,
    redhat_release_combiner,
    os_release,
    rhsm_releasever,
    uname,
    lsmod,
    lscpu,
    sap,
    sestatus,
    tuned,
    gcp_license_codes,
    gcp_network_interfaces,
    gb_status,
    hdb_version,
    installed_rpms,
    unit_files,
    list_units,
    pmlog_summary,
    pmlog_summary_pcp_zeroconf,
    ps_auxcww,
    date_utc,
    uptime,
    yum_repos_d,
    dnf_modules,
    dnf_module_list,
    cloud_provider,
    display_name,
    ansible_host,
    version_info,
    product_ids,
    branch_info,
    tags,
    systemctl_status_all,
    rpm_ostree_status,
    ros_config,
    ros_collect,
    pcp_raw_data,
    yum_updates,
    iris_cpfs,
    iris_list,
    eap_json_reports
):
    """
    This method applies parsers to a host and returns a system profile that can
    be sent to inventory service.

    Note that we strip all keys with the value of "None". Inventory service
    ignores any key with None as the value.
    """
    profile = {"tags": {"insights-client": {}}, "is_marketplace": False}

    if uname:
        try:
            profile["arch"] = uname.arch
        except Exception as e:
            catch_error("uname", e)
            raise

    if dmidecode:
        try:
            if dmidecode.bios:
                profile["bios_release_date"] = dmidecode.bios.get("release_date")
                profile["bios_vendor"] = dmidecode.bios.get("vendor")
                profile["bios_version"] = dmidecode.bios.get("version")
        except Exception as e:
            catch_error("dmidecode", e)
            raise

    if ansible_info:
        profile["ansible"] = {}
        try:
            if ansible_info.catalog_worker_version:
                profile["ansible"]["catalog_worker_version"] = ansible_info.catalog_worker_version
            if ansible_info.controller_version:
                profile["ansible"]["controller_version"] = ansible_info.controller_version
            if ansible_info.hub_version:
                profile["ansible"]["hub_version"] = ansible_info.hub_version
        except Exception as e:
            catch_error("ansible_info", e)
            raise

    if aws_instance_id:
        if aws_instance_id.get("marketplaceProductCodes"):
            if len(aws_instance_id["marketplaceProductCodes"]) >= 1:
                profile["is_marketplace"] = True

    if azure_instance_plan:
        if any(
            [
                azure_instance_plan.name,
                azure_instance_plan.product,
                azure_instance_plan.publisher,
            ]
        ):
            if azure_instance_plan.product != 'rhel-byos':
                profile["is_marketplace"] = True

    if gcp_license_codes:
        for i in gcp_license_codes.ids:
            if i in GCP_CONFIRMED_CODES:
                profile["is_marketplace"] = True

    if gb_status:
        # Set the greenboot status
        if gb_status.red:
            profile["greenboot_status"] = "red"
        elif gb_status.green:
            profile["greenboot_status"] = "green"
        profile["greenboot_fallback_detected"] = True if gb_status.fallback else False

    if rpm_ostree_status:
        origin = rpm_ostree_status.query.deployments.origin
        origin_check = [item.value.endswith("edge") for item in origin]
        if origin_check and all(origin_check):
            profile["host_type"] = "edge"
            if os_release and os_release.is_rhel:
                profile["system_update_method"] = "rpm-ostree"

        deployments = _get_deployments(rpm_ostree_status)
        if deployments:
            profile["rpm_ostree_deployments"] = deployments

    if cpu_info:
        try:
            profile["cpu_flags"] = cpu_info.flags
            profile["cpu_model"] = cpu_info.model_name
            profile["number_of_cpus"] = cpu_info.cpu_count
            profile["number_of_sockets"] = cpu_info.socket_count
        except Exception as e:
            catch_error("cpuinfo", e)
            raise
        # sort cpu flags. Do it here in case cpu_flags is a None value
        if profile["cpu_flags"]:
            profile["cpu_flags"] = sorted(cpu_info.flags)

    if lscpu:
        try:
            cores_per_socket = lscpu.info.get("Cores per socket")
            profile["cores_per_socket"] = int(cores_per_socket) if cores_per_socket else None
        except Exception as e:
            catch_error("lscpu", e)
            raise

    if sap:
        profile["sap_system"] = False
        try:
            instances = sap.instances
            if instances:
                profile["sap_system"] = True
                sids = {sap.sid(instance) for instance in instances}
                profile["sap_sids"] = sorted(list(sids))
                inst = instances[0]
                profile["sap_instance_number"] = sap[inst].number
            profile["sap"] = {}
            profile["sap"]["sap_system"] = profile.get("sap_system")
            if profile.get("sap_sids"):
                profile["sap"]["sids"] = profile.get("sap_sids")
            if profile.get("sap_instance_number"):
                profile["sap"]["instance_number"] = profile.get("sap_instance_number")
        except Exception as e:
            catch_error("sap", e)
            raise

    if hdb_version:
        try:
            if type(hdb_version) == list:
                profile["sap_version"] = hdb_version[0].version
            else:
                profile["sap_version"] = hdb_version.version
            if profile.get("sap"):
                profile["sap"]["version"] = profile["sap_version"]
        except Exception as e:
            catch_error("hdb_version", e)
            raise

    if tuned:
        try:
            if "active" in tuned.data:
                profile["tuned_profile"] = tuned.data["active"]
        except Exception as e:
            catch_error("tuned", e)
            raise

    if sestatus:
        try:
            profile["selinux_current_mode"] = sestatus.data["current_mode"].lower()
            profile["selinux_config_file"] = sestatus.data["mode_from_config_file"]
        except Exception as e:
            catch_error("sestatus", e)
            raise

    if unit_files:
        try:
            profile["enabled_services"] = _enabled_services(unit_files)
            profile["installed_services"] = _installed_services(unit_files)
        except Exception as e:
            catch_error("unit_files", e)
            raise

    if virt_what:
        try:
            profile["infrastructure_type"] = _get_virt_phys_fact(virt_what)
            profile["infrastructure_vendor"] = virt_what.generic
        except Exception as e:
            catch_error("virt_what", e)
            raise

    if installed_rpms:
        try:
            # the sorts work on InstalledRpm instances, which will use the RPM
            # ordering algorithm.
            latest = _get_latest_packages(installed_rpms)
            profile["installed_packages"] = [p.nevra for p in _sort_packages(latest)]

            stale = _get_stale_packages(installed_rpms)
            profile["installed_packages_delta"] = [
                p.nevra for p in _sort_packages(stale)
            ]

            gpg_pubkeys = _get_gpg_pubkey_packages(installed_rpms)
            profile["gpg_pubkeys"] = [p.package for p in sorted(gpg_pubkeys)]

            mssql_server = _get_mssql_server_package(latest)
            if mssql_server:
                profile["mssql"] = {"version": mssql_server.version}
        except Exception as e:
            catch_error("installed_packages", e)
            raise

    if lsmod:
        try:
            profile["kernel_modules"] = sorted(list(lsmod.data.keys()))
        except Exception as e:
            catch_error("lsmod", e)
            raise

    if date_utc:
        try:
            # re-inject UTC timezone into date_utc in order to obtain isoformat w/ TZ offset
            utc_tz = datetime.timezone(datetime.timedelta(hours=0), name="UTC")
            utcdate = date_utc.datetime.replace(tzinfo=utc_tz)
            profile["captured_date"] = utcdate.isoformat()
        except Exception as e:
            catch_error("date_utc", e)
            raise

    if uptime and date_utc:
        try:
            boot_time = date_utc.datetime - uptime.uptime
            profile["last_boot_time"] = boot_time.astimezone().isoformat()
        except Exception as e:
            catch_error("uptime", e)
            raise

    if ip_addr:
        try:
            network_interfaces = []
            for iface in ip_addr:
                interface = {
                    "ipv4_addresses": iface.addrs(version=4),
                    "ipv6_addresses": iface.addrs(version=6),
                    "mac_address": _filter_macs(_safe_fetch_interface_field(iface, "mac")),
                    "mtu": _safe_fetch_interface_field(iface, "mtu"),
                    "name": _safe_fetch_interface_field(iface, "name"),
                    "state": _safe_fetch_interface_field(iface, "state"),
                    "type": _safe_fetch_interface_field(iface, "type"),
                }
                network_interfaces.append(_remove_empties(interface))

            profile["network_interfaces"] = sorted(
                network_interfaces, key=lambda k: k["name"]
            )
        except Exception as e:
            catch_error("ip_addr", e)
            raise

    if uname:
        try:
            profile["os_kernel_version"] = uname.version
            profile["os_kernel_release"] = uname.release
        except Exception as e:
            catch_error("uname", e)
            raise

    if (redhat_release_parser or redhat_release_combiner) and os_release:
        try:
            if profile.get("system_update_method") is None:
                profile["system_update_method"] = "yum"
            if os_release.is_rhel and redhat_release_combiner:
                profile["os_release"] = redhat_release_combiner.rhel
                profile["operating_system"] = {
                    "major": redhat_release_combiner.major,
                    "minor": redhat_release_combiner.minor,
                    "name": "RHEL"
                }
                if profile.get("host_type") is None:
                    if redhat_release_combiner.major >= 8:
                        profile["system_update_method"] = "dnf"
            elif "CentOS Linux" in os_release.name and redhat_release_parser:
                minor = 0 if redhat_release_parser.minor is None else redhat_release_parser.minor
                profile["os_release"] = '{0}.{1}'.format(redhat_release_parser.major, minor)
                profile["operating_system"] = {
                    "major": redhat_release_parser.major,
                    "minor": minor,
                    "name": os_release.name
                }

        except Exception as e:
            catch_error("redhat_release", e)
            raise

    # When inventory allows us to delete system facts, do that instead using empty string here
    profile["rhsm"] = {"version": ""}
    if rhsm_releasever:
        try:
            # We can add pre-parsed minor + major values, but the schema specifies just version
            # {"major": rhsm_releasever.major, "minor": rhsm_releasever.minor}
            if rhsm_releasever.set:
                profile["rhsm"] = {"version": rhsm_releasever.set}
        except Exception as e:
            catch_error("rhsm_releasever", e)
            raise

    if ps_auxcww:
        try:
            profile["running_processes"] = sorted(list(ps_auxcww.running))
        except Exception as e:
            catch_error("ps_auxcww", e)
            raise

    if meminfo:
        try:
            profile["system_memory_bytes"] = meminfo.total
        except Exception as e:
            catch_error("meminfo", e)
            raise

    if yum_repos_d:
        try:
            repos = []
            for yum_repo_file in yum_repos_d:
                for yum_repo_definition in yum_repo_file:
                    baseurl = yum_repo_file[yum_repo_definition].get("baseurl", [])
                    repo = {
                        "id": yum_repo_definition,
                        "name": yum_repo_file[yum_repo_definition].get("name"),
                        "base_url": baseurl[0] if len(baseurl) > 0 else None,
                        "mirrorlist": yum_repo_file[yum_repo_definition].get("mirrorlist"),
                        "enabled": _to_bool(
                            yum_repo_file[yum_repo_definition].get("enabled")
                        ),
                        "gpgcheck": _to_bool(
                            yum_repo_file[yum_repo_definition].get("gpgcheck")
                        ),
                    }
                    repos.append(_remove_empties(repo))
            profile["yum_repos"] = sorted(repos, key=lambda k: k["id"])
        except Exception as e:
            catch_error("yum_repos_d", e)
            raise

    if not dnf_module_list and dnf_modules:
        # use dnf_modules if older insights-client (without dnf_module_list) is used
        try:
            modules = []
            for module in dnf_modules:
                for module_name in module.sections():
                    modules.append(
                        {
                            "name": module_name,
                            "stream": module.get(module_name, "stream"),
                        }
                    )
            profile["dnf_modules"] = sorted(modules, key=lambda k: k["name"])
        except Exception as e:
            catch_error("dnf_modules", e)
            raise

    if dnf_module_list:
        try:
            modules = []
            for name, module in dnf_module_list.items():
                for stream in module.streams:
                    if stream.active:
                        modules.append({"name": name, "stream": stream.stream})
            profile["dnf_modules"] = sorted(modules, key=lambda k: k["name"])
        except Exception as e:
            catch_error("dnf_modules", e)
            raise

    if cloud_provider:
        try:
            profile["cloud_provider"] = cloud_provider.cloud_provider
        except Exception as e:
            catch_error("cloud_provider", e)
            raise

    if display_name:
        try:
            profile["display_name"] = display_name.content[0]
        except Exception as e:
            catch_error("display_name", e)
            raise

    if ansible_host:
        try:
            profile["ansible_host"] = ansible_host.content[0]
        except Exception as e:
            catch_error("ansible_host", e)
            raise

    if version_info:
        try:
            version_info_json = json.loads(version_info.content[0])
            profile["insights_client_version"] = version_info_json["client_version"]
            profile["insights_egg_version"] = version_info_json["core_version"]
        except Exception as e:
            catch_error("version_info", e)
            raise

    if branch_info:
        try:
            branch_info_json = branch_info.data
            if branch_info_json["remote_branch"] != -1:
                profile["satellite_managed"] = True
                profile["satellite_id"] = branch_info_json["remote_leaf"]
            else:
                profile["satellite_managed"] = False
            if branch_info_json.get("labels"):
                if type(branch_info_json["labels"]) == list:
                    new_tags = format_tags(branch_info_json["labels"])
                    profile["tags"].update(new_tags)
                else:
                    profile["tags"].update(branch_info_json["labels"])
        except Exception as e:
            catch_error("branch_info", e)
            raise

    if product_ids:
        installed_products = []
        try:
            for product_id in list(product_ids.ids):
                installed_products.append({"id": product_id})
            profile["installed_products"] = sorted(
                installed_products, key=lambda k: k["id"]
            )
        except Exception as e:
            catch_error("product_ids", e)
            raise

    if tags:
        try:
            tags_json = tags.data
            if type(tags_json) == list:
                new_tags = format_tags(tags_json)
                profile["tags"].update(new_tags)
            else:
                # Need to turn the values into a list
                for entry in tags_json.keys():
                    for k, v in tags_json[entry].items():
                        if type(tags_json[entry][k]) != list:
                            tags_json[entry][k] = []
                            tags_json[entry][k].append(v)
                profile["tags"].update(tags_json)
        except Exception as e:
            catch_error("tags", e)
            raise

    if yum_updates:
        try:
            profile["yum_updates"] = json.loads(yum_updates.content[0])
        except Exception as e:
            catch_error("yum_updates", e)
            raise

        # Add general facts to global system profile, as yum_updates is large
        if type(profile["yum_updates"]) == dict:
            profile["releasever"] = profile["yum_updates"].get("releasever")
            profile["basearch"] = profile["yum_updates"].get("basearch")

    if (pmlog_summary_pcp_zeroconf or ros_collect or    # ros new collection
            pmlog_summary or ros_config):               # ros old collection
        profile["is_ros"] = True
        profile["is_pcp_raw_data_collected"] = bool(pcp_raw_data)

    if eap_json_reports:
        profile["is_runtimes"] = True

    if systemctl_status_all:
        profile["systemd"] = {
            "state": systemctl_status_all.state,
            "jobs_queued": int(systemctl_status_all.jobs.split(" ")[0]),
            "failed": int(systemctl_status_all.failed.split(" ")[0])
        }
        if list_units:
            if int(systemctl_status_all.failed.split(" ")[0]) > 0:
                profile["systemd"]["failed_services"] = [svc for svc in list_units.service_names
                    if list_units.is_failed(svc)]

    if aws_public_hostnames:
        profile["public_dns"] = _remove_empty_string(aws_public_hostnames)

    if aws_public_ipv4_addresses:
        profile["public_ipv4_addresses"] = _remove_empty_string(aws_public_ipv4_addresses)

    if azure_public_ipv4_addresses:
        profile["public_ipv4_addresses"] = _remove_empty_string(azure_public_ipv4_addresses)

    if gcp_network_interfaces:
        profile["public_ipv4_addresses"] = _remove_empty_string(gcp_network_interfaces.public_ips)

    if bootc_status:
        try:
            profile["bootc_status"] = {}
            status = bootc_status.get('status', {})
            for bootc_key in ["booted", "staged", "rollback"]:
                bootc_value = status.get(bootc_key)
                if bootc_value:
                    profile["bootc_status"][bootc_key] = {
                        "image": bootc_value.get('image', {}).get('image', {}).get('image', ''),
                        "image_digest": bootc_value.get('image', {}).get('imageDigest', ''),
                    }
                    cached_value = bootc_value.get('cachedUpdate')
                    if cached_value:
                        profile["bootc_status"][bootc_key].update({
                            "cached_image": cached_value.get('image', {}).get('image', ''),
                            "cached_image_digest": cached_value.get('imageDigest', ''),
                        })
        except Exception as e:
            catch_error("bootc_status", e)
            raise

    if iris_cpfs and iris_list:
        try:
            intersystems_profile = {}
            intersystems_profile["is_intersystems"] = True
            intersystems_profile["running_instances"] = []

            # Get all CPF info in format <cpf-file-path: cpf-info>
            cpf_info = {}
            for cpf in iris_cpfs:
                if (cpf.file_path and cpf.has_option('ConfigFile', 'Product') and
                        cpf.has_option('ConfigFile', 'Version')):
                    cpf_info[cpf.file_path] = {
                        "product": cpf.get('ConfigFile', 'Product'),
                        "version": cpf.get('ConfigFile', 'Version'),
                    }
            if cpf_info:
                # Filter for running instance and grab the instance_name
                for instance in iris_list:
                    if instance['status'].startswith('running'):
                        instance_name = instance['instance_name']
                        conf_directory = instance['directory']
                        conf_file = instance['conf file'].split()[0].strip()
                        cpf_file_path = os.path.join(conf_directory, conf_file)
                        if instance_name and cpf_file_path and cpf_file_path in cpf_info:
                            instance_info = _remove_empties({
                                "instance_name": instance['instance_name'],
                                "product": cpf_info[cpf_file_path]["product"],
                                "version": cpf_info[cpf_file_path]["version"],
                            })
                            if instance_info:
                                intersystems_profile["running_instances"].append(instance_info)
            profile["intersystems"] = _remove_empties(intersystems_profile)
        except Exception as e:
            catch_error("intersystems", e)
            raise

    metadata_response = make_metadata()
    profile_sans_none = _remove_empties(profile)
    metadata_response.update(profile_sans_none)
    return metadata_response


def format_tags(tags):
    """
    helper function for converting list tags to nested tags for inventory
    """
    tags_dict = {}
    for entry in tags:
        if entry.get("namespace"):
            namespace = entry.pop("namespace")
        else:
            namespace = "insights-client"
        if tags_dict.get(namespace) is None:
            tags_dict[namespace] = {}
        if tags_dict[namespace].get(entry["key"]) is None:
            tags_dict[namespace][entry["key"]] = []
        if entry["value"] is not None:
            value_str = str(entry["value"])
            tags_dict[namespace][entry["key"]].append(value_str)

    return tags_dict


def _to_bool(value):
    """
    small helper method to convert "0/1" and "enabled/disabled" to booleans
    """
    if value in ["0", "disabled"]:
        return False
    if value in ["1", "enabled"]:
        return True
    else:
        return None


def _remove_empties(d):
    """
    small helper method to remove keys with value of None, [] or ''. These are
    not accepted by inventory service.
    """
    return {x: d[x] for x in d if d[x] not in [None, "", []]}


def _remove_empty_string(arr):
    """
    small helper method to remove empty string from an array.
    """
    return [i for i in arr if i != '']


def _get_deployments(rpm_ostree_status):
    """
    Extract limited data from each deployment in the rpm ostree status.
    """
    deployments = rpm_ostree_status.data.get("deployments", [])
    results = []
    for deployment in deployments:
        dep = {
            "id": deployment.get("id", ""),
            "checksum": deployment.get("checksum", ""),
            "origin": deployment.get("origin", ""),
            "osname": deployment.get("osname", ""),
            "booted": deployment.get("booted", False),
            "pinned": deployment.get("pinned", False),
        }

        if "version" in deployment:
            dep["version"] = deployment.get("version", "")

        results.append(dep)
    return results


def _get_latest_packages(rpms):
    """
    Extract latest non gpg-pubkey packages from the InstalledRpms parser.
    """
    return set(rpms.get_max(p) for p in rpms.packages if p != "gpg-pubkey")


def _get_stale_packages(rpms):
    """
    Get all non gpg-pubkey packages that aren't the latest versions from the
    InstalledRpms parser.
    """
    result = set()
    for name, packages in rpms.packages.items():
        if name != "gpg-pubkey" and len(packages) > 1:
            result |= set(packages) - set([max(packages)])
    return result


def _get_gpg_pubkey_packages(rpms):
    """
    Get the gpg-pubkey packages from the InstalledRpms parser.
    """
    return rpms.packages.get("gpg-pubkey", [])


def _get_mssql_server_package(packages):
    """
    Get the mssql-server package from the latest packages from the
    InstalledRpms parser.
    """
    result = None
    for package in packages:
        if package.name == "mssql-server":
            result = package
            break
    return result


def _sort_packages(packages):
    return sorted(packages, key=lambda p: (p.name, p))


def _get_virt_phys_fact(virt_what):
    if getattr(virt_what, "is_virtual", False):
        return "virtual"
    elif getattr(virt_what, "is_physical", False):
        return "physical"
    else:
        return None


def _enabled_services(unit_files):
    """
    This method finds enabled services and strips the '.service' suffix
    """
    return [
        service[:-8].strip("@")
        for service in unit_files.services
        if unit_files.services[service] and ".service" in service
    ]


def _installed_services(unit_files):
    """
    This method finds installed services and strips the '.service' suffix
    """
    return [service[:-8] for service in unit_files.services if ".service" in service]


# from insights-core get_canonical_facts util
def _safe_parse(ds):
    try:
        return ds.content[0]

    except Exception:
        return None


def _safe_fetch_interface_field(interface, field_name):
    try:
        return interface[field_name]
    except KeyError:
        return None


def _filter_macs(mac):
    if mac:
        m = re.compile(MAC_REGEX)
        if m.match(mac):
            return mac
        else:
            return None
    else:
        return None


def _remove_bad_names(facts, keys):
    defined_facts = facts
    for key in keys:
        if key in defined_facts and len(defined_facts[key]) not in range(2, 200):
            defined_facts.pop(key)
    return defined_facts


def run_profile():

    args = None

    import argparse
    import os
    import sys

    puptoo_logging.initialize_logging()
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("archive", nargs="?", help="Archive to analyze.")
    args = p.parse_args()

    root = args.archive
    if root:
        root = os.path.realpath(root)
    try:
        broker = run(system_profile, root=root)
        result = broker[system_profile]
        print(result)
    except Exception as e:
        print("System_profile failure: %s" % e)
        sys.exit(1)


@metrics.SYSTEM_PROFILE.time()
def get_system_profile(path=None):
    broker = run(system_profile, root=path)
    result = broker[system_profile]
    del result["type"]
    return result


def postprocess(facts):
    m = re.compile(MAC_REGEX)
    if facts["system_profile"].get("display_name"):
        facts["display_name"] = facts["system_profile"].get("display_name")
    if facts["system_profile"].get("ansible_host"):
        facts["ansible_host"] = facts["system_profile"].get("ansible_host")
    if facts["system_profile"].get("satellite_id"):
        facts["satellite_id"] = facts["system_profile"].get("satellite_id")
    if facts["system_profile"].get("tags"):
        facts["tags"] = facts["system_profile"].pop("tags")
    if facts.get("mac_addresses"):
        facts["mac_addresses"] = [mac for mac in facts["mac_addresses"] if m.match(mac)]
    groomed_facts = _remove_empties(
        _remove_bad_names(facts, ["display_name", "ansible_host"])
    )
    return groomed_facts
