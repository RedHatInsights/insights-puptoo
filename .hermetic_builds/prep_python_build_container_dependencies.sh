#!/bin/bash

microdnf install --setopt=tsflags=nodocs -y python3 python3-pip which git tar xz bzip2 unzip gcc glibc-devel krb5-libs krb5-devel python3-devel libffi-devel gcc-c++ make zlib-ng-compat-devel openssl-devel libzstd-devel && \
    microdnf upgrade -y && \
    microdnf clean all
set -ex && if [ -e `which python3` ]; then ln -s `which python3` /usr/local/bin/python3; fi
set -ex && if [ -e `which python3` ]; then ln -s `which python3` /usr/local/bin/python; fi
set -ex && if [ -e `which pip3` ]; then ln -s `which pip3` /usr/local/bin/pip3; fi
set -ex && if [ -e `which pip3` ]; then ln -s `which pip3` /usr/local/bin/pip; fi
microdnf install -y wget
