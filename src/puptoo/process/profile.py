import datetime
import json
import logging

from insights import make_metadata, rule, run
from insights.combiners.cloud_provider import CloudProvider
from insights.combiners.redhat_release import RedHatRelease
from insights.parsers.rhsm_releasever import RhsmReleaseVer
from insights.combiners.virt_what import VirtWhat
from insights.combiners.sap import Sap
from insights.core import dr
from insights.parsers.aws_instance_id import AWSInstanceIdDoc
from insights.parsers.cpuinfo import CpuInfo
from insights.parsers.date import DateUTC
from insights.parsers.dmidecode import DMIDecode
from insights.parsers.dnf_modules import DnfModules
from insights.parsers.sap_hdb_version import HDBVersion
from insights.parsers.installed_product_ids import InstalledProductIDs
from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.ip import IpAddr
from insights.parsers.lsmod import LsMod
from insights.parsers.lscpu import LsCPU
from insights.parsers.meminfo import MemInfo
from insights.parsers.pmlog_summary import PmLogSummary
from insights.parsers.ps import PsAuxcww
from insights.parsers.sestatus import SEStatus
from insights.parsers.systemd.unitfiles import UnitFiles
from insights.parsers.tuned import Tuned
from insights.parsers.uname import Uname
from insights.parsers.uptime import Uptime
from insights.parsers.yum_repos_d import YumReposD
from insights.specs import Specs

from ..utils import config, metrics, puptoo_logging

logger = logging.getLogger(config.APP_NAME)

dr.log.setLevel(config.FACT_EXTRACT_LOGLEVEL)


def catch_error(parser, error):
    log_msg = "System Profile failed due to %s encountering an error: %s"
    logger.error(log_msg, parser, error)


@rule(
    optional=[
        Specs.hostname,
        AWSInstanceIdDoc,
        CpuInfo,
        VirtWhat,
        MemInfo,
        IpAddr,
        DMIDecode,
        RedHatRelease,
        RhsmReleaseVer,
        Uname,
        LsMod,
        LsCPU,
        Sap,
        SEStatus,
        Tuned,
        HDBVersion,
        InstalledRpms,
        UnitFiles,
        PmLogSummary,
        PsAuxcww,
        DateUTC,
        Uptime,
        YumReposD,
        DnfModules,
        CloudProvider,
        Specs.display_name,
        Specs.version_info,
        InstalledProductIDs,
        Specs.branch_info,
        Specs.tags,
    ]
)
def system_profile(
    hostname,
    aws_instance_id,
    cpu_info,
    virt_what,
    meminfo,
    ip_addr,
    dmidecode,
    redhat_release,
    rhsm_releasever,
    uname,
    lsmod,
    lscpu,
    sap,
    sestatus,
    tuned,
    hdb_version,
    installed_rpms,
    unit_files,
    pmlog_summary,
    ps_auxcww,
    date_utc,
    uptime,
    yum_repos_d,
    dnf_modules,
    cloud_provider,
    display_name,
    version_info,
    product_ids,
    branch_info,
    tags,
):
    """
    This method applies parsers to a host and returns a system profile that can
    be sent to inventory service.

    Note that we strip all keys with the value of "None". Inventory service
    ignores any key with None as the value.
    """
    profile = {"tags": {}}

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

    if aws_instance_id:
        if aws_instance_id.get("marketplaceProductCodes"):
            if len(aws_instance_id["marketplaceProductCodes"]) >= 1:
                profile["is_marketplace"] = True

    if cpu_info:
        try:
            profile["cpu_flags"] = cpu_info.flags
            profile["cpu_model"] = cpu_info.model_name
            profile["number_of_cpus"] = cpu_info.cpu_count
            profile["number_of_sockets"] = cpu_info.socket_count
        except Exception as e:
            catch_error("cpuinfo", e)
            raise

    if lscpu:
        try:
            profile["cores_per_socket"] = int(lscpu.info.get("Cores per socket"))
        except Exception as e:
            catch_error("lscpu", e)
            raise

    if sap:
        try:
            profile["sap_system"] = True
            sids = {sap.sid(instance) for instance in sap.local_instances}
            profile["sap_sids"] = sorted(list(sids))
            if sap.local_instances:
                inst = sap.local_instances[0]
                profile["sap_instance_number"] = sap[inst].number
        except Exception as e:
            catch_error("sap", e)
            raise

    if hdb_version:
        try:
            profile["sap_version"] = hdb_version.version
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
        valid_modes = ["permissive", "enforcing", "disabled"]
        try:
            profile["selinux_current_mode"] = sestatus.data["current_mode"].lower()
            current_mode = sestatus.data["mode_from_config_file"]
            if current_mode in valid_modes:
                profile["selinux_config_file"] = current_mode
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
            installed_packages = {
                installed_rpms.get_max(p).nevra for p in installed_rpms.packages
            }
            profile["installed_packages"] = sorted(list(installed_packages))
            all_installed_packages = []
            for p in installed_rpms.packages:
                package_list = installed_rpms.packages[p]
                for each_package in package_list:
                    all_installed_packages.append(each_package.nevra)
            all_installed_packages_set = set(all_installed_packages)
            profile["installed_packages_delta"] = sorted(
                list(all_installed_packages_set - installed_packages)
            )
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
            profile["last_boot_time"] = boot_time.isoformat()
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
                    "mac_address": _safe_fetch_interface_field(iface, "mac"),
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

    if redhat_release:
        try:
            profile["os_release"] = redhat_release.rhel
            profile["operating_system"] = {
                "major": redhat_release.major,
                "minor": redhat_release.minor,
                "name": "RHEL",
            }
        except Exception as e:
            catch_error("redhat_release", e)
            raise

    # By default, always provide None value
    profile["rhsm"] = None
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
                        "enabled": _to_bool(
                            yum_repo_file[yum_repo_definition].get("enabled")
                        ),
                        "gpgcheck": _to_bool(
                            yum_repo_file[yum_repo_definition].get("gpgcheck")
                        ),
                    }
                    repos.append(_remove_empties(repo))
            profile["yum_repos"] = sorted(repos, key=lambda k: k["name"])
        except Exception as e:
            catch_error("yum_repos_d", e)
            raise

    if dnf_modules:
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
            branch_info_json = json.loads(branch_info.content.decode("utf-8"))
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
            tags_json = json.loads(tags.content.decode("utf-8"))
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

    if pmlog_summary:
        profile["is_ros"] = True

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
        if tags_dict[namespace].get(entry["key"]):
            tags_dict[namespace][entry["key"]].append(entry["value"])
        else:
            tags_dict[namespace][entry["key"]] = []
            tags_dict[namespace][entry["key"]].append(entry["value"])

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


def _remove_empties(d, preserve_keys=[]):
    """
    small helper method to remove keys with value of None, [] or ''. These are
    not accepted by inventory service.
    """
    return {x: d[x] for x in d if d[x] not in [None, "", []] or x in preserve_keys}


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


def _remove_bad_display_name(facts):
    defined_facts = facts
    if "display_name" in defined_facts and len(
        defined_facts["display_name"]
    ) not in range(2, 200):
        defined_facts.pop("display_name")
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
    if facts["system_profile"].get("display_name"):
        facts["display_name"] = facts["system_profile"].get("display_name")
    if facts["system_profile"].get("satellite_id"):
        facts["satellite_id"] = facts["system_profile"].get("satellite_id")
    if facts["system_profile"].get("tags"):
        facts["tags"] = facts["system_profile"].pop("tags")
    # Preserve the rhsm system fact (None value means disabled version lock, should not be filtered out)
    groomed_facts = _remove_empties(_remove_bad_display_name(facts), ["rhsm"])
    return groomed_facts
