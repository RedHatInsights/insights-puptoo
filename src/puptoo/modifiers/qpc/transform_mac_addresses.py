from ..base import Modifier


class TransformMacAddresses(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        mac_addresses = host.get("mac_addresses")
        if mac_addresses is None:
            return

        if not mac_addresses:
            del host["mac_addresses"]
            transformed_obj["removed"].append("empty mac_addresses")
            return

        host["mac_addresses"] = list(set(mac_addresses))
        transformed_obj["modified"].append(
            "transformed mac_addresses to store unique values"
        )
