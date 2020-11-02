#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install .
pip install .[test]
INVENTORY_TOPIC=platform.inventory.host-ingress-p1 ACG_CONFIG=./cdappconfig.json pytest

if [ $? != 0 ]; then
    exit 1
fi

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
