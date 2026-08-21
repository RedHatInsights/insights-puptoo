"""Tests for the QPC config variables added to src.puptoo.utils.config.

RHINENG-29853 (TDD, this file) / RHINENG-27919 (implementation).
"""

import importlib

import pytest


def _reload_config(monkeypatch, env_overrides):
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)
    import src.puptoo.utils.config as config_mod

    importlib.reload(config_mod)
    return config_mod


def _reset_env(monkeypatch):
    for var in [
        "MAX_HOSTS_PER_REP",
        "HOSTS_TRANSFORMATION_ENABLED",
        "DISCOVERY_HOST_TTL",
        "SATELLITE_HOST_TTL",
        "BYPASS_PAYLOAD_EXPIRATION",
        "ENABLED_HANDLERS",
    ]:
        monkeypatch.delenv(var, raising=False)


def _cleanup_config(monkeypatch):
    """Leave the module in its default state so later tests/files that import it
    live (without reloading) don't inherit whatever override the previous test set.
    Mirrors `_cleanup_telemetry` in test_telemetry.py.
    """
    _reset_env(monkeypatch)
    import src.puptoo.utils.config as config_mod

    importlib.reload(config_mod)


# --- Defaults (no env vars set) ---


def test_max_hosts_per_rep_default(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.MAX_HOSTS_PER_REP == 10000


def test_hosts_transformation_enabled_default_true(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.HOSTS_TRANSFORMATION_ENABLED is True


def test_discovery_host_ttl_default(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.DISCOVERY_HOST_TTL == "29"


def test_satellite_host_ttl_default(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.SATELLITE_HOST_TTL == "29"


def test_bypass_payload_expiration_default_false(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.BYPASS_PAYLOAD_EXPIRATION is False


def test_enabled_handlers_default_none_accepts_all(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.ENABLED_HANDLERS is None


# --- Overrides via env var ---


def test_max_hosts_per_rep_override(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {"MAX_HOSTS_PER_REP": "500"})
    assert config_mod.MAX_HOSTS_PER_REP == 500
    assert isinstance(config_mod.MAX_HOSTS_PER_REP, int)
    _cleanup_config(monkeypatch)


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("false", False),
        ("False", False),
        ("no", False),
        ("true", True),
        ("yes", True),
        ("t", True),
        ("T", True),
        ("y", True),
    ],
)
def test_hosts_transformation_enabled_override(monkeypatch, env_value, expected):
    _reset_env(monkeypatch)
    config_mod = _reload_config(
        monkeypatch, {"HOSTS_TRANSFORMATION_ENABLED": env_value}
    )
    assert config_mod.HOSTS_TRANSFORMATION_ENABLED is expected
    _cleanup_config(monkeypatch)


def test_discovery_host_ttl_override(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {"DISCOVERY_HOST_TTL": "45"})
    assert config_mod.DISCOVERY_HOST_TTL == "45"
    _cleanup_config(monkeypatch)


def test_satellite_host_ttl_override(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {"SATELLITE_HOST_TTL": "60"})
    assert config_mod.SATELLITE_HOST_TTL == "60"
    _cleanup_config(monkeypatch)


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("true", True),
        ("yes", True),
        ("t", True),
        ("y", True),
        ("false", False),
        ("no", False),
    ],
)
def test_bypass_payload_expiration_override(monkeypatch, env_value, expected):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {"BYPASS_PAYLOAD_EXPIRATION": env_value})
    assert config_mod.BYPASS_PAYLOAD_EXPIRATION is expected
    _cleanup_config(monkeypatch)


def test_enabled_handlers_parses_comma_separated_list(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(
        monkeypatch, {"ENABLED_HANDLERS": "advisor,compliance,malware-detection"}
    )
    assert config_mod.ENABLED_HANDLERS == ["advisor", "compliance", "malware-detection"]
    _cleanup_config(monkeypatch)


def test_enabled_handlers_strips_whitespace(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(
        monkeypatch, {"ENABLED_HANDLERS": "advisor, compliance , qpc"}
    )
    assert config_mod.ENABLED_HANDLERS == ["advisor", "compliance", "qpc"]
    _cleanup_config(monkeypatch)


def test_enabled_handlers_single_value(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {"ENABLED_HANDLERS": "qpc"})
    assert config_mod.ENABLED_HANDLERS == ["qpc"]
    _cleanup_config(monkeypatch)


# --- log_config() picks up the new vars (AC: "Logged by log_config() when puptoo starts") ---


def test_log_config_logs_new_variables(monkeypatch, caplog):
    _reset_env(monkeypatch)
    config_mod = _reload_config(
        monkeypatch, {"ENABLED_HANDLERS": "qpc", "MAX_HOSTS_PER_REP": "5"}
    )

    with caplog.at_level("INFO", logger=config_mod.APP_NAME):
        config_mod.log_config()

    messages = " ".join(caplog.messages)
    for var_name in [
        "MAX_HOSTS_PER_REP",
        "HOSTS_TRANSFORMATION_ENABLED",
        "DISCOVERY_HOST_TTL",
        "SATELLITE_HOST_TTL",
        "BYPASS_PAYLOAD_EXPIRATION",
        "ENABLED_HANDLERS",
    ]:
        assert var_name in messages

    _cleanup_config(monkeypatch)


# --- No impact on existing config variables (AC) ---


def test_existing_config_variables_unaffected(monkeypatch):
    _reset_env(monkeypatch)
    config_mod = _reload_config(monkeypatch, {})
    assert config_mod.APP_NAME == "insights-puptoo"
    assert config_mod.GROUP_ID == "insights-puptoo"
    assert config_mod.INVENTORY_TOPIC == "platform.inventory.host-ingress"
    assert config_mod.KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE == 2097152
