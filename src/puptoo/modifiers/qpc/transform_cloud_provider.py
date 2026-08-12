from ..base import Modifier


class TransformCloudProvider(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        sp = host.get("system_profile", {})
        if sp.get("cloud_provider") == "google":
            sp["cloud_provider"] = "gcp"
