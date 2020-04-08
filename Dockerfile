FROM registry.redhat.io/ubi8/python-36
COPY src src
COPY setup.py .
RUN pip3 install .
ENTRYPOINT ["puptoo"]
