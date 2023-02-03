#!/bin/bash

# Run unit tests first since it activates/deactives its own virtual env
source unit_test.sh

# --------------------------------------------
# Options that must be configured by app owner
# --------------------------------------------
APP_NAME="ingress"  # name of app-sre "application" folder this component lives in
COMPONENT_NAME="puptoo"  # name of app-sre "resourceTemplate" in deploy.yaml for this component
IMAGE="quay.io/cloudservices/insights-puptoo"
BONFIRE_REPO_ORG="Victoremepunto"
BONFIRE_REPO_BRANCH="set-expiry-label-as-parameter"

IQE_PLUGINS="e2e"
IQE_MARKER_EXPRESSION="smoke"
IQE_FILTER_EXPRESSION=""
IQE_CJI_TIMEOUT="30m"

# Install bonfire repo/initialize
CICD_URL=https://raw.githubusercontent.com/Victoremepunto/bonfire/master/cicd
curl -s $CICD_URL/bootstrap.sh > .cicd_bootstrap.sh && source .cicd_bootstrap.sh

source $CICD_ROOT/build.sh
#source $CICD_ROOT/deploy_ephemeral_env.sh

#source $CICD_ROOT/cji_smoke_test.sh
