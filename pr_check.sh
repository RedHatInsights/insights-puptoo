#!/bin/bash

# --------------------------------------------
# Options that must be configured by app owner
# --------------------------------------------
APP_NAME="ingress"  # name of app-sre "application" folder this component lives in
COMPONENT_NAME="puptoo"  # name of app-sre "resourceTemplate" in deploy.yaml for this component
IMAGE="quay.io/cloudservices/insights-puptoo"
REF_ENV="insights-stage"

IQE_PLUGINS="puptoo"
IQE_MARKER_EXPRESSION="smoke"
IQE_FILTER_EXPRESSION=""
IQE_CJI_TIMEOUT="30m"
IQE_INSTALL_LOCAL_PLUGIN="true"
IQE_LOCAL_PLUGIN_PATH="$APP_ROOT/iqe-insights-upload-processor"

# Install bonfire repo/initialize
CICD_URL=https://raw.githubusercontent.com/RedHatInsights/bonfire/master/cicd
curl -s $CICD_URL/bootstrap.sh > .cicd_bootstrap.sh && source .cicd_bootstrap.sh

# Workaround - clone submodules - initialize and update them
cd ${APP_ROOT}
git submodule update --init

source $CICD_ROOT/build.sh

# Run unit tests
# source $APP_ROOT/run.sh

source $CICD_ROOT/deploy_ephemeral_env.sh

# If local IQE plugin is configured, use custom script to deploy and test
# Otherwise, use the standard cji_smoke_test.sh
if [ "$IQE_INSTALL_LOCAL_PLUGIN" = "true" ]; then
    echo "Using local IQE plugin for CJI tests"
    source $APP_ROOT/run_cji_with_local_plugin.sh
else
    echo "Using standard IQE plugin from Nexus for CJI tests"
    source $CICD_ROOT/cji_smoke_test.sh
fi
