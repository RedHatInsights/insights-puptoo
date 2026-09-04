"""Tests for the env-var feature flag backend (src.puptoo.feature_flags)."""

import pytest

from src.puptoo.feature_flags import (
    FLAG_ENV_VARS,
    FLAG_FALLBACK_VALUES,
    get_flag_value,
    get_flag_value_and_fallback,
    init_unleash,
)


class TestFlagDefaults:
    def test_qpc_processing_enabled_defaults_true(self):
        assert FLAG_FALLBACK_VALUES["puptoo.qpc-processing-enabled"] is True

    def test_qpc_org_migration_defaults_false(self):
        assert FLAG_FALLBACK_VALUES["puptoo.qpc-org-migration"] is False

    def test_qpc_hosts_transformation_defaults_false(self):
        assert FLAG_FALLBACK_VALUES["puptoo.qpc-hosts-transformation"] is False

    def test_get_flag_value_returns_fallback_when_env_unset(self, monkeypatch):
        for flag, default in FLAG_FALLBACK_VALUES.items():
            env_var = FLAG_ENV_VARS[flag]
            monkeypatch.delenv(env_var, raising=False)
            assert get_flag_value(flag, "org-1") is default


class TestEnvVarOverrides:
    def test_processing_enabled_can_be_disabled(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "false")
        assert get_flag_value("puptoo.qpc-processing-enabled", "org-1") is False

    def test_processing_enabled_can_be_enabled(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "true")
        assert get_flag_value("puptoo.qpc-processing-enabled", "org-1") is True

    def test_hosts_transformation_can_be_enabled(self, monkeypatch):
        monkeypatch.setenv("HOSTS_TRANSFORMATION_ENABLED", "true")
        assert get_flag_value("puptoo.qpc-hosts-transformation", "org-1") is True

    def test_org_migration_can_be_enabled(self, monkeypatch):
        monkeypatch.setenv("QPC_ORG_MIGRATION_ENABLED", "yes")
        assert get_flag_value("puptoo.qpc-org-migration", "org-1") is True

    def test_truthy_values_all_accepted(self, monkeypatch):
        for val in ("true", "True", "TRUE", "t", "yes", "y", "1"):
            monkeypatch.setenv("QPC_PROCESSING_ENABLED", val)
            assert get_flag_value("puptoo.qpc-processing-enabled", "org-1") is True

    def test_falsy_values_all_rejected(self, monkeypatch):
        for val in ("false", "False", "FALSE", "f", "no", "n", "0", ""):
            monkeypatch.setenv("QPC_PROCESSING_ENABLED", val)
            assert get_flag_value("puptoo.qpc-processing-enabled", "org-1") is False


class TestGetFlagValueAndFallback:
    def test_returns_env_value_not_using_fallback(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "false")
        value, using_fallback = get_flag_value_and_fallback(
            "puptoo.qpc-processing-enabled", {}
        )
        assert value is False
        assert using_fallback is False

    def test_returns_fallback_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("QPC_PROCESSING_ENABLED", raising=False)
        value, using_fallback = get_flag_value_and_fallback(
            "puptoo.qpc-processing-enabled", {}
        )
        assert value is True
        assert using_fallback is True

    def test_org_id_does_not_affect_result(self, monkeypatch):
        monkeypatch.setenv("QPC_PROCESSING_ENABLED", "false")
        assert get_flag_value("puptoo.qpc-processing-enabled", "org-A") is False
        assert get_flag_value("puptoo.qpc-processing-enabled", "org-B") is False

    def test_unknown_flag_raises_key_error(self):
        with pytest.raises(KeyError):
            get_flag_value("puptoo.nonexistent-flag", "org-1")


class TestInitUnleash:
    def test_is_noop_and_does_not_raise(self):
        init_unleash()

    def test_repeated_calls_do_not_raise(self):
        init_unleash()
        init_unleash()
