"""Feature flag module — env-var backend (interim).

Unleash SDK is disabled while the Konflux EC exception for yggdrasil-engine
(shipped by unleashclient) is pending. To restore the Unleash backend, replace
this file with the version from branch
RHINENG-29362/2.7-add-qpc-unleash-feature-flags and re-add unleashclient==6.8.0
to pyproject.toml + run `uv lock`. No call-site changes required.

Usage:
    from .feature_flags import init_unleash, get_flag_value

    # At startup (in app.py main()):
    init_unleash()

    # When checking a flag:
    if get_flag_value("puptoo.some-flag", org_id):
        ...
"""

import logging
import os
from collections.abc import Mapping

from .utils import config

logger = logging.getLogger(config.APP_NAME)

FLAG_FALLBACK_VALUES: dict[str, bool] = {
    "puptoo.qpc-processing-enabled": True,
    "puptoo.qpc-org-migration": False,
    "puptoo.qpc-hosts-transformation": False,
}

# Maps each flag to the env var that overrides its hardcoded default.
# org_id-based per-org routing is not available without Unleash —
# all orgs share the same value. Restore the Unleash backend for per-org targeting.
FLAG_ENV_VARS: dict[str, str] = {
    "puptoo.qpc-processing-enabled": "QPC_PROCESSING_ENABLED",
    "puptoo.qpc-org-migration": "QPC_ORG_MIGRATION_ENABLED",
    "puptoo.qpc-hosts-transformation": "HOSTS_TRANSFORMATION_ENABLED",
}

_TRUTHY = frozenset(("true", "t", "yes", "y", "1"))


def init_unleash() -> None:
    """No-op — Unleash SDK disabled pending EC exception for yggdrasil-engine."""
    logger.warning(
        "Unleash client disabled (EC exception for yggdrasil-engine pending); "
        "feature flags are controlled by environment variables"
    )


def _read_env_flag(flag_name: str) -> bool | None:
    env_var = FLAG_ENV_VARS.get(flag_name)
    if env_var is None:
        return None
    raw = os.getenv(env_var)
    if raw is None:
        return None
    return raw.lower() in _TRUTHY


def get_flag_value_and_fallback(
    flag_name: str, _context: Mapping[str, str]
) -> tuple[bool, bool]:
    env_value = _read_env_flag(flag_name)
    if env_value is not None:
        return env_value, False
    return FLAG_FALLBACK_VALUES[flag_name], True


def get_flag_value(flag_name: str, org_id: str) -> bool:
    return get_flag_value_and_fallback(flag_name, {"orgId": org_id})[0]
