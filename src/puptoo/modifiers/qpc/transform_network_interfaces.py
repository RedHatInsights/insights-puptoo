from ..base import Modifier


def _remove_mac_addrs_for_omitted_nics(host, mac_addresses_to_omit, transformed_obj):
    mac_addresses = host.get("mac_addresses")
    if mac_addresses and len(mac_addresses_to_omit) > 0:
        host["mac_addresses"] = list(set(mac_addresses) - set(mac_addresses_to_omit))
        if not host["mac_addresses"]:
            del host["mac_addresses"]
        transformed_obj["removed"].append("omit mac_addresses for omitted nics")
    return [host, transformed_obj]


class TransformNetworkInterfaces(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        sp = host.get("system_profile", {})
        nics = sp.get("network_interfaces")
        if not nics:
            return

        mac_addresses_to_omit = []
        filtered_nics = []

        for nic in nics:
            name = nic.get("name")

            if not name:
                continue

            if name.startswith("cali"):
                mac_addr = nic.get("mac_address")
                if mac_addr:
                    mac_addresses_to_omit.append(mac_addr)
                continue

            mtu = nic.get("mtu")
            if mtu is not None:
                try:
                    nic["mtu"] = int(mtu)
                except (ValueError, TypeError):
                    pass

            ipv4 = nic.get("ipv4_addresses")
            if ipv4 is not None:
                original_ipv4 = list(ipv4)
                cleaned = []
                for addr in ipv4:
                    stripped = addr.split("/")[0] if addr else ""
                    if stripped:
                        cleaned.append(stripped)
                nic["ipv4_addresses"] = cleaned
                if cleaned != original_ipv4:
                    if "ipv4_addresses" not in transformed_obj["modified"]:
                        transformed_obj["modified"].append("ipv4_addresses")

            ipv6 = nic.get("ipv6_addresses")
            if ipv6 is not None:
                nic["ipv6_addresses"] = [addr for addr in ipv6 if addr]

            filtered_nics.append(nic)

        sp["network_interfaces"] = filtered_nics

        _remove_mac_addrs_for_omitted_nics(host, mac_addresses_to_omit, transformed_obj)
