import requests
import logging
import json

import datetime

from tempfile import NamedTemporaryFile

from utils import config, metrics

from insights.core import dr
from insights import extract, rule, make_metadata, run
from insights.combiners.cloud_provider import CloudProvider
from insights.combiners.redhat_release import RedHatRelease
from insights.combiners.virt_what import VirtWhat
from insights.parsers.dmidecode import DMIDecode
from insights.parsers.cpuinfo import CpuInfo
from insights.parsers.date import DateUTC
from insights.parsers.installed_product_ids import InstalledProductIDs
from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.lsmod import LsMod
from insights.parsers.meminfo import MemInfo
from insights.parsers.uname import Uname
from insights.parsers.systemd.unitfiles import UnitFiles
from insights.parsers.ps import PsAuxcww
from insights.parsers.ip import IpAddr
from insights.parsers.uptime import Uptime
from insights.parsers.yum_repos_d import YumReposD
from insights.parsers.dnf_modules import DnfModules
from insights.specs import Specs
from insights.util.canonical_facts import get_canonical_facts

logger = logging.getLogger(config.APP_NAME)

dr.log.setLevel(config.FACT_EXTRACT_LOGLEVEL)


@metrics.GET_FILE.time()
def get_archive(url):
    archive = requests.get(url)
    return archive.content


@rule(optional=[Specs.hostname, CpuInfo, VirtWhat, MemInfo, IpAddr, DMIDecode,
                RedHatRelease, Uname, LsMod, InstalledRpms, UnitFiles, PsAuxcww,
                DateUTC, Uptime, YumReposD, DnfModules, CloudProvider, Specs.display_name, Specs.version_info,
                InstalledProductIDs, Specs.branch_info, Specs.tags])
def system_profile(hostname, cpu_info, virt_what, meminfo, ip_addr, dmidecode,
                   redhat_release, uname, lsmod, installed_rpms, unit_files, ps_auxcww,
                   date_utc, uptime, yum_repos_d, dnf_modules, cloud_provider, display_name, version_info,
                   product_ids, branch_info, tags):
    """
    This method applies parsers to a host and returns a system profile that can
    be sent to inventory service.

    Note that we strip all keys with the value of "None". Inventory service
    ignores any key with None as the value.
    """
    profile = {"tags": []}
    if uname:
        profile['arch'] = uname.arch

    if dmidecode:
        try:
            profile['bios_release_date'] = dmidecode.bios.get('release_date')
            profile['bios_vendor'] = dmidecode.bios.get('vendor')
            profile['bios_version'] = dmidecode.bios.get('version')
        except AttributeError:
            pass

    if cpu_info:
        profile['cpu_flags'] = cpu_info.flags
        profile['number_of_cpus'] = cpu_info.cpu_count
        profile['number_of_sockets'] = cpu_info.socket_count
        if cpu_info.core_total and cpu_info.socket_count:
            profile['cores_per_socket'] = cpu_info.core_total // cpu_info.socket_count

    if unit_files:
        profile['enabled_services'] = _enabled_services(unit_files)
        profile['installed_services'] = _installed_services(unit_files)

    if virt_what:
        profile['infrastructure_type'] = _get_virt_phys_fact(virt_what)
        profile['infrastructure_vendor'] = virt_what.generic

    if installed_rpms:
        profile['installed_packages'] = sorted([installed_rpms.get_max(p).nevra for p in installed_rpms.packages])

    if lsmod:
        profile['kernel_modules'] = list(lsmod.data.keys())

    if date_utc:
        # re-inject UTC timezone into date_utc in order to obtain isoformat w/ TZ offset
        utc_tz = datetime.timezone(datetime.timedelta(hours=0), name="UTC")
        utcdate = date_utc.datetime.replace(tzinfo=utc_tz)
        profile['captured_date'] = utcdate.isoformat()

    if uptime and date_utc:
        boot_time = date_utc.datetime - uptime.uptime
        profile['last_boot_time'] = boot_time.isoformat()

    if ip_addr:
        network_interfaces = []
        for iface in ip_addr:
            interface = {'ipv4_addresses': iface.addrs(version=4),
                         'ipv6_addresses': iface.addrs(version=6),
                         'mac_address': _safe_fetch_interface_field(iface, 'mac'),
                         'mtu': _safe_fetch_interface_field(iface, 'mtu'),
                         'name': _safe_fetch_interface_field(iface, 'name'),
                         'state': _safe_fetch_interface_field(iface, 'state'),
                         'type': _safe_fetch_interface_field(iface, 'type')}
            network_interfaces.append(_remove_empties(interface))

        profile['network_interfaces'] = network_interfaces

    if uname:
        profile['os_kernel_version'] = uname.version
        profile['os_kernel_release'] = uname.release

    if redhat_release:
        try:
            profile['os_release'] = redhat_release.rhel
        except AttributeError:
            pass

    if ps_auxcww:
        profile['running_processes'] = list(ps_auxcww.running)

    if meminfo:
        profile['system_memory_bytes'] = meminfo.total

    if yum_repos_d:
        repos = []
        for yum_repo_file in yum_repos_d:
            for yum_repo_definition in yum_repo_file:
                baseurl = yum_repo_file[yum_repo_definition].get('baseurl', [])
                repo = {'id': yum_repo_definition,
                        'name': yum_repo_file[yum_repo_definition].get('name'),
                        'base_url': baseurl[0] if len(baseurl) > 0 else None,
                        'enabled': _to_bool(yum_repo_file[yum_repo_definition].get('enabled')),
                        'gpgcheck': _to_bool(yum_repo_file[yum_repo_definition].get('gpgcheck'))}
                repos.append(_remove_empties(repo))
        profile['yum_repos'] = repos

    if dnf_modules:
        modules = []
        for module in dnf_modules:
            for module_name in module.sections():
                modules.append({'name': module_name,
                                'stream': module.get(module_name, 'stream')})
        profile['dnf_modules'] = modules

    if cloud_provider:
        profile['cloud_provider'] = cloud_provider.cloud_provider

    if display_name:
        profile['display_name'] = display_name.content[0]

    if version_info:
        version_info_json = json.loads(version_info.content[0])
        profile['insights_client_version'] = version_info_json['client_version']
        profile['insights_egg_version'] = version_info_json['core_version']

    if branch_info:
        branch_info_json = json.loads(branch_info.content.decode("utf-8"))
        if branch_info_json["remote_branch"] != -1:
            profile["satellite_managed"] = True
            profile["satellite_id"] = branch_info_json["remote_leaf"]
        else:
            profile["satellite_managed"] = False
        if branch_info_json.get("labels"):
            profile["tags"] = profile["tags"] + branch_info_json["labels"]

    if product_ids:
        profile['installed_products'] = [{'id': product_id} for product_id in product_ids.ids]

    if tags:
        tags_json = json.loads(tags.content.decode("utf-8"))
        for item in tags_json:
            item["namespace"] = "insights-client"
        profile["tags"] = profile["tags"] + tags_json

    metadata_response = make_metadata()
    profile_sans_none = _remove_empties(profile)
    metadata_response.update(profile_sans_none)
    return metadata_response


def _to_bool(value):
    """
    small helper method to convert "0/1" and "enabled/disabled" to booleans
    """
    if value in ['0', 'disabled']:
        return False
    if value in ['1', 'enabled']:
        return True
    else:
        return None


def _remove_empties(d):
    """
    small helper method to remove keys with value of None, [] or ''. These are
    not accepted by inventory service.
    """
    return {x: d[x] for x in d if d[x] not in [None, '', []]}


def _get_virt_phys_fact(virt_what):
    if getattr(virt_what, 'is_virtual', False):
        return 'virtual'
    elif getattr(virt_what, 'is_physical', False):
        return 'physical'
    else:
        return None


def _enabled_services(unit_files):
    """
    This method finds enabled services and strips the '.service' suffix
    """
    return [service[:-8] for service in unit_files.services if unit_files.services[service] and '.service' in service]


def _installed_services(unit_files):
    """
    This method finds installed services and strips the '.service' suffix
    """
    return [service[:-8] for service in unit_files.services if '.service' in service]


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
    if 'display_name' in defined_facts and len(defined_facts['display_name']) not in range(2, 200):
        defined_facts.pop('display_name')
    return defined_facts


@metrics.SYSTEM_PROFILE.time()
def get_system_profile(path=None):
    broker = run(system_profile, root=path)
    result = broker[system_profile]
    del result["type"]
    return result


@metrics.EXTRACT.time()
def extraction(msg, extra, remove=True):
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
        logger.exception("Failed to extract facts: %s", e, extra=extra)
        facts["error"] = e
    finally:
        if facts["system_profile"].get("display_name"):
            facts["display_name"] = facts["system_profile"].get("display_name")
        if facts["system_profile"].get("satellite_id"):
            facts["satellite_id"] = facts["system_profile"].get("satellite_id")
        if facts["system_profile"].get("tags"):
            facts["tags"] = facts["system_profile"].pop("tags")
        groomed_facts = _remove_empties(_remove_bad_display_name(facts))
        return groomed_facts
