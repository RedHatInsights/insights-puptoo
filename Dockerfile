FROM registry.redhat.io/ubi8/ubi-minimal
WORKDIR /app-root/
RUN microdnf install -y python36 python3-devel curl python3-pip git tar xz bzip2 && \
    git clone -b 3.0 https://github.com/RedHatInsights/insights-core && \
    pip3 install ./insights-core
COPY src src
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN pip3 install --upgrade pip && pip3 install .  
RUN curl -L -o /usr/bin/haberdasher \ 
    https://github.com/RedHatInsights/haberdasher/releases/latest/download/haberdasher_linux_amd64 && \
    chmod 755 /usr/bin/haberdasher
ENTRYPOINT ["/usr/bin/haberdasher"]
CMD ["puptoo"]