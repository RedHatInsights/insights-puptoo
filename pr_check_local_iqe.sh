#!/bin/bash

# pr_check_local_iqe.sh — Non-voting PR check using in-repo IQE plugin
# This runs alongside pr_check.sh (voting) to validate the local plugin.
# Once stable, swap this to voting and retire the Nexus-based pipeline.

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

source $CICD_ROOT/deploy_ephemeral_env.sh

source $APP_ROOT/run_cji_with_local_plugin.sh
