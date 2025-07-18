from contextlib import contextmanager
import logging
from tempfile import NamedTemporaryFile
from pathlib import Path

import requests
from insights import extract as extract_archive

from .profile import get_system_profile, postprocess
from ..utils import config, metrics
logger = logging.getLogger(config.APP_NAME)


@metrics.GET_FILE.time()
def get_archive(url):
    archive = requests.get(url)
    return archive.content


def validate_size(path, extra):
    """
    reject payloads where the extracted size exceeds the configured max
    """
    total_size = sum(p.stat().st_size for p in Path(path).rglob('*'))
    metrics.msg_extraction_size.observe(total_size)
    if total_size >= int(config.MAX_EXTRACTED_SIZE):
        metrics.msg_size_exceeded.inc()
        logger.info(
            "Unpacked archive exceeds extracted file size limit of %s, request_id: %s",
            config.MAX_EXTRACTED_SIZE,
            extra["request_id"]
        )
        # TODO: actively reject payloads that exceed our configured max size
    elif total_size >= int(config.MAX_EXTRACTED_SIZE_L2):
        # Request for debugging usage in insights-engine
        logger.info(
            "Unpacked archive exceeds extracted file size limit of %s (but within limit %s), request_id: %s",
            config.MAX_EXTRACTED_SIZE_L2,
            config.MAX_EXTRACTED_SIZE,
            extra["request_id"]
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
    facts = {"system_profile": {}}
    with unpacked_archive(msg, remove) as (unpacked, err):
        if err:
            logger.exception("Failed to extract archive: %s", str(err), extra=extra)
            facts["error"] = str(err)
            return facts

        try:
            validate_size(unpacked.tmp_dir, extra)
            # extract canonical_facts and system_profile in one go
            facts = get_system_profile(unpacked.tmp_dir)
            facts = postprocess(facts)
        except Exception as e:
            logger.exception("Failed to extract facts: %s", str(e), extra=extra)
            facts["error"] = str(e)
        return facts
