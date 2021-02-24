from contextlib import contextmanager
import logging
from tempfile import NamedTemporaryFile

import requests
from insights import extract as extract_archive
from insights.util.canonical_facts import get_canonical_facts

from .profile import get_system_profile, postprocess
from ..utils import config, metrics
logger = logging.getLogger(config.APP_NAME)


@metrics.GET_FILE.time()
def get_archive(url):
    archive = requests.get(url)
    return archive.content


@contextmanager
def unpacked_archive(msg, remove=True):
    """
    Simple ContextManager which is used to for automatically downloading + unpacking
    insights archive, and performing cleanup when needed.
    """
    metrics.extraction_count.inc()
    try:
        with NamedTemporaryFile(delete=remove) as tf:
            tf.write(get_archive(msg["url"]))
            tf.flush()
            with extract_archive(tf.name) as ex:
                yield ex
    finally:
        metrics.msg_processed.inc()
        metrics.extract_success.inc()


@metrics.EXTRACT.time()
def extract(msg, extra, remove=True):
    """
    Perform the extraction of canonical system facts and system profile.
    """
    facts = {"system_profile": {}}
    with unpacked_archive(msg, remove) as unpacked:
        try:
            facts = get_canonical_facts(unpacked.tmp_dir)
            facts['system_profile'] = get_system_profile(unpacked.tmp_dir)
        except Exception as e:
            logger.exception("Failed to extract facts: %s", str(e), extra=extra)
            facts["error"] = str(e)
        finally:
            facts = postprocess(facts)
            metrics.msg_processed.inc()
            metrics.extract_success.inc()
            return facts
