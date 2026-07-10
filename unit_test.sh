#!/bin/bash
set -euo pipefail

echo "### Installing dependencies with uv ..."
uv sync

echo "### Running unit tests ..."
uv run pytest tests/ --junitxml="${WORKSPACE:-.}/artifacts/junit-unit_tests.xml"
echo ">>> unit test result: SUCCESS"

# Clone system-profile schema repo to /tmp
SCHEMA_DIR=/tmp/insights-host-inventory
rm -rf "$SCHEMA_DIR"
git clone --depth 1 https://github.com/RedHatInsights/insights-host-inventory.git "$SCHEMA_DIR"

echo '---------------------------------'
echo ' Run the profile and schema check'
echo '---------------------------------'
for file in dev/test-archives/*; do
    filename="$(basename "$file").tar.gz"
    tar -zcf "/tmp/$filename" "$file"
    echo "### Running insights-run to populate profile on $file ..."
    uv run insights-run -p src/puptoo -f json "/tmp/$filename" > /tmp/output.json
    uv run insights-run -p src/puptoo "/tmp/$filename"
    echo ">>> Profile result: SUCCESS"
    OUTPUT_JSON="/tmp/output.json" uv run python dev/parse_json.py
    echo "### Checking output against schema ..."
    uv run python "$SCHEMA_DIR/tools/simple-test/tester.py" \
        "$SCHEMA_DIR/swagger/system_profile.spec.yaml" /tmp/output.json
    echo ">>> Schema validation result: SUCCESS"
    rm "/tmp/$filename" /tmp/output.json
done

rm -rf "$SCHEMA_DIR"
