#!/bin/bash

# Run unit tests first since it activates/deactives its own virtual env
source unit_test.sh

# --------------------------------------------
# Options that must be configured by app owner
# --------------------------------------------
APP_NAME="ingress"  # name of app-sre "application" folder this component lives in
APP_TEST_DEPENDENCY_NAME="host-inventory" # name of app-sre "application" which the smoke tests depend on
COMPONENT_NAME="puptoo"  # name of app-sre "resourceTemplate" in deploy.yaml for this component
IMAGE="quay.io/cloudservices/insights-puptoo"

IQE_PLUGINS="e2e"
IQE_MARKER_EXPRESSION="smoke"
IQE_FILTER_EXPRESSION=""
IQE_CJI_TIMEOUT="30m"

# Install bonfire repo/initialize
CICD_URL=https://raw.githubusercontent.com/RedHatInsights/bonfire/master/cicd
curl -s $CICD_URL/bootstrap.sh > .cicd_bootstrap.sh && source .cicd_bootstrap.sh

source $CICD_ROOT/build.sh
#source $CICD_ROOT/deploy_ephemeral_env.sh

# Deploy to application and dependencies to ephemeral env
source ${CICD_ROOT}/_common_deploy_logic.sh
export NAMESPACE=$(bonfire namespace reserve)
bonfire deploy \
    ${APP_NAME} \
    ${APP_TEST_DEPENDENCY_NAME} \
    --source=appsre \
    --ref-env insights-stage \
    --set-template-ref ${COMPONENT_NAME}=${GIT_COMMIT} \
    --set-image-tag ${IMAGE}=${IMAGE_TAG} \
    --namespace ${NAMESPACE} \
    --timeout ${DEPLOY_TIMEOUT} \
    ${COMPONENTS_ARG} \
    ${COMPONENTS_RESOURCES_ARG}

source $CICD_ROOT/cji_smoke_test.sh
