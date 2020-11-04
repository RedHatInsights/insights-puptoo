import datetime
import json
import logging
from tempfile import NamedTemporaryFile

import requests
from insights import extract, make_metadata, rule, run
from insights.combiners.cloud_provider import CloudProvider
from insights.combiners.redhat_release import RedHatRelease
from insights.combiners.virt_what import VirtWhat
from insights.combiners.sap import Sap
from insights.core import dr
from insights.parsers.cpuinfo import CpuInfo
from insights.parsers.date import DateUTC
from insights.parsers.dmidecode import DMIDecode
from insights.parsers.dnf_modules import DnfModules
from insights.parsers.installed_product_ids import InstalledProductIDs
from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.ip import IpAddr
from insights.parsers.lsmod import LsMod
from insights.parsers.lscpu import LsCPU
from insights.parsers.meminfo import MemInfo
from insights.parsers.ps import PsAuxcww
from insights.parsers.sestatus import SEStatus
from insights.parsers.systemd.unitfiles import UnitFiles
from insights.parsers.tuned import Tuned
from insights.parsers.uname import Uname
from insights.parsers.uptime import Uptime
from insights.parsers.yum_repos_d import YumReposD
from insights.specs import Specs
from insights.util.canonical_facts import get_canonical_facts

from .utils import config, metrics

logger = logging.getLogger(config.APP_NAME)

dr.log.setLevel(config.FACT_EXTRACT_LOGLEVEL)


def log_failure(component, error):
    fail_log = "Failed to process %s in system_profile: %s"
    logger.error(fail_log, component, error)


@metrics.GET_FILE.time()
def get_archive(url):
    archive = requests.get(url)
    return archive.content


@rule(
    optional=[
        Specs.hostname,
        CpuInfo,
        VirtWhat,
        MemInfo,
        IpAddr,
        DMIDecode,
        RedHatRelease,
        Uname,
        LsMod,
        LsCPU,
        Sap,
        SEStatus,
        Tuned,
        InstalledRpms,
        UnitFiles,
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
    cpu_info,
    virt_what,
    meminfo,
    ip_addr,
    dmidecode,
    redhat_release,
    uname,
    lsmod,
    lscpu,
    sap,
    sestatus,
    tuned,
    installed_rpms,
    unit_files,
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
            log_failure("uname", e)
            pass

    if dmidecode:
        try:
            profile["bios_release_date"] = dmidecode.bios.get("release_date")
            profile["bios_vendor"] = dmidecode.bios.get("vendor")
            profile["bios_version"] = dmidecode.bios.get("version")
        except Exception as e:
            log_failure("dmidecode", e)
            pass

    if cpu_info:
        try:
            profile["cpu_flags"] = cpu_info.flags
            profile["number_of_cpus"] = cpu_info.cpu_count
            profile["number_of_sockets"] = cpu_info.socket_count
        except Exception as e:
            log_failure("cpu_info", e)
            pass

    if lscpu:
        try:
            profile["cores_per_socket"] = lscpu.info['Cores per socket']
        except Exception as e:
            log_failure("lscpu", e)
            pass

    if sap:
        try:
            profile["sap_system"] = True
            sids = {sap.sid(instance) for instance in sap.local_instances}
            profile["sap_sids"] = sorted(list(sids))
            if sap.local_instances:
                inst = sap.local_instances[0]
                if sap[inst].number not in ["98", "99"]:
                    profile["sap_instance_number"] = sap[inst].number
        except Exception as e:
            log_failure("sap", e)
            pass

    if tuned:
        try:
            profile["tuned_profile"] = tuned.data['active']
        except Exception as e:
            log_failure("tuned", e)
            pass

    if sestatus:
        try:
            profile["selinux_current_mode"] = sestatus.data['current_mode'].lower()
            profile["selinux_config_file"] = sestatus.data['mode_from_config_file']
        except Exception as e:
            log_failure("sestatus", e)
            pass

    if unit_files:
        try:
            profile["enabled_services"] = _enabled_services(unit_files)
            profile["installed_services"] = _installed_services(unit_files)
        except Exception as e:
            log_failure("unit_files", e)
            pass

    if virt_what:
        try:
            profile["infrastructure_type"] = _get_virt_phys_fact(virt_what)
            profile["infrastructure_vendor"] = virt_what.generic
        except Exception as e:
            log_failure("virt_what", e)
            pass

    if installed_rpms:
        try:
            profile["installed_packages"] = sorted(
                [installed_rpms.get_max(p).nevra for p in installed_rpms.packages]
            )
        except Exception as e:
            log_failure("installed_rpms", e)
            pass

    if lsmod:
        try:
            profile["kernel_modules"] = list(lsmod.data.keys())
        except Exception as e:
            log_failure("lsmod", e)
            pass

    if date_utc:
        try:
            # re-inject UTC timezone into date_utc in order to obtain isoformat w/ TZ offset
            utc_tz = datetime.timezone(datetime.timedelta(hours=0), name="UTC")
            utcdate = date_utc.datetime.replace(tzinfo=utc_tz)
            profile["captured_date"] = utcdate.isoformat()
        except Exception as e:
            log_failure("date_utc", e)
            pass

    if uptime and date_utc:
        try:
            boot_time = date_utc.datetime - uptime.uptime
            profile["last_boot_time"] = boot_time.isoformat()
        except Exception as e:
            log_failure("uptime and date_utc", e)
            pass

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

            profile["network_interfaces"] = network_interfaces
        except Exception as e:
            log_failure("ip_addr", e)

    if uname:
        try:
            profile["os_kernel_version"] = uname.version
            profile["os_kernel_release"] = uname.release
        except Exception as e:
            log_failure("uname", e)
            pass

    if redhat_release:
        try:
            profile["os_release"] = redhat_release.rhel
        except Exception as e:
            log_failure("redhat_release", e)
            pass

    if ps_auxcww:
        try:
            profile["running_processes"] = list(ps_auxcww.running)
        except Exception as e:
            log_failure("ps_auxcww", e)
            pass

    if meminfo:
        try:
            profile["system_memory_bytes"] = meminfo.total
        except Exception as e:
            log_failure("meminfo", e)
            pass

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
            profile["yum_repos"] = repos
        except Exception as e:
            log_failure("yum_repos_d", e)
            pass

    if dnf_modules:
        try:
            modules = []
            for module in dnf_modules:
                for module_name in module.sections():
                    modules.append(
                        {"name": module_name, "stream": module.get(module_name, "stream")}
                    )
            profile["dnf_modules"] = modules
        except Exception as e:
            log_failure("dnf_modules", e)
            pass

    if cloud_provider:
        try:
            profile["cloud_provider"] = cloud_provider.cloud_provider
        except Exception as e:
            log_failure("cloud_provider", e)
            pass

    if display_name:
        try:
            profile["display_name"] = display_name.content[0]
        except Exception as e:
            log_failure("display_name", e)
            pass

    if version_info:
        try:
            version_info_json = json.loads(version_info.content[0])
            profile["insights_client_version"] = version_info_json["client_version"]
            profile["insights_egg_version"] = version_info_json["core_version"]
        except Exception as e:
            log_failure("version_info", e)
            pass

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
            log_failure("branch_info", e)
            pass

    if product_ids:
        try:
            profile["installed_products"] = [
                {"id": product_id} for product_id in product_ids.ids
            ]
        except Exception as e:
            log_failure("product_ids", e)
            pass

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
            log_failure("tags", e)
            pass

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


def _remove_empties(d):
    """
    small helper method to remove keys with value of None, [] or ''. These are
    not accepted by inventory service.
    """
    return {x: d[x] for x in d if d[x] not in [None, "", []]}


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
        service[:-8].strip('@')
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


@metrics.SYSTEM_PROFILE.time()
def get_system_profile(path=None):
    broker = run(system_profile, root=path)
    result = broker[system_profile]
    del result["type"]
    return result


@metrics.EXTRACT.time()
def extraction(msg, extra, remove=True):
    metrics.extraction_count.inc()
    facts = {"system_profile": {}}
    try:
        with NamedTemporaryFile(delete=remove) as tf:
            tf.write(get_archive(msg["url"]))
            tf.flush()
            logger.debug("extracting facts from %s", tf.name, extra=extra)
            with extract(tf.name) as ex:
                facts = get_canonical_facts(path=ex.tmp_dir)
                facts["system_profile"] = get_system_profile(path=ex.tmp_dir)
    except Exception as e:
        logger.exception("Failed to extract facts: %s", str(e), extra=extra)
        facts["error"] = str(e)
    finally:
        if facts["system_profile"].get("display_name"):
            facts["display_name"] = facts["system_profile"].get("display_name")
        if facts["system_profile"].get("satellite_id"):
            facts["satellite_id"] = facts["system_profile"].get("satellite_id")
        if facts["system_profile"].get("tags"):
            facts["tags"] = facts["system_profile"].pop("tags")
        groomed_facts = _remove_empties(_remove_bad_display_name(facts))
        metrics.msg_processed.inc()
        metrics.extract_success.inc()
        return groomed_facts
