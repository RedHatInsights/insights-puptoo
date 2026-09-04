#!/bin/bash
set -euo pipefail

pip3 install --upgrade "pip>=26.1,<26.2"
pip3 install "pip-tools>=7.5,<7.6" "pybuild-deps>=0.5,<1"
cd /var/tmp

# Packages that only ship binary wheels (no sdist on PyPI) must be excluded
# from pybuild-deps, which resolves build deps from source distributions.
WHEEL_ONLY_PACKAGES="yggdrasil-engine"

requirements_input="requirements.txt"
if [ -n "${WHEEL_ONLY_PACKAGES}" ]; then
    filter_pattern=$(echo "${WHEEL_ONLY_PACKAGES}" | tr ' ' '|')
    grep -vE "^(${filter_pattern})==" requirements.txt > /tmp/requirements-filtered.txt
    requirements_input="/tmp/requirements-filtered.txt"
fi

pybuild-deps compile --generate-hashes "${requirements_input}" -o requirements-build.txt
pip-compile requirements-build.in --allow-unsafe --generate-hashes -o requirements-extras.txt
