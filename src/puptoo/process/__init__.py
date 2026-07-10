import logging
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from insights import extract as extract_archive
from opentelemetry import trace

from ..telemetry import get_tracer
from ..utils import config, metrics
from .profile import get_system_profile, postprocess

logger = logging.getLogger(config.APP_NAME)
tracer = get_tracer(__name__)


@metrics.GET_FILE.time()
def get_archive(url):
    archive = requests.get(url)
    return archive.content


def validate_size(path, extra):
    """
    reject payloads where the extracted size exceeds the configured max
    """
    total_size = sum(p.stat().st_size for p in Path(path).rglob("*"))
    metrics.msg_extraction_size.observe(total_size)
    if total_size >= int(config.MAX_EXTRACTED_SIZE):
        metrics.msg_size_exceeded.inc()
        logger.info(
            "Unpacked archive exceeds extracted file size limit of %s, request_id: %s",
            config.MAX_EXTRACTED_SIZE,
            extra["request_id"],
        )
        # TODO: actively reject payloads that exceed our configured max size
    elif total_size >= int(config.MAX_EXTRACTED_SIZE_L2):
        # Request for debugging usage in insights-engine
        logger.info(
            "Unpacked archive exceeds extracted file size limit of %s (but within limit %s), request_id: %s",
            config.MAX_EXTRACTED_SIZE_L2,
            config.MAX_EXTRACTED_SIZE,
            extra["request_id"],
        )


@contextmanager
def unpacked_archive(msg, remove=True):
    """
    Simple ContextManager which is used to for automatically downloading + unpacking
    insights archive, and performing cleanup when needed.
    """
    metrics.unpacking_count.inc()
    try:
        with NamedTemporaryFile(delete=remove) as tf:
            tf.write(get_archive(msg["url"]))
            tf.flush()
            with extract_archive(tf.name) as ex:
                yield ex, None
    except Exception as err:
        metrics.unpacking_failure.inc()
        yield None, err
    else:
        metrics.unpacking_success.inc()


@metrics.EXTRACT.time()
def extract(msg, extra, remove=True):
    """
    Perform the extraction of canonical system facts and system profile.
    """
    with tracer.start_as_current_span("puptoo.extract_facts") as span:
        facts = {"system_profile": {}}
        with unpacked_archive(msg, remove) as (unpacked, err):
            if err:
                logger.exception("Failed to extract archive: %s", str(err), extra=extra)
                facts["error"] = str(err)
                span.set_status(trace.StatusCode.ERROR, str(err))
                span.record_exception(err)
                return facts

            try:
                with tracer.start_as_current_span(
                    "puptoo.validate_size",
                ) as vs_span:
                    validate_size(unpacked.tmp_dir, extra)
                    vs_span.set_status(trace.StatusCode.OK)
                with tracer.start_as_current_span(
                    "puptoo.get_system_profile"
                ) as sp_span:
                    try:
                        facts = get_system_profile(unpacked.tmp_dir)
                        sp_span.set_status(trace.StatusCode.OK)
                    except Exception as e:
                        sp_span.set_status(trace.StatusCode.ERROR, str(e))
                        sp_span.record_exception(e)
                        raise
                with tracer.start_as_current_span("puptoo.postprocess") as pp_span:
                    try:
                        facts = postprocess(facts)
                        pp_span.set_status(trace.StatusCode.OK)
                    except Exception as e:
                        pp_span.set_status(trace.StatusCode.ERROR, str(e))
                        pp_span.record_exception(e)
                        raise
            except Exception as e:
                logger.exception("Failed to extract facts: %s", str(e), extra=extra)
                facts["error"] = str(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                span.record_exception(e)
            else:
                span.set_status(trace.StatusCode.OK)
            return facts
