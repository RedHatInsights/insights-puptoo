from .qpc.add_host_facts import AddHostFacts
from .qpc.remove_display_name import RemoveDisplayName
from .qpc.remove_invalid_bios_uuid import RemoveInvalidBiosUUID
from .qpc.transform_cloud_provider import TransformCloudProvider
from .qpc.transform_installed_packages import TransfromInstalledPackages
from .qpc.transform_ip_addresses import TransformIPAddress
from .qpc.transform_mac_addresses import TransformMacAddresses
from .qpc.transform_network_interfaces import TransformNetworkInterfaces
from .qpc.transform_os_kernel_version import TransformOsKernalVersion
from .qpc.transform_os_release import TransformOsRelease
from .qpc.transform_tags import TransformTags

QPC_MODIFIER_ORDER = [
    RemoveDisplayName,
    RemoveInvalidBiosUUID,
    TransformCloudProvider,
    TransformIPAddress,
    TransformMacAddresses,
    TransformNetworkInterfaces,
    TransformOsKernalVersion,
    TransformOsRelease,
    TransformTags,
    TransfromInstalledPackages,
    AddHostFacts,
]

_MODIFIERS = []
_registered = False


def register_modifiers():
    global _MODIFIERS, _registered
    if _registered:
        return
    _MODIFIERS = [cls() for cls in QPC_MODIFIER_ORDER]
    _registered = True


def get_modifiers():
    if not _registered:
        register_modifiers()
    return _MODIFIERS
