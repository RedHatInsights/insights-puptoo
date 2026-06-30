import pytest

from src.puptoo.exceptions import (
    PuptooError,
    FailDownloadException,
    FailExtractException,
    FailUploadException,
    QPCKafkaMsgException,
    QPCReportException,
    RetryExhaustedException,
)

ALL_LEAF_EXCEPTIONS = [
    FailDownloadException,
    FailExtractException,
    FailUploadException,
    QPCKafkaMsgException,
    QPCReportException,
    RetryExhaustedException,
]

ALL_EXCEPTIONS = [PuptooError] + ALL_LEAF_EXCEPTIONS


@pytest.mark.parametrize("exc_cls", ALL_LEAF_EXCEPTIONS)
def test_all_subclass_of_puptoo_error(exc_cls):
    assert issubclass(exc_cls, PuptooError)


def test_puptoo_error_is_subclass_of_exception():
    assert issubclass(PuptooError, Exception)


@pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
def test_exception_message_preserved(exc_cls):
    with pytest.raises(exc_cls, match="something went wrong"):
        raise exc_cls("something went wrong")


def test_exception_chaining_preserves_cause():
    cause = ValueError("root cause")
    with pytest.raises(FailUploadException) as exc_info:
        raise FailUploadException("upload failed") from cause
    assert exc_info.value.__cause__ is cause


def test_catch_by_base_catches_subclass():
    caught = False
    try:
        raise FailExtractException("bad extraction")
    except PuptooError:
        caught = True
    assert caught


def test_sibling_not_caught_by_sibling():
    with pytest.raises(FailExtractException):
        try:
            raise FailExtractException("extract error")
        except FailUploadException:
            pytest.fail(
                "FailExtractException should not be caught by FailUploadException"
            )


def test_exception_classes_are_distinct():
    for i, cls_a in enumerate(ALL_LEAF_EXCEPTIONS):
        for cls_b in ALL_LEAF_EXCEPTIONS[i + 1 :]:
            assert cls_a is not cls_b
