#!/bin/bash

# check python version
python3 --version

python3 -m venv .unit_test_venv
source .unit_test_venv/bin/activate
pip install --upgrade pip
pip install .
pip install -r requirements.txt
INSIGHTS_FILTERS_ENABLED=false INVENTORY_TOPIC=platform.inventory.host-ingress-p1 ACG_CONFIG=./cdappconfig.json pytest tests/ --junitxml=$WORKSPACE/artifacts/junit-unit_tests.xml

if [ $? != 0 ]; then
   echo "Failed to run unit test"
   exit 1
fi

git clone https://github.com/RedHatInsights/inventory-schemas.git

echo '---------------------------------'
echo ' Run the profile and schema check'
echo '---------------------------------'
for file in dev/test-archives/*; do
   filename="$(basename "$file").tar.gz"
   tar -zcf $filename "$file"
   insights-run -p src/puptoo -f json $filename > output.json
   insights-run -p src/puptoo $filename # this is to print the results in the test console
   if [ $? != 0 ]; then
      exit 1
   fi
   python parse_json.py
   python inventory-schemas/tools/simple-test/tester.py inventory-schemas/schemas/system_profile/v1.yaml output.json
   if [ $? != 0 ]; then
      exit 1
   fi
   rm $filename
   rm -rf inventory-schemas
   rm output.json
done

deactivate
