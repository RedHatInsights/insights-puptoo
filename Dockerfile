FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

WORKDIR /app-root/

RUN microdnf install --setopt=tsflags=nodocs -y python3.11 python3.11-pip which git tar xz bzip2 unzip gcc krb5-libs krb5-devel python3.11-devel libffi-devel && \
    microdnf upgrade -y && \
    microdnf clean all

RUN set -ex && if [ -e `which python3.11` ]; then ln -s `which python3.11` /usr/local/bin/python; fi

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
COPY unit_test.sh unit_test.sh
COPY dev dev
COPY tests tests
COPY src src

RUN pip3.11 install .

CMD ["puptoo"]
