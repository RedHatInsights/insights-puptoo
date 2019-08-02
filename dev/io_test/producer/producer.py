import json
import time
import logging
import os
import boto3
import sys


from kafka import KafkaConsumer, KafkaProducer

if any("KUBERNETES" in k for k in os.environ):
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
else:
    AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY', None)
    AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY', None)
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', "http://minio:9000")

MSG_COUNT = os.getenv("MSG_COUNT", 100)
FETCH_BUCKET = os.getenv("FETCH_BUCKET", "insights-upload-perma")
PRODUCE_TOPIC = os.getenv("PRODUCE_TOPIC", "platform.upload.advisor")

s3 = boto3.client('s3',
                  endpoint_url=S3_ENDPOINT_URL,
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

producer = KafkaProducer(bootstrap_servers=["kafka:29092"],
                         value_serializer=lambda x: json.dumps(x).encode("utf-8")
                         )

msg = {"topic": PRODUCE_TOPIC,
       "data": {"account": "000001"}}

logging.basicConfig(level="INFO",
                    format="%(threadName)s %(levelname)s %(name)s - %(message)s"
                    )

logger = logging.getLogger("producer")

def get_keys():
    keylist = []
    for key in s3.list_objects(Bucket=FETCH_BUCKET)["Contents"][:MSG_COUNT]:
        keylist.append(key["Key"])

    return keylist


def get_url(uuid):
    url = s3.generate_presigned_url("get_object",
                                    Params={"Bucket": FETCH_BUCKET,
                                            "Key": uuid}, ExpiresIn=86400)
    return url

def main():
    keys = get_keys()
    for key in keys:
        url = get_url(key)
        msg["data"]["request_id"] = key
        msg["data"]["url"] = url
        logger.info("sending message for ID %s", key)
        producer.send(msg["topic"], value=msg["data"])

    producer.flush()

if __name__ == "__main__":
    time.sleep(10)  # need to delay a bit so the kafka boxes can spin up
    main()
