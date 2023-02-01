#!/bin/bash

cd $APP_ROOT
IMAGE="quay.io/cloudservices/insights-puptoo"
IMAGE_TAG=$IMAGE_TAG
NETWORK="puptoo-test-$IMAGE_TAG"

function teardown_docker {	
	docker rm -f $TEST_CONTAINER_ID || true
	docker network rm $NETWORK || true
}

trap "teardown_docker" EXIT SIGINT SIGTERM

docker network create --driver bridge $NETWORK

TEST_CONTAINER_ID=$(docker run -d \
	--network ${NETWORK} \
   $IMAGE:$IMAGE_TAG \
   /bin/bash -c 'sleep infinity' || echo "0")

if [[ "$TEST_CONTAINER_ID" == "0" ]]; then
	echo "Failed to start test container"
	exit 1
fi

echo '===================================='
echo '===    Running Tests    ============'
echo '===================================='
set +e

docker exec $TEST_CONTAINER_ID /bin/bash -c 'source ./unit_test.sh'
TEST_RESULT=$?
set -e

if [ $TEST_RESULT -ne 0 ]; then
	echo '====================================='
	echo '====    ✖ ERROR: TEST FAILED     ===='
	echo '====================================='
	exit 1
fi

echo '====================================='
echo '====   ✔ SUCCESS: PASSED TESTS   ===='
echo '====================================='

teardown_docker



