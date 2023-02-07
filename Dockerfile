FROM registry.redhat.io/ubi8/ubi-minimal

WORKDIR /app-root/

RUN microdnf install -y python38 python38-devel curl python38-pip git tar xz bzip2 unzip && \
    git clone -b 3.0 https://github.com/RedHatInsights/insights-core && \
    pip3 install ./insights-core

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
COPY unit_test.sh unit_test.sh
COPY dev dev
COPY tests tests 
COPY src src

RUN pip3 install --upgrade pip && pip3 install . 

CMD ["puptoo"]
