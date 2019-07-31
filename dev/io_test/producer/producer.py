import json
import time
import logging
import os
import boto3
import sys


from kafka import KafkaConsumer, KafkaProducer

AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY', None)
AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY', None)
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', "http://minio:9000")
REQUEST_ID = os.getenv("REQUEST_ID", "testrequestid")
MSG_COUNT = os.getenv("MSG_COUNT", 100)

s3 = boto3.client('s3',
                  endpoint_url=S3_ENDPOINT_URL,
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

producer = KafkaProducer(bootstrap_servers=["kafka:29092"],
                         value_serializer=lambda x: json.dumps(x).encode("utf-8")
                         )

msg = {"topic": "platform.upload.advisor",
       "data": {"request_id": REQUEST_ID,
                "account": "000001"}}

logging.basicConfig(level="INFO",
                    format="%(threadName)s %(levelname)s %(name)s - %(message)s"
                    )

logger = logging.getLogger("producer")

def get_url(uuid):
    url = s3.generate_presigned_url("get_object",
                                    Params={"Bucket": "insights-upload-perma",
                                            "Key": uuid}, ExpiresIn=86400)
    return url

def main():
    count = 0
    test_url = get_url(REQUEST_ID)
    while count < MSG_COUNT:
        msg["data"]["time"] = time.time()
        msg["data"]["url"] = test_url
        logger.info("sending message %s", count)
        producer.send(msg["topic"], value=msg["data"])

        count += 1

if __name__ == "__main__":
    time.sleep(10)  # need to delay a bit so the kafka boxes can spin up
    main()
