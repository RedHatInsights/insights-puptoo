FROM registry.redhat.io/ubi8/python-36
USER 0
RUN yum install -y git && yum remove -y nodejs npm kernel-headers && yum update --security -y && yum clean all \
&& git clone -b 3.0 https://github.com/RedHatInsights/insights-core \
&& pip3 install ./insights-core
COPY src src
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN pip3 install --upgrade pip && pip3 install .
RUN curl -L -o /usr/bin/haberdasher \
https://github.com/RedHatInsights/haberdasher/releases/latest/download/haberdasher_linux_amd64 && \
chmod 755 /usr/bin/haberdasher
USER 1001
ENTRYPOINT ["/usr/bin/haberdasher"]
CMD ["puptoo"]
