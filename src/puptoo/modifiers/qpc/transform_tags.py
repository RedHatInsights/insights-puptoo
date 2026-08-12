from ..base import Modifier

_MAX_TAG_VALUE_LENGTH = 250


class TransformTags(Modifier):
    def run(self, host, transformed_obj, **kwargs):
        tags = host.get("tags")
        if not tags:
            return

        modified = False
        for tag in tags:
            value = tag.get("value")
            if value is None:
                continue

            if isinstance(value, bool):
                tag["value"] = str(value).lower()
                modified = True
            elif not isinstance(value, str):
                tag["value"] = str(value)
                modified = True
            elif len(value) > _MAX_TAG_VALUE_LENGTH:
                tag["value"] = "Original value exceeds 250 characters."
                modified = True

        if modified:
            transformed_obj["modified"].append("tags")
