import json
import os
from base64 import b64decode
from datetime import datetime, timedelta

from ..base import Modifier

SATELLITE_HOST_TTL = int(os.getenv("SATELLITE_HOST_TTL", "26280"))


class AddHostFacts(Modifier):
    def get_stale_time(self, request_obj):
        source = request_obj.get("source", "")
        if source == "satellite":
            ttl = SATELLITE_HOST_TTL
        else:
            ttl = 26
        stale_time = datetime.utcnow() + timedelta(hours=ttl)
        return stale_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def run(self, host, transformed_obj, **kwargs):
        request_obj = kwargs.get("request_obj", {})

        host["reporter"] = request_obj.get("source", "yupana")
        host["org_id"] = request_obj.get("org_id")
        host["stale_timestamp"] = self.get_stale_time(request_obj)

        b64_identity = request_obj.get("b64_identity")
        if b64_identity:
            identity = json.loads(b64decode(b64_identity).decode("utf-8"))
            system = identity.get("identity", {}).get("system", {})
            owner_id = system.get("cn")
            if owner_id and host.get("system_profile") is not None:
                host["system_profile"]["owner_id"] = owner_id

        yupana_host_id = host.get("yupana_host_id")
        if yupana_host_id:
            host["subscription_manager_id"] = yupana_host_id

        facts = {
            "namespace": "yupana",
            "facts": {
                "yupana_host_id": host.get("yupana_host_id"),
                "report_platform_id": request_obj.get("report_platform_id"),
                "report_slice_id": host.get("report_slice_id"),
                "source": request_obj.get("source"),
                "account": request_obj.get("account"),
            },
        }
        host["facts"] = [facts]
        transformed_obj["modified"].append("facts")

        host.pop("yupana_host_id", None)
        host.pop("report_slice_id", None)
