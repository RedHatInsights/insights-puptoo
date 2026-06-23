#!/bin/bash

echo ">>> Running: cd /app-root/insights-puptoo"
cd /app-root/insights-puptoo
ret=$?
echo "<<< Return value of 'cd /app-root/insights-puptoo': $ret"

echo ">>> Running: uv sync"
uv sync
ret=$?
echo "<<< Return value of 'uv sync': $ret"

echo ">>> Running: uv lock"
uv lock
ret=$?
echo "<<< Return value of 'uv lock': $ret"

### Export requirements.txt & requirements-dev.txt
echo ">>> Running: uv export --format requirements-txt --no-emit-project -o requirements.txt"
uv export --format requirements-txt --no-emit-project -o requirements.txt
ret=$?
echo "<<< Return value of 'uv export ... requirements.txt': $ret"

echo ">>> Running: uv export --format requirements-txt --no-emit-project --only-group dev -o requirements-dev.txt"
uv export --format requirements-txt --no-emit-project --only-group dev -o requirements-dev.txt
ret=$?
echo "<<< Return value of 'uv export ... requirements-dev.txt': $ret"
