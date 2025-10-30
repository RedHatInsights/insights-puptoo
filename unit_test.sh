#!/bin/bash

# check python version
python3.11 --version

python3.11 -m venv /tmp/.unit_test_venv
source /tmp/.unit_test_venv/bin/activate
pip install --upgrade pip
pip install .
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "### Running unit test ..."
INSIGHTS_FILTERS_ENABLED=false INVENTORY_TOPIC=platform.inventory.host-ingress-p1 ACG_CONFIG=dev/cdappconfig.json pytest tests/ --junitxml=$WORKSPACE/artifacts/junit-unit_tests.xml

if [ $? != 0 ]; then
   echo ">>> unit test result: FAILURE"
   exit 1
fi
echo ">>> unit test result: SUCCESS"

# Clone system-profile schema repo to /tmp
git clone https://github.com/RedHatInsights/insights-host-inventory.git /tmp/insights-host-inventory

echo '---------------------------------'
echo ' Run the profile and schema check'
echo '---------------------------------'
for file in dev/test-archives/*; do
    filename="$(basename "$file").tar.gz"
    # Create tar archive in /tmp
    tar -zcf /tmp/$filename "$file"
    # Run insights-run and output to /tmp/output.json
    echo "### Running insights-run to populate profile on $file ..."
    insights-run -p src/puptoo -f json /tmp/$filename > /tmp/output.json
    insights-run -p src/puptoo /tmp/$filename # Print results in test console
    if [ $? != 0 ]; then
        echo ">>> Profile result: FAILURE"
        exit 1
    fi
    echo ">>> Profile result: SUCCESS"
    OUTPUT_JSON="/tmp/output.json" python3.11 dev/parse_json.py
    # Run schema tester with files in /tmp
    echo "### Checking output against schema insights-host-inventory/swagger/system_profile.spec.yaml ..."
    python3.11 /tmp/insights-host-inventory/tools/simple-test/tester.py /tmp/insights-host-inventory/swagger/system_profile.spec.yaml /tmp/output.json
    if [ $? != 0 ]; then
        echo ">>> Schema validation result: FAILURE"
        exit 1
    fi
    echo ">>> Schema validation result: SUCCESS"
    # Clean up files
    rm /tmp/$filename
    rm /tmp/output.json
done

# Clean up schema repo directory
rm -rf /tmp/insights-host-inventory

# Deactivate virtual environment
deactivate
