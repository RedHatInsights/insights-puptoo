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
COMPONENT_NAME="insights-puptoo-new"  # name of app-sre "resourceTemplate" in deploy.yaml for this component
IMAGE="quay.io/cloudservices/insights-puptoo"  # TODO: look IMAGE up from build_deploy.sh?
IQE_PLUGINS=ingress
IQE_MARKER_EXPRESSION=smoke

# ---------------------------
# We'll take it from here ...
# ---------------------------

set -ex

oc login --token=$OC_LOGIN_TOKEN --server=$OC_LOGIN_SERVER

curl -JOL https://raw.githubusercontent.com/RedHatInsights/bonfire/6bed83573a7eb2c1248c1eb933386488849ab841/cicd/bootstrap.sh

source ./bootstrap.sh
source ./build.sh
source ./deploy_ephemeral_env.sh
source ./smoke_test.sh
