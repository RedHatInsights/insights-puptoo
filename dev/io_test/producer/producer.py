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

    s3 = boto3.client("s3",
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION)

else:
    AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY', None)
    AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY', None)
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', "http://minio:9000")

    s3 = boto3.client('s3',
                      endpoint_url=S3_ENDPOINT_URL,
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

MSG_COUNT = os.getenv("MSG_COUNT", 100)
FETCH_BUCKET = os.getenv("FETCH_BUCKET", "insights-upload-perma")
PRODUCE_TOPIC = os.getenv("PRODUCE_TOPIC", "platform.upload.advisor")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split()

producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS,
                         value_serializer=lambda x: json.dumps(x).encode("utf-8")
                         )

msg = {"topic": PRODUCE_TOPIC,
       "data": {"account": "000001"}}

logging.basicConfig(level="INFO",
                    format="%(asctime)s %(threadName)s %(levelname)s %(name)s - %(message)s"
                    )

logger = logging.getLogger("producer")

def gen_keys_and_urls():
    for key in s3.list_objects(Bucket=FETCH_BUCKET)["Contents"][:MSG_COUNT]:
        yield key, get_url(key)

def get_url(uuid):
    url = s3.generate_presigned_url("get_object",
                                    Params={"Bucket": FETCH_BUCKET,
                                            "Key": uuid}, ExpiresIn=86400)
    return url

def main():
    for key, url in gen_keys_and_urls():
        data = dict(request_id=key, url=url, account=msg["data"]["account"])
        logger.info("sending message for ID %s", key)
        producer.send(PRODUCE_TOPIC, value=data)
    producer.flush()
    logger.info("producer flushed")

if __name__ == "__main__":
    time.sleep(10)  # need to delay a bit so the kafka boxes can spin up
    main()
