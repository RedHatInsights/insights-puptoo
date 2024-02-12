FROM registry.redhat.io/ubi8/ubi-minimal

WORKDIR /app-root/

RUN INSTALL_PKGS="python3.11 python3.11-devel curl python3.11-pip git tar xz bzip2 unzip" && \
    microdnf --nodocs -y upgrade && \
    microdnf -y --setopt=tsflags=nodocs --setopt=install_weak_deps=0 install $INSTALL_PKGS && \
    microdnf clean all && \
    git clone -b 3.0 https://github.com/RedHatInsights/insights-core && \
    pip3 install ./insights-core

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
COPY unit_test.sh unit_test.sh
COPY dev dev
COPY tests tests 
COPY src src

RUN pip3.11 install --upgrade pip && pip3.11 install . 

CMD ["puptoo"]
