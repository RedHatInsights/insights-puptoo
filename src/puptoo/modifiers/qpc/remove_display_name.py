from ..base import Modifier


class RemoveDisplayName(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        if "display_name" in host:
            del host["display_name"]
            transformed_obj["removed"].append("display_name")
