FROM registry.redhat.io/ubi8/python-36
USER 0
RUN yum install -y git && yum remove -y nodejs npm kernel-headers && yum update -y && yum clean all \
&& git clone -b 3.0 https://github.com/RedHatInsights/insights-core \
&& pip3 install ./insights-core
COPY src src
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN pip3 install --upgrade pip && pip3 install .
USER 1001
ENTRYPOINT ["puptoo"]
