"""Unleash feature flag client for Puptoo.

Provides centralized feature flag management following the pattern
established in insights-host-inventory (lib/feature_flags.py). Since
Puptoo is not a Flask application, this module uses UnleashClient
directly instead of flask-unleash.

Usage:
    from .feature_flags import init_unleash, get_flag_value

    # At startup (in app.py main()):
    init_unleash()

    # When checking a flag (once flags are defined):
    if get_flag_value("puptoo.some-flag", org_id):
        ...
"""

import logging
from collections.abc import Mapping

from .utils import config

logger = logging.getLogger(config.APP_NAME)

_client = None

FLAG_FALLBACK_VALUES: dict[str, bool] = {}


def custom_fallback(feature_name: str, context: dict) -> bool:
    raise ConnectionError(
        f"Could not contact Unleash server, or feature toggle {feature_name} not found."
    )


def init_unleash() -> None:
    global _client

    if _client is not None:
        return

    if config.BYPASS_UNLEASH:
        logger.warning(
            "Unleash is bypassed (BYPASS_UNLEASH=true); "
            "feature flags will use fallback values"
        )
        return

    if not config.UNLEASH_TOKEN:
        logger.warning(
            "No Unleash API token provided; feature flags will use fallback values"
        )
        return

    from UnleashClient import UnleashClient

    _client = UnleashClient(
        url=config.UNLEASH_URL,
        app_name=config.APP_NAME,
        refresh_interval=config.UNLEASH_REFRESH_INTERVAL,
        cache_directory=config.UNLEASH_CACHE_DIR,
        custom_headers={"Authorization": config.UNLEASH_TOKEN},
    )
    _client.initialize_client()
    logger.info(
        "Unleash client initialized: url=%s app=%s refresh=%ds",
        config.UNLEASH_URL,
        config.APP_NAME,
        config.UNLEASH_REFRESH_INTERVAL,
    )


def _build_flag_context(org_id: str) -> dict[str, str]:
    return {"orgId": org_id}


def get_flag_value_and_fallback(
    flag_name: str, context: Mapping[str, str]
) -> tuple[bool, bool]:
    flag_value = FLAG_FALLBACK_VALUES[flag_name]
    using_fallback = True

    try:
        if _client is not None:
            flag_value = _client.is_enabled(
                flag_name, context=context, fallback_function=custom_fallback
            )
            using_fallback = False
    except ConnectionError:
        logger.warning(
            "Could not connect to Unleash or toggle %s not found; "
            "falling back to default value %s",
            flag_name,
            flag_value,
        )

    return flag_value, using_fallback


def get_flag_value(flag_name: str, org_id: str) -> bool:
    return get_flag_value_and_fallback(flag_name, _build_flag_context(org_id))[0]
