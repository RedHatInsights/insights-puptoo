import re

from ..base import Modifier

_KERNEL_VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+)")


class TransformOsKernalVersion(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        sp = host.get("system_profile", {})
        kernel = sp.get("os_kernel_version")
        if not kernel:
            return

        match = _KERNEL_VERSION_RE.match(kernel)
        if match:
            version = match.group(1)
            if version != kernel:
                transformed_obj["modified"].append(
                    f"os_kernel_version from '{kernel}' to '{version}'"
                )
                sp["os_kernel_version"] = version
