import json
import os
import shutil

from src.puptoo.process.profile import _read_python_purls, get_system_profile


def _write(tmp_path, relpath, data, raw=None):
    """Write a collector output file under an archive root and return the root path."""
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(raw if raw is not None else json.dumps(data), encoding="utf-8")
    return str(tmp_path)


DEFAULT_REL = "data/insights_datasources/python_purls.json"


def test_reads_detector_object_shape(tmp_path):
    """The detector's list-of-objects shape (each with a "purl") is mapped, sorted + deduped."""
    data = [
        {"purl": "pkg:pypi/jinja2@2.11.3", "dist": "Jinja2"},
        {"purl": "pkg:pypi/requests@2.28.1", "dist": "requests"},
        {"purl": "pkg:pypi/jinja2@2.11.3"},  # duplicate
    ]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_python_purls(root) == [
        "pkg:pypi/jinja2@2.11.3",
        "pkg:pypi/requests@2.28.1",
    ]


def test_reads_plain_string_array_shape(tmp_path):
    """A plain JSON array of purl strings is accepted too."""
    data = ["pkg:pypi/b@2", "pkg:pypi/a@1", "pkg:pypi/a@1"]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_python_purls(root) == ["pkg:pypi/a@1", "pkg:pypi/b@2"]


def test_reads_jsonl_shape(tmp_path):
    """The datasource's JSONL output (one JSON object per line) is parsed, sorted + deduped."""
    jsonl = (
        '{"purl": "pkg:pypi/b@2", "dist": "b"}\n'
        '{"purl": "pkg:pypi/a@1", "dist": "a"}\n'
        '{"purl": "pkg:pypi/a@1", "dist": "a"}'  # duplicate
    )
    root = _write(tmp_path, DEFAULT_REL, None, raw=jsonl)
    assert _read_python_purls(root) == ["pkg:pypi/a@1", "pkg:pypi/b@2"]


def test_jsonl_skips_mangled_line(tmp_path):
    """The point of JSONL: a line dropped/mangled by redaction costs one record, not the inventory."""
    jsonl = (
        '{"purl": "pkg:pypi/a@1"}\n'
        '{"purl": "pkg:pypi/REDACTED  <- not valid json\n'
        '{"purl": "pkg:pypi/b@2"}'
    )
    root = _write(tmp_path, DEFAULT_REL, None, raw=jsonl)
    assert _read_python_purls(root) == ["pkg:pypi/a@1", "pkg:pypi/b@2"]


def test_json_suffix_candidate(tmp_path):
    """The no-suffix insights_commands/python_purls candidate is discovered."""
    data = ["pkg:pypi/a@1"]
    root = _write(tmp_path, "data/insights_commands/python_purls", data)
    assert _read_python_purls(root) == ["pkg:pypi/a@1"]


def test_recursive_glob_fallback(tmp_path):
    """A file placed in a non-standard archive location is still found via the glob fallback."""
    data = ["pkg:pypi/a@1"]
    root = _write(tmp_path, "some/unexpected/dir/python_purls.json", data)
    assert _read_python_purls(root) == ["pkg:pypi/a@1"]


def test_none_path_returns_none():
    assert _read_python_purls(None) is None


def test_missing_file_returns_none(tmp_path):
    assert _read_python_purls(str(tmp_path)) is None


def test_malformed_json_returns_none(tmp_path):
    """Invalid JSON must not raise; returns None so the rest of the profile still flows."""
    root = _write(tmp_path, DEFAULT_REL, None, raw="{not valid json")
    assert _read_python_purls(root) is None


def test_single_jsonl_object_is_one_record(tmp_path):
    """Under JSONL a single JSON object on one line is a valid one-record inventory (not 'wrong shape')."""
    root = _write(
        tmp_path, DEFAULT_REL, {"purl": "pkg:pypi/a@1"}
    )  # json.dumps(dict) -> one line
    assert _read_python_purls(root) == ["pkg:pypi/a@1"]


def test_empty_array_returns_none(tmp_path):
    root = _write(tmp_path, DEFAULT_REL, [])
    assert _read_python_purls(root) is None


def test_skips_non_string_and_empty_items(tmp_path):
    """Non-string / empty / malformed items are dropped; valid purls survive."""
    data = [
        "pkg:pypi/a@1",
        "",
        None,
        123,
        {"nope": "x"},
        {"purl": ""},
        {"purl": "pkg:pypi/b@2"},
    ]
    root = _write(tmp_path, DEFAULT_REL, data)
    assert _read_python_purls(root) == ["pkg:pypi/a@1", "pkg:pypi/b@2"]


def test_python_purls_flows_into_system_profile(tmp_path):
    """End-to-end wiring: a python_purls datasource file in a real archive lands in
    system_profile.python_purls through the actual puptoo profile pipeline."""
    src_archive = os.path.join(
        os.path.dirname(__file__), "..", "dev", "test-archives", "core-base"
    )
    dst = os.path.join(str(tmp_path), "archive")
    shutil.copytree(src_archive, dst)
    ds_dir = os.path.join(dst, "data", "insights_datasources")
    os.makedirs(ds_dir, exist_ok=True)
    with open(os.path.join(ds_dir, "python_purls.json"), "w") as fh:
        fh.write(
            '{"purl": "pkg:pypi/requests@2.28.1", "dist": "requests", "source": "dist-info", "installer": "pip"}'
        )
    facts = get_system_profile(dst)
    assert facts["system_profile"]["python_purls"] == ["pkg:pypi/requests@2.28.1"]
