FROM registry.redhat.io/ubi8/python-36
COPY src src
COPY setup.py .
RUN pip3 install .
USER 0
RUN yum remove -y nodejs npm kernel-headers
USER 1001
ENTRYPOINT ["puptoo"]
