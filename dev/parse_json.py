#!/usr/bin/python
# Utility for parsing JSON for tests

import json
import os

# Get the file path from OUTPUT_JSON environment variable, default to "output.json"
json_file_path = os.getenv("OUTPUT_JSON", "output.json")

with open(json_file_path, "r") as f:
    data = json.loads(f.read())
    data = data["system"]["metadata"]

with open(json_file_path, "w") as f:
    f.write(json.dumps(data))