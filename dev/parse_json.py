#!/usr/bin/python
# Utility for parsing JSON for tests

import json
import os

# Get the file path from OUTPUT_JSON environment variable, default to "output.json"
json_file_path = os.getenv("OUTPUT_JSON", "output.json")


def _strip_json_nulls(value):
    """
    Drop JSON nulls before inventory schema validation.

    Puptoo payloads are RFC 7396 merge patches after RHINENG-29896: null
    deletes a stored field. The system profile swagger describes the stored
    document, which must not contain null.
    """
    if isinstance(value, dict):
        return {k: _strip_json_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_json_nulls(item) for item in value if item is not None]
    return value


with open(json_file_path, "r") as f:
    data = json.loads(f.read())
    data = data["system"]["metadata"]

with open(json_file_path, "w") as f:
    f.write(json.dumps(_strip_json_nulls(data)))
