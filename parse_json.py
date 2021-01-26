#!/usr/bin/python
# Utility for parsing JSON for tests

import json


with open("output.json", "r") as f:
    data = json.loads(f.read())
    data = data["system"]["metadata"]

with open("output.json", "w") as f:
    f.write(json.dumps(data))
