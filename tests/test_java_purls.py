import json

from src.puptoo.process.profile import _read_java_purls


def _write(tmp_path, relpath, data, raw=None):
    """Write a collector output file under an archive root and return the root path."""
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(raw if raw is not None else json.dumps(data), encoding="utf-8")
    return str(tmp_path)


DEFAULT_REL = "data/insights_commands/lightwell_java_purls"


def test_reads_detector_object_shape(tmp_path):
    """The detector's list-of-objects shape (each with a "purl") is mapped, sorted + deduped."""
    data = [
        {"purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1", "name": "log4j-core"},
        {"purl": "pkg:maven/com.google.guava/guava@31.0", "name": "guava"},
        {"purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1"},  # duplicate
    ]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_java_purls(root) == [
        "pkg:maven/com.google.guava/guava@31.0",
        "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1",
    ]


def test_reads_plain_string_array_shape(tmp_path):
    """A plain JSON array of purl strings is accepted too."""
    data = ["pkg:maven/b/b@2", "pkg:maven/a/a@1", "pkg:maven/a/a@1"]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_java_purls(root) == ["pkg:maven/a/a@1", "pkg:maven/b/b@2"]


def test_json_suffix_candidate(tmp_path):
    """The .json variant of the collector filename is discovered."""
    data = ["pkg:maven/a/a@1"]
    root = _write(tmp_path, "data/insights_commands/lightwell_java_purls.json", data)
    assert _read_java_purls(root) == ["pkg:maven/a/a@1"]


def test_recursive_glob_fallback(tmp_path):
    """A file placed in a non-standard archive location is still found via the glob fallback."""
    data = ["pkg:maven/a/a@1"]
    root = _write(tmp_path, "some/unexpected/dir/lightwell_java_purls_v2.json", data)
    assert _read_java_purls(root) == ["pkg:maven/a/a@1"]


def test_none_path_returns_none():
    assert _read_java_purls(None) is None


def test_missing_file_returns_none(tmp_path):
    assert _read_java_purls(str(tmp_path)) is None


def test_malformed_json_returns_none(tmp_path):
    """Invalid JSON must not raise; returns None so the rest of the profile still flows."""
    root = _write(tmp_path, DEFAULT_REL, None, raw="{not valid json")
    assert _read_java_purls(root) is None


def test_wrong_top_level_shape_returns_none(tmp_path):
    """A JSON object (not a list) is an unexpected shape and yields None."""
    root = _write(tmp_path, DEFAULT_REL, {"purl": "pkg:maven/a/a@1"})
    assert _read_java_purls(root) is None


def test_empty_array_returns_none(tmp_path):
    root = _write(tmp_path, DEFAULT_REL, [])
    assert _read_java_purls(root) is None


def test_skips_non_string_and_empty_items(tmp_path):
    """Non-string / empty / malformed items are dropped; valid purls survive."""
    data = ["pkg:maven/a/a@1", "", None, 123, {"nope": "x"}, {"purl": ""}, {"purl": "pkg:maven/b/b@2"}]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_java_purls(root) == ["pkg:maven/a/a@1", "pkg:maven/b/b@2"]
