#!/bin/bash

set -exv

IMAGE="quay.io/cloudservices/insights-puptoo"
IMAGE_TAG=$(git rev-parse --short=7 HEAD)
SMOKE_TEST_TAG="latest"
SECURITY_COMPLIANCE_TAG="sc-$(date +%Y%m%d)"

if [[ -z "$QUAY_USER" || -z "$QUAY_TOKEN" ]]; then
    echo "QUAY_USER and QUAY_TOKEN must be set"
    exit 1
fi

DOCKER_CONF="$PWD/.docker"
mkdir -p "$DOCKER_CONF"
docker --config="$DOCKER_CONF" login -u="$QUAY_USER" -p="$QUAY_TOKEN" quay.io
docker --config="$DOCKER_CONF" login -u="$RH_REGISTRY_USER" -p="$RH_REGISTRY_TOKEN" registry.redhat.io
docker --config="$DOCKER_CONF" build --no-cache -t "${IMAGE}:${IMAGE_TAG}" .
docker --config="$DOCKER_CONF" push "${IMAGE}:${IMAGE_TAG}"

if [[ $GIT_BRANCH == *"security-compliance"* ]]; then
    docker --config="$DOCKER_CONF" tag "${IMAGE}:${IMAGE_TAG}" "${IMAGE}:${SECURITY_COMPLIANCE_TAG}"
    docker --config="$DOCKER_CONF" push "${IMAGE}:${SECURITY_COMPLIANCE_TAG}"
elif [ "${PUSH_TO_LATEST:=true}" == "true" ]; then
    docker --config="$DOCKER_CONF" tag "${IMAGE}:${IMAGE_TAG}" "${IMAGE}:${SMOKE_TEST_TAG}"
    docker --config="$DOCKER_CONF" push "${IMAGE}:${SMOKE_TEST_TAG}"
fi
