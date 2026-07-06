import io
import json
import logging
from minio import Minio
from .exceptions import FailUploadException
from .utils import config, puptoo_logging  # noqa: F401

logger = logging.getLogger(config.APP_NAME)


# Minio client setup and upload yum_updates object
def upload_object(yum_updates, extra, msg):
    _bytes = json.dumps(yum_updates).encode("utf-8")
    client = Minio(
        endpoint=config.S3_ENDPOINT,
        access_key=config.AWS_ACCESS_KEY,
        secret_key=config.AWS_SECRET_KEY,
        secure=config.USE_SSL,
    )
    if client.bucket_exists(config.BUCKET_NAME):
        try:
            client.put_object(
                bucket_name=config.BUCKET_NAME,
                object_name=extra["request_id"],
                data=io.BytesIO(_bytes),
                length=len(_bytes),
            )
            logger.info(
                "Successfully uploaded object (%s) to s3 bucket", extra["request_id"]
            )

            # add object url
            if msg.get("custom_metadata") is None:
                msg["custom_metadata"] = {}
            msg["custom_metadata"]["yum_updates_s3url"] = get_url(
                client, extra["request_id"]
            )
        except Exception as exc:
            raise FailUploadException(
                f"Failed to upload object {extra['request_id']}"
            ) from exc
    else:
        logger.error("Bucket (%s) does not exist", config.BUCKET_NAME)


# Get presigned object URL
def get_url(client, object_name):
    try:
        url = client.presigned_get_object(config.BUCKET_NAME, object_name)
        logger.info("Successfully fetched object (%s) url - %s", object_name, url)
    except Exception as exc:
        raise FailUploadException(
            f"Failed to fetch presigned URL for object {object_name}"
        ) from exc

    return url
