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

### Compile requirements.txt & requirements-dev.txt (uv pip compile so
### MintMaker detects the tool from the header and uses uv pip compile)
echo ">>> Running: uv pip compile pyproject.toml --generate-hashes --python-version 3.11 -o requirements.txt"
uv pip compile pyproject.toml --generate-hashes --python-version 3.11 -o requirements.txt
ret=$?
echo "<<< Return value of 'uv pip compile ... requirements.txt': $ret"

echo ">>> Running: uv pip compile --group dev --generate-hashes --python-version 3.11 -o requirements-dev.txt"
uv pip compile --group dev --generate-hashes --python-version 3.11 -o requirements-dev.txt
ret=$?
echo "<<< Return value of 'uv pip compile ... requirements-dev.txt': $ret"
