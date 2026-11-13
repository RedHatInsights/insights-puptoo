FROM registry.access.redhat.com/ubi10/s2i-base:1794223620 AS kafka_build
USER 0
ADD librdkafka .
RUN ./configure --prefix=/usr && \
    make && \
    make install

FROM registry.access.redhat.com/ubi10/ubi-minimal:1794499368

WORKDIR /app-root/

# file-libs provides libmagic, which insights-core's insights.contrib.magic binds
# to for archive content-type detection. UBI9 pulled it in transitively; UBI10 does
# not. Without it insights-core falls back to the `file` CLI, which is not installed,
# and Advisor archive extraction fails with "No such file or directory: 'file'".
RUN microdnf install --setopt=tsflags=nodocs -y python3 python3-pip which git tar xz bzip2 unzip gcc glibc-devel krb5-libs krb5-devel python3-devel libffi-devel gcc-c++ make zlib-ng-compat zlib-ng-compat-devel openssl-libs openssl-devel libzstd libzstd-devel file-libs && \
    microdnf upgrade -y && \
    microdnf clean all

RUN set -ex && if [ -e `which python3` ]; then ln -s `which python3` /usr/local/bin/python; fi

# install librdkafka
COPY --from=kafka_build /usr/lib/librdkafka*.so* /usr/lib/
COPY --from=kafka_build /usr/lib/pkgconfig/rdkafka*.pc /usr/lib/pkgconfig/
COPY --from=kafka_build /usr/include/librdkafka /usr/include/librdkafka
RUN ldconfig

COPY --chown=1001:0 uv.lock uv.lock
COPY --chown=1001:0 pyproject.toml pyproject.toml
COPY --chown=1001:0 requirements.txt requirements.txt
COPY --chown=1001:0 requirements-dev.txt requirements-dev.txt
COPY --chown=1001:0 unit_test.sh unit_test.sh
COPY --chown=1001:0 dev dev
COPY --chown=1001:0 tests tests
COPY --chown=1001:0 src src

RUN pip3 install --upgrade "pip>=26.1.2" && \
    pip3 install . --ignore-installed

RUN microdnf remove -y which gcc python3-devel libffi-devel gcc-c++ make zlib-ng-compat-devel openssl-devel libzstd-devel && \
    microdnf clean all

ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib

RUN mkdir -p /licenses
COPY LICENSE /licenses

RUN mkdir -p /artifacts &&  chown 1001:0 /artifacts

USER 1001

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
