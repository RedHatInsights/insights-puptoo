from src.puptoo.process.profile import _remove_empties, _remove_empty_string, _to_bool


def test_remove_empties_strips_none_and_empty():
    d = {"a": "value", "b": None, "c": "", "d": [], "e": {}, "f": 0, "g": False}
    result = _remove_empties(d)
    assert result == {"a": "value", "f": 0, "g": False}


def test_remove_empties_bypass_keys_preserves_empty():
    d = {"dnf_modules": [], "other": [], "keep": "yes"}
    result = _remove_empties(d, bypass_keys={"dnf_modules"})
    assert result == {"dnf_modules": [], "keep": "yes"}


def test_remove_empties_bypass_keys_preserves_none():
    d = {"dnf_modules": None, "other": None}
    result = _remove_empties(d, bypass_keys={"dnf_modules"})
    assert result == {"dnf_modules": None}


def test_remove_empty_string():
    assert _remove_empty_string(["a", "", "b", ""]) == ["a", "b"]
    assert _remove_empty_string([]) == []
    assert _remove_empty_string(["", ""]) == []
    assert _remove_empty_string(["valid"]) == ["valid"]


def test_to_bool():
    assert _to_bool("1") is True
    assert _to_bool("enabled") is True
    assert _to_bool("0") is False
    assert _to_bool("disabled") is False
    assert _to_bool("unknown") is None
