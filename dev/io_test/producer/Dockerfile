FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY producer.py .

CMD [ "python", "./producer.py" ]