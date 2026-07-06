import json
import logging
import os

import boto3
from kafka import KafkaProducer

if any("KUBERNETES" in k for k in os.environ):
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

else:
    AWS_ACCESS_KEY_ID = os.getenv("MINIO_ACCESS_KEY", None)
    AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_SECRET_KEY", None)
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

MSG_COUNT = int(os.getenv("MSG_COUNT", 100))
FETCH_BUCKET = os.getenv("FETCH_BUCKET", "insights-upload-perma")
PRODUCE_TOPIC = os.getenv("PRODUCE_TOPIC", "platform.upload.announce")
SERVICE = os.getenv("SERVICE", "advisor")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092").split()

B64_IDENTITY = (
    "eyJpZGVudGl0eSI6IHsib3JnX2lkIjogIjAwMDAwMSIsICJ0eXBlIjogIlVzZXIiLCAi"
    "c3lzdGVtIjogeyJjbiI6ICJ0ZXN0LW93bmVyIn19fQ=="
)

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda x: json.dumps(x).encode("utf-8"),
)

logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(threadName)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger("producer")


def get_keys():
    response = s3.list_objects(Bucket=FETCH_BUCKET)
    contents = response.get("Contents", [])
    if not contents:
        logger.error(
            "No objects found in bucket '%s'. Upload an insights archive first.",
            FETCH_BUCKET,
        )
        return []
    return [key["Key"] for key in contents[:MSG_COUNT]]


def get_url(uuid):
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": FETCH_BUCKET, "Key": uuid}, ExpiresIn=86400
    )
    return url


def main():
    keys = get_keys()
    for key in keys:
        url = get_url(key)
        msg = {
            "account": "000001",
            "org_id": "000001",
            "request_id": key,
            "url": url,
            "b64_identity": B64_IDENTITY,
            "metadata": {},
            "platform_metadata": {"org_id": "000001"},
        }
        headers = [("service", SERVICE.encode("utf-8"))]
        logger.info("sending message for ID %s", key)
        producer.send(PRODUCE_TOPIC, value=msg, headers=headers)

    producer.flush()
    producer.close()
    logger.info("sent %d message(s)", len(keys))


if __name__ == "__main__":
    main()
