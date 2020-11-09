FROM registry.redhat.io/ubi8/python-36
USER 0
RUN yum install -y git && yum remove -y nodejs npm kernel-headers \
&& git clone -b 3.0 https://github.com/RedHatInsights/insights-core \
&& pip3 install ./insights-core
COPY src src
COPY setup.py .
RUN pip3 install .
ENTRYPOINT ["puptoo"]
