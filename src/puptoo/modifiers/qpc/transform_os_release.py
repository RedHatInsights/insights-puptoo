import re

from ..base import Modifier

_VERSION_RE = re.compile(r"(\d+)(?:\.(\d+))?")
_JUST_VERSION_RE = re.compile(r"\d+(?:\.\d+)*$")

_OS_NAME_MAP = {
    "red hat enterprise linux": "RHEL",
    "centos": "CentOS",
}


class TransformOsRelease(Modifier):
    def match_regex_and_find_os_details(self, os_release):
        match = _VERSION_RE.search(os_release)
        if not match:
            return None

        result = {"major": match.group(1)}
        result["minor"] = match.group(2) if match.group(2) else "0"

        lower = os_release.lower()
        for pattern, name in _OS_NAME_MAP.items():
            if pattern in lower:
                result["name"] = name
                break

        return result

    def run(self, host, transformed_obj, **kwargs):
        sp = host.get("system_profile", {})
        os_release = sp.get("os_release")
        if os_release is None:
            return

        stripped = os_release.strip()
        without_parens = re.sub(r"\(.*?\)", "", stripped).strip()

        if not without_parens:
            del sp["os_release"]
            transformed_obj["removed"].append("empty os_release")
            return

        if _JUST_VERSION_RE.fullmatch(without_parens):
            transformed_obj["missing_data"].append(
                f"operating system info for os release '{os_release}'"
            )
            return

        os_details = self.match_regex_and_find_os_details(os_release)

        if os_details is None:
            del sp["os_release"]
            transformed_obj["removed"].append("empty os_release")
            return

        version = os_details["major"]
        if os_details.get("minor") and os_details["minor"] != "0":
            version = f"{os_details['major']}.{os_details['minor']}"

        original = os_release
        sp["os_release"] = version
        transformed_obj["modified"].append(
            f"os_release from '{original}' to '{version}'"
        )

        if "name" in os_details:
            sp["operating_system"] = {
                "name": os_details["name"],
                "major": os_details["major"],
                "minor": os_details.get("minor", "0"),
            }
