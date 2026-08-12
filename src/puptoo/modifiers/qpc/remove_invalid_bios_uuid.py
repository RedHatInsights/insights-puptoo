import re

from ..base import Modifier

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_uuid(val):
    if not isinstance(val, str):
        return False
    return bool(_UUID_RE.match(val))


class RemoveInvalidBiosUUID(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        bios_uuid = host.get("bios_uuid")
        if bios_uuid is not None and not is_valid_uuid(bios_uuid):
            transformed_obj["removed"].append(f"invalid uuid: {bios_uuid}")
            del host["bios_uuid"]
