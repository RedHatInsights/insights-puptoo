"""Typed exception hierarchy for puptoo."""


class PuptooError(Exception):
    """Base exception for all puptoo errors."""


class FailDownloadException(PuptooError):
    """Archive download failed."""


class FailExtractException(PuptooError):
    """Fact extraction from an archive failed."""


class FailUploadException(PuptooError):
    """S3 object upload failed."""


class QPCKafkaMsgException(PuptooError):
    """Invalid or unprocessable Kafka message from QPC."""


class QPCReportException(PuptooError):
    """QPC report processing failed."""


class RetryExhaustedException(PuptooError):
    """Message processing retry limit exceeded."""
