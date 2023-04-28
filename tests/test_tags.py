import json
import pytest
from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import format_tags, system_profile


TAGS = """
[{"namespace": "insights-client", "value": "testing123", "key": "group"}, {"namespace": "insights-client", "value": null, "key": "test_group"}]
""".strip()


@pytest.mark.parametrize(
    "input_tags, expected_tags",
    [
        ([{"namespace": "ns1", "key": "key1", "value": "value1"}], {"ns1": {"key1": ["value1"]}}),
        (
            [{"namespace": "insights-client", "key": "key1", "value": "value1"}],
            {"insights-client": {"key1": ["value1"]}},
        ),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": "value1"},
                {"namespace": "ns1", "key": "key1", "value": "value2"},
            ],
            {"ns1": {"key1": ["value1", "value2"]}},
        ),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": "value1"},
                {"namespace": "ns1", "key": "key1", "value": "value2"},
                {"namespace": "ns1", "key": "key2", "value": "value2"},
                {"namespace": "ns1", "key": "key2", "value": "value3"},
                {"namespace": "ns2", "key": "key2", "value": "value1"},
                {"namespace": "ns2", "key": "key2", "value": "value3"},
                {"namespace": "ns2", "key": "key3", "value": "value3"},
                {"namespace": "ns2", "key": "key3", "value": "value4"},
            ],
            {
                "ns1": {"key1": ["value1", "value2"], "key2": ["value2", "value3"]},
                "ns2": {"key2": ["value1", "value3"], "key3": ["value3", "value4"]},
            },
        ),
        ([{"key": "key1", "value": "value1"}], {"insights-client": {"key1": ["value1"]}}),
        ([{"namespace": "ns1", "key": "key1", "value": 1}], {"ns1": {"key1": ["1"]}}),
        ([{"namespace": "ns1", "key": "key1", "value": None}], {"ns1": {"key1": []}}),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": None},
                {"namespace": "ns1", "key": "key1", "value": "value1"},
            ],
            {"ns1": {"key1": ["value1"]}},
        ),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": "value1"},
                {"namespace": "ns1", "key": "key1", "value": None},
            ],
            {"ns1": {"key1": ["value1"]}},
        ),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": 1},
                {"namespace": "ns1", "key": "key1", "value": "2"},
                {"namespace": "ns1", "key": "key1", "value": None},
            ],
            {"ns1": {"key1": ["1", "2"]}},
        ),
        (
            [
                {"namespace": "ns1", "key": "key1", "value": 1},
                {"namespace": "ns1", "key": "key2", "value": "2"},
                {"namespace": "ns1", "key": "key3", "value": None},
            ],
            {"ns1": {"key1": ["1"], "key2": ["2"], "key3": []}},
        ),
    ],
    ids=[
        "simple",
        "simple-insights-client",
        "two-values",
        "complex",
        "no-namespace",
        "int-value",
        "null-value",
        "null-and-str-value",
        "str-and-null-value",
        "int-str-null-same-key",
        "int-str-null-different-keys",
    ],
)
def test_format_tags(input_tags, expected_tags):
    output_tags = format_tags(input_tags)
    assert output_tags == expected_tags


def test_tags():
    input_data = InputData().add(Specs.tags, TAGS)
    result = run_test(system_profile, input_data)
    assert result['tags'] == format_tags(json.loads(TAGS))
