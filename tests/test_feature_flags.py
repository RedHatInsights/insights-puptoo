"""Tests for the Unleash feature flags module (src.puptoo.feature_flags)."""

import importlib
from unittest.mock import MagicMock, patch

import pytest

TEST_FEATURE_FLAG = "puptoo.test-feature"


def _reload_modules(monkeypatch, env_overrides):
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)
    import src.puptoo.utils.config as config_mod
    import src.puptoo.feature_flags as ff_mod

    importlib.reload(config_mod)
    importlib.reload(ff_mod)
    return ff_mod


def _cleanup(monkeypatch):
    monkeypatch.setenv("BYPASS_UNLEASH", "true")
    monkeypatch.setenv("UNLEASH_TOKEN", "")
    import src.puptoo.utils.config as config_mod
    import src.puptoo.feature_flags as ff_mod

    importlib.reload(config_mod)
    importlib.reload(ff_mod)


# --- init_unleash ---


def test_init_unleash_skips_when_bypass_is_true(monkeypatch):
    ff_mod = _reload_modules(monkeypatch, {"BYPASS_UNLEASH": "true"})

    ff_mod._client = None
    ff_mod.init_unleash()
    assert ff_mod._client is None


def test_init_unleash_skips_when_token_empty(monkeypatch):
    ff_mod = _reload_modules(
        monkeypatch, {"BYPASS_UNLEASH": "false", "UNLEASH_TOKEN": ""}
    )

    ff_mod._client = None
    ff_mod.init_unleash()
    assert ff_mod._client is None

    _cleanup(monkeypatch)


def test_init_unleash_creates_client_when_configured(monkeypatch):
    ff_mod = _reload_modules(
        monkeypatch,
        {
            "BYPASS_UNLEASH": "false",
            "UNLEASH_TOKEN": "test-token",
            "UNLEASH_URL": "http://localhost:4242/api",
        },
    )

    ff_mod._client = None

    with patch("UnleashClient.UnleashClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance
        ff_mod.init_unleash()

        MockClient.assert_called_once()
        mock_instance.initialize_client.assert_called_once()
        assert ff_mod._client is mock_instance

    ff_mod._client = None
    _cleanup(monkeypatch)


def test_init_unleash_idempotent():
    import src.puptoo.feature_flags as ff_mod

    sentinel = MagicMock()
    ff_mod._client = sentinel
    ff_mod.init_unleash()
    assert ff_mod._client is sentinel
    ff_mod._client = None


# --- custom_fallback ---


def test_custom_fallback_raises_connection_error():
    from src.puptoo.feature_flags import custom_fallback

    with pytest.raises(ConnectionError, match="feature toggle"):
        custom_fallback("some.flag", {})


# --- get_flag_value_and_fallback ---


@patch.dict("src.puptoo.feature_flags.FLAG_FALLBACK_VALUES", {TEST_FEATURE_FLAG: False})
def test_flag_value_from_unleash():
    import src.puptoo.feature_flags as ff_mod

    mock_client = MagicMock()
    mock_client.is_enabled.return_value = True
    ff_mod._client = mock_client

    value, using_fallback = ff_mod.get_flag_value_and_fallback(TEST_FEATURE_FLAG, {})
    assert value is True
    assert using_fallback is False

    ff_mod._client = None


@patch.dict("src.puptoo.feature_flags.FLAG_FALLBACK_VALUES", {TEST_FEATURE_FLAG: False})
def test_flag_fallback_on_connection_error():
    import src.puptoo.feature_flags as ff_mod

    mock_client = MagicMock()
    mock_client.is_enabled.side_effect = ConnectionError("boom")
    ff_mod._client = mock_client

    value, using_fallback = ff_mod.get_flag_value_and_fallback(TEST_FEATURE_FLAG, {})
    assert value is False
    assert using_fallback is True

    ff_mod._client = None


@patch.dict("src.puptoo.feature_flags.FLAG_FALLBACK_VALUES", {TEST_FEATURE_FLAG: False})
def test_flag_fallback_when_client_is_none():
    import src.puptoo.feature_flags as ff_mod

    ff_mod._client = None
    value, using_fallback = ff_mod.get_flag_value_and_fallback(TEST_FEATURE_FLAG, {})
    assert value is False
    assert using_fallback is True


# --- get_flag_value ---


@patch.dict("src.puptoo.feature_flags.FLAG_FALLBACK_VALUES", {TEST_FEATURE_FLAG: False})
def test_get_flag_value_builds_context_from_org_id():
    import src.puptoo.feature_flags as ff_mod

    mock_client = MagicMock()
    mock_client.is_enabled.return_value = True
    ff_mod._client = mock_client

    result = ff_mod.get_flag_value(TEST_FEATURE_FLAG, "1234567")
    assert result is True

    call_args = mock_client.is_enabled.call_args
    assert call_args[1]["context"] == {"orgId": "1234567"}

    ff_mod._client = None


# --- _build_flag_context ---


def test_build_flag_context():
    from src.puptoo.feature_flags import _build_flag_context

    ctx = _build_flag_context("org-42")
    assert ctx == {"orgId": "org-42"}


def test_get_flag_value_raises_on_unregistered_flag():
    import src.puptoo.feature_flags as ff_mod

    with pytest.raises(KeyError):
        ff_mod.get_flag_value("puptoo.not-registered", "org-1")
