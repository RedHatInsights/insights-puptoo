#!/bin/bash
set -euo pipefail

# Detect the package manager (microdnf on ubi-minimal, dnf on full ubi)
if command -v microdnf >/dev/null 2>&1; then
    PKG_MGR=microdnf
elif command -v dnf >/dev/null 2>&1; then
    PKG_MGR=dnf
else
    echo "Error: neither microdnf nor dnf found"
    exit 1
fi

$PKG_MGR install --setopt=tsflags=nodocs -y python3.11 python3.11-pip which git tar xz bzip2 unzip gcc glibc-devel krb5-libs krb5-devel python3.11-devel libffi-devel gcc-c++ make zlib-devel openssl-devel libzstd-devel wget
$PKG_MGR upgrade -y
$PKG_MGR clean all

for cmd in python3 python; do
    if [ ! -e /usr/local/bin/$cmd ] && command -v python3.11 >/dev/null 2>&1; then
        ln -s "$(command -v python3.11)" /usr/local/bin/$cmd
    fi
done
for cmd in pip3 pip; do
    if [ ! -e /usr/local/bin/$cmd ] && command -v pip3.11 >/dev/null 2>&1; then
        ln -s "$(command -v pip3.11)" /usr/local/bin/$cmd
    fi
done
