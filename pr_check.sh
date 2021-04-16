#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
pip install -r requirements.txt
INVENTORY_TOPIC=platform.inventory.host-ingress-p1 ACG_CONFIG=./cdappconfig.json pytest

git clone https://github.com/RedHatInsights/inventory-schemas.git

if [ $? != 0 ]; then
    exit 1
fi
# --------------------------------
# Run the profile and schema check
# --------------------------------
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

# ---------------
# Run pytest
#----------------
export INSIGHTS_FILTERS_ENABELD=false
pytest --disable-pytest-warnings ./tests

deactivate

# --------------------------------------------
# Options that must be configured by app owner
# --------------------------------------------
APP_NAME="ingress"  # name of app-sre "application" folder this component lives in
COMPONENT_NAME="puptoo"  # name of app-sre "resourceTemplate" in deploy.yaml for this component
IMAGE="quay.io/cloudservices/insights-puptoo"

IQE_PLUGINS="ingress"
IQE_MARKER_EXPRESSION="smoke"
IQE_FILTER_EXPRESSION=""

# ---------------------------
# We'll take it from here ...
# ---------------------------

source build_deploy.sh

CICD_URL=https://raw.githubusercontent.com/RedHatInsights/bonfire/master/cicd
curl -s $CICD_URL/bootstrap.sh -o bootstrap.sh
source bootstrap.sh  # checks out bonfire and changes to "cicd" dir...

source deploy_ephemeral_env.sh
source smoke_test.sh
