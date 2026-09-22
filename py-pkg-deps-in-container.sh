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

### Export requirements.txt & requirements-dev.txt (uv export so
### MintMaker/Renovate detects the tool from the header and uses uv export)
echo ">>> Running: uv export --frozen --no-dev --no-emit-project -o requirements.txt"
uv export --frozen --no-dev --no-emit-project -o requirements.txt
ret=$?
echo "<<< Return value of 'uv export ... requirements.txt': $ret"

echo ">>> Running: uv export --frozen --only-group dev --no-emit-project -o requirements-dev.txt"
uv export --frozen --only-group dev --no-emit-project -o requirements-dev.txt
ret=$?
echo "<<< Return value of 'uv export ... requirements-dev.txt': $ret"
