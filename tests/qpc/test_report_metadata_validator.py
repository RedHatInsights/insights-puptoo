import tarfile
import uuid
from io import BytesIO
from unittest.mock import patch

import pytest

from src.puptoo.exceptions import FailExtractException
from src.puptoo.qpc.validators import validate_metadata_file
from src.puptoo.utils.config import MAX_HOSTS_PER_REP
from tests.qpc.conftest import create_tar_buffer


def _extract_metadata_member(tar):
    for member in tar.getmembers():
        if "/metadata.json" in member.name or member.name == "metadata.json":
            return member
    return None


def test_metadata_with_missing_keys():
    uuid1 = uuid.uuid4()
    metadata_json = {
        "host_inventory_api_version": "1.0.0",
        "source": "qpc",
        "source_metadata": {"foo": "bar"},
        "report_slices": {str(uuid1): {"number_hosts": 1}},
    }
    report_json = {
        "report_slice_id": str(uuid1),
        "hosts": {str(uuid1): {"key": "value"}},
    }
    report_files = {
        "metadata.json": metadata_json,
        f"{uuid1}.json": report_json,
    }
    request_obj = {"account": 123, "request_id": 456}
    buf = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buf), mode="r:*")
    metafile = _extract_metadata_member(tar)
    with pytest.raises(FailExtractException):
        validate_metadata_file(tar, metafile, request_obj)


def test_validate_metadata_file():
    uuid1 = uuid.uuid4()
    metadata_json = {
        "report_id": 1,
        "host_inventory_api_version": "1.0.0",
        "source": "qpc",
        "source_metadata": {"foo": "bar"},
        "report_slices": {str(uuid1): {"number_hosts": 1}},
    }
    report_json = {
        "report_slice_id": str(uuid1),
        "hosts": {str(uuid1): {"key": "value"}},
    }
    report_files = {
        "metadata.json": metadata_json,
        f"{uuid1}.json": report_json,
    }
    request_obj = {"account": 123, "org_id": 123, "request_id": 456}
    buf = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buf), mode="r:*")
    metafile = _extract_metadata_member(tar)
    result = validate_metadata_file(tar, metafile, request_obj)
    assert result == {str(uuid1): 1}


def test_metadata_with_invalid_slice():
    uuid1 = uuid.uuid4()
    metadata_json = {
        "report_id": 1,
        "host_inventory_api_version": "1.0.0",
        "source": "qpc",
        "source_metadata": {"foo": "bar"},
        "report_slices": {str(uuid1): {"number_hosts": MAX_HOSTS_PER_REP + 1}},
    }
    report_json = {
        "report_slice_id": str(uuid1),
        "hosts": {str(uuid1): {"key": "value"}},
    }
    report_files = {
        "metadata.json": metadata_json,
        f"{uuid1}.json": report_json,
    }
    request_obj = {"account": 123, "org_id": 123, "request_id": 456}
    buf = create_tar_buffer(report_files)
    tar = tarfile.open(fileobj=BytesIO(buf), mode="r:*")
    metafile = _extract_metadata_member(tar)
    with patch("src.puptoo.qpc.validators.LOG.warning") as mock:
        result = validate_metadata_file(tar, metafile, request_obj)
    mock.assert_called_once()
    assert result == {}
