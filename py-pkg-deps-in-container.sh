#!/bin/bash

echo ">>> Running: cd /app-root/insights-puptoo"
cd /app-root/insights-puptoo
ret=$?
echo "<<< Return value of 'cd /app-root/insights-puptoo': $ret"

# pip install poetry
echo ">>> Running: poetry install"
poetry install
ret=$?
echo "<<< Return value of 'poetry install': $ret"

echo ">>> Running: poetry lock"
poetry lock
ret=$?
echo "<<< Return value of 'poetry lock': $ret"

# echo ">>> Running: poetry self add poetry-plugin-export"
# poetry self add poetry-plugin-export
# ret=$?
# echo "<<< Return value of 'poetry self add poetry-plugin-export': $ret"

### Export requirements.txt & requirements-dev.txt
echo ">>> Running: poetry export --format requirements.txt --output requirements.txt"
poetry export --format requirements.txt --output requirements.txt
ret=$?
echo "<<< Return value of 'poetry export --format requirements.txt --output requirements.txt': $ret"

echo ">>> Running: poetry export --only dev -o requirements-dev.txt"
poetry export --only dev -o requirements-dev.txt
ret=$?
echo "<<< Return value of 'poetry export --only dev -o requirements-dev.txt': $ret"
