#!/bin/bash

# check python version
python3.11 --version

python3.11 -m venv /tmp/.unit_test_venv
source /tmp/.unit_test_venv/bin/activate
pip install --upgrade pip
pip install .
pip install -r requirements.txt
pip install -r requirements-dev.txt
INSIGHTS_FILTERS_ENABLED=false INVENTORY_TOPIC=platform.inventory.host-ingress-p1 ACG_CONFIG=dev/cdappconfig.json pytest tests/ --junitxml=$WORKSPACE/artifacts/junit-unit_tests.xml

if [ $? != 0 ]; then
   echo "Failed to run unit test"
   exit 1
fi

# Clone inventory-schemas to /tmp
git clone https://github.com/RedHatInsights/inventory-schemas.git /tmp/inventory-schemas

echo '---------------------------------'
echo ' Run the profile and schema check'
echo '---------------------------------'
for file in dev/test-archives/*; do
    filename="$(basename "$file").tar.gz"
    # Create tar archive in /tmp
    tar -zcf /tmp/$filename "$file"
    # Run insights-run and output to /tmp/output.json
    insights-run -p src/puptoo -f json /tmp/$filename > /tmp/output.json
    insights-run -p src/puptoo /tmp/$filename # Print results in test console
    if [ $? != 0 ]; then
        exit 1
    fi
    OUTPUT_JSON="/tmp/output.json" python3.11 dev/parse_json.py
    # Run schema tester with files in /tmp
    python3.11 /tmp/inventory-schemas/tools/simple-test/tester.py /tmp/inventory-schemas/schemas/system_profile/v1.yaml /tmp/output.json
    if [ $? != 0 ]; then
        exit 1
    fi
    # Clean up files
    rm /tmp/$filename
    rm /tmp/output.json
done

# Clean up inventory-schemas directory
rm -rf /tmp/inventory-schemas

# Deactivate virtual environment
deactivate
