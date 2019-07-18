import requests
import logging

import config

from insights import extract, rule, make_metadata, run
from insights.util.canonical_facts import get_canonical_facts

logger = logging.getLogger(config.APP_NAME)

def get_archive(url):
    archive = requests.get(url)
    return archive

def extract(msg, extra):
    facts = {}
    try:
        with NamedTemporaryFile(delete=remove) as tf:
            tf.write(get_archive(msg["url"]))
            logger.info("extracting facts from %s", tf.name, extra=extra)
            with get_facts(tf.name) as ex:
                facts = get_canonical_facts(path=ex.tmp_dir)
                facts["system_profile"] get_system_profile(path=ex.tmp_dir)
    except Exception as e:
        logger.exception("Failed to extract facts: %s", e, extra=extra)
        facts["error"] = e
    else:
        # log seomething
        print("log somethign")
    finally:
        if facts["system_profile"].get("display_name"):
            facts["display_name"] = facts["system_profile"].get("display_name")
        groomed_facts = _remove_empties(_remove_bad_display_name(facts))
        return groomed_facts
