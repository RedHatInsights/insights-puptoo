FROM registry.redhat.io/ubi8/ubi-minimal

WORKDIR /app-root/

RUN microdnf install -y python38 python38-devel curl python3-pip git tar xz bzip2 unzip && \
    git clone -b 3.0 https://github.com/RedHatInsights/insights-core && \
    pip3 install ./insights-core

COPY src src
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

RUN pip3 install --upgrade pip && pip3 install .

CMD ["puptoo"]
