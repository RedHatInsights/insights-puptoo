FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

WORKDIR /app-root/

RUN microdnf install --setopt=tsflags=nodocs -y python3.11 python3.11-pip which git tar xz bzip2 unzip gcc glibc-devel krb5-libs krb5-devel python3.11-devel libffi-devel gcc-c++ make zlib-devel openssl-devel libzstd-devel && \
    microdnf upgrade -y && \
    microdnf clean all

RUN set -ex && if [ -e `which python3.11` ]; then ln -s `which python3.11` /usr/local/bin/python; fi

# Download and install librdkafka
RUN curl -L https://github.com/confluentinc/librdkafka/archive/refs/tags/v2.10.1.zip -o /tmp/librdkafka.zip || cp /cachi2/output/deps/generic/v2.10.1.zip /tmp/librdkafka.zip && \
    unzip /tmp/librdkafka.zip -d /tmp && \
    cd /tmp/librdkafka-2.10.1 && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    rm -rf /tmp/librdkafka*

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
COPY unit_test.sh unit_test.sh
COPY dev dev
COPY tests tests
COPY src src

RUN pip3.11 install .

RUN microdnf remove -y which gcc python3.11-devel libffi-devel gcc-c++ make zlib-devel openssl-devel libzstd-devel && \
    microdnf clean all

CMD ["puptoo"]

# Define labels for the puptoo
LABEL url="https://www.redhat.com"
LABEL name="puptoo" \
      description="This adds the satellite/puptoo-rhel9 image to the Red Hat container registry. To pull this container image, run the following command: podman pull registry.stage.redhat.io/satellite/puptoo-rhel9" \
      summary="A new satellite/puptoo-rhel9 container image is now available as a Technology Preview in the Red Hat container registry."
LABEL com.redhat.component="puptoo" \
      io.k8s.display-name="IoP puptoo" \
      io.k8s.description="This adds the satellite/puptoo image to the Red Hat container registry. To pull this container image, run the following command: podman pull registry.stage.redhat.io/satellite/puptoo-rhel9" \
      io.openshift.tags="insights satellite iop puptoo"
