from ..base import Modifier


class TransformIPAddress(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        ip_addresses = host.get("ip_addresses")
        if ip_addresses is None:
            return

        cleaned = [ip.strip() for ip in ip_addresses if ip.strip()]

        seen = set()
        unique = []
        for ip in cleaned:
            if ip not in seen:
                seen.add(ip)
                unique.append(ip)

        if not unique:
            del host["ip_addresses"]
            transformed_obj["removed"].append("empty ip_addresses")
            return

        if unique != ip_addresses:
            host["ip_addresses"] = unique
            transformed_obj["modified"].append(
                "transformed ip_addresses to store unique values"
            )
