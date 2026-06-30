from unittest.mock import MagicMock, patch

import pytest

from src.puptoo.exceptions import FailUploadException
from src.puptoo.upload import get_url, upload_object
import src.puptoo.upload as upload_mod


@pytest.fixture(autouse=True)
def reset_client():
    upload_mod._client = None
    yield
    upload_mod._client = None


# --- get_url ---


@patch("src.puptoo.upload._get_client")
@patch("src.puptoo.upload.config")
def test_get_url_returns_url_on_success(mock_config, mock_get_client):
    mock_config.BUCKET_NAME = "test-bucket"
    client = MagicMock()
    mock_get_client.return_value = client
    client.presigned_get_object.return_value = "https://s3/obj"

    assert get_url("obj-1") == "https://s3/obj"
    client.presigned_get_object.assert_called_once_with("test-bucket", "obj-1")


@patch("src.puptoo.upload._get_client")
@patch("src.puptoo.upload.config")
def test_get_url_raises_fail_upload_on_error(mock_config, mock_get_client):
    mock_config.BUCKET_NAME = "test-bucket"
    client = MagicMock()
    mock_get_client.return_value = client
    cause = RuntimeError("network")
    client.presigned_get_object.side_effect = cause

    with pytest.raises(FailUploadException, match="obj-1") as exc_info:
        get_url("obj-1")
    assert exc_info.value.__cause__ is cause


# --- upload_object ---


@patch("src.puptoo.upload._get_client")
@patch("src.puptoo.upload.config")
def test_upload_object_raises_fail_upload_on_put_error(mock_config, mock_get_client):
    mock_config.BUCKET_NAME = "test-bucket"
    client = MagicMock()
    mock_get_client.return_value = client
    client.bucket_exists.return_value = True
    client.put_object.side_effect = RuntimeError("put failed")

    with pytest.raises(FailUploadException, match="req-1"):
        upload_object({"data": 1}, {"request_id": "req-1"}, {})


@patch("src.puptoo.upload._get_client")
@patch("src.puptoo.upload.config")
def test_upload_object_skips_when_bucket_missing(mock_config, mock_get_client):
    mock_config.BUCKET_NAME = "test-bucket"
    client = MagicMock()
    mock_get_client.return_value = client
    client.bucket_exists.return_value = False

    upload_object({"data": 1}, {"request_id": "req-1"}, {})
    client.put_object.assert_not_called()


@patch("src.puptoo.upload._get_client")
@patch("src.puptoo.upload.config")
def test_upload_object_sets_custom_metadata_on_success(mock_config, mock_get_client):
    mock_config.BUCKET_NAME = "test-bucket"
    client = MagicMock()
    mock_get_client.return_value = client
    client.bucket_exists.return_value = True
    client.presigned_get_object.return_value = "https://s3/url"

    msg = {}
    upload_object({"data": 1}, {"request_id": "req-1"}, msg)

    assert msg["custom_metadata"]["yum_updates_s3url"] == "https://s3/url"
