import hashlib
import io
import json
import logging
from minio import Minio
from .utils import config, puptoo_logging  # noqa: F401

logger = logging.getLogger(config.APP_NAME)


def normalize_yum_updates(yum_updates):
    """
    Normalize yum_updates for deterministic checksumming.
    Sorts dictionary keys and list items to ensure consistent ordering.
    """
    if not isinstance(yum_updates, dict):
        return yum_updates

    normalized = {}

    # Sort all top-level keys
    for key in sorted(yum_updates.keys()):
        if key == "update_list":
            # Sort update_list dictionary keys (package names)
            normalized["update_list"] = {}
            for pkg_name in sorted(yum_updates["update_list"].keys()):
                pkg_data = yum_updates["update_list"][pkg_name]
                # Sort available_updates list (by package name, then erratum, then repository)
                if isinstance(pkg_data, dict) and "available_updates" in pkg_data:
                    normalized["update_list"][pkg_name] = {
                        "available_updates": sorted(
                            pkg_data["available_updates"],
                            key=lambda x: (
                                x.get("package", ""),
                                x.get("erratum", ""),
                                x.get("repository", ""),
                            ),
                        )
                    }
                else:
                    # Preserve other fields if they exist
                    normalized["update_list"][pkg_name] = pkg_data
        else:
            normalized[key] = yum_updates[key]

    return normalized


def get_yum_updates_checksum(yum_updates):
    """
    Calculate SHA256 checksum of normalized yum_updates data.
    Returns hex digest of the checksum.
    """
    normalized = normalize_yum_updates(yum_updates)
    json_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


# Minio client setup and upload yum_updates object
def upload_object(yum_updates, extra, msg):
    _bytes = json.dumps(yum_updates).encode("utf-8")
    client = Minio(endpoint=config.S3_ENDPOINT, access_key=config.AWS_ACCESS_KEY, secret_key=config.AWS_SECRET_KEY, secure=config.USE_SSL)
    if client.bucket_exists(config.BUCKET_NAME):
        try:
            client.put_object(bucket_name=config.BUCKET_NAME, object_name=extra["request_id"], data=io.BytesIO(_bytes), length=len(_bytes))
            logger.info(
                "Successfully uploaded object (%s) to s3 bucket", extra["request_id"]
            )

            # Calculate checksum and add to custom_metadata
            checksum = get_yum_updates_checksum(yum_updates)
            if msg.get("custom_metadata") is None:
                msg["custom_metadata"] = {}
            msg["custom_metadata"]["yum_updates_checksum"] = checksum
            msg["custom_metadata"]["yum_updates_s3url"] = get_url(client, extra["request_id"])
            logger.info(
                "Calculated yum_updates checksum (%s) for request_id: %s", checksum, extra["request_id"]
            )
        except:
            logger.exception("An error occurred while uploading object")
    else:
        logger.error("Bucket (%s) does not exist", config.BUCKET_NAME)


# Get presigned object URL
def get_url(client, object_name):
    try:
        url = client.presigned_get_object(config.BUCKET_NAME, object_name)
        logger.info("Successfully fetched object (%s) url - %s", object_name, url)
    except Exception:
        logger.exception("An error occurred while fetching s3 url for object %s", object_name)

    return url
