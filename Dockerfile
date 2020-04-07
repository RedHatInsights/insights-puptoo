FROM registry.redhat.io/ubi8/python-36
# RUN dnf -y install python3-pip git
RUN pip3 install pipenv
COPY *.py ./
COPY utils ./
COPY mq ./
COPY Pipfile* ./
RUN pipenv --python 3.6 install
