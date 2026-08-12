import json
import logging
import os
import sys

from insights.parsers.installed_rpms import InstalledRpm

from ..base import Modifier

logger = logging.getLogger(__name__)

KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE = int(
    os.getenv("KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE", 2097152)
)


class TransfromInstalledPackages(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        sp = host.get("system_profile", {})
        installed_packages = sp.get("installed_packages")
        if not installed_packages:
            return

        msg_size = sys.getsizeof(json.dumps(host))
        if msg_size > KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE:
            del sp["installed_packages"]
            transformed_obj["removed"].append("installed_packages")
            return

        try:
            new_packages = []
            for pkg in installed_packages:
                rpm = InstalledRpm.from_package(pkg)
                epoch = rpm.epoch if rpm.epoch is not None else "0"
                new_packages.append(
                    f"{rpm.name}-{epoch}:{rpm.version}-{rpm.release}.{rpm.arch}"
                )
            sp["installed_packages"] = new_packages
            transformed_obj["modified"].append(
                "installed_packages: prepending default epoch of 0 when missing"
            )
        except Exception as e:
            del sp["installed_packages"]
            transformed_obj["removed"].append(
                f"installed_packages: prepending default epoch failure: {e}"
            )
