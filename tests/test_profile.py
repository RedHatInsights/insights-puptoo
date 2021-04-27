from src.puptoo.process import profile

CLIENT_TAGS = [
    {"key": "name", "value": "Foo", "namespace": "insights-client"},
    {"key": "zOne", "value": "bar", "namespace": "insights-client"},
    {"key": "locAtion", "value": "nc", "namespace": "Insights-client"},
]


SAT_TAGS = [
    {"namespace": "satellite", "key": "foo", "value": "bar"},
    {"namespace": "Satellite", "key": "Boop", "value": "beep"},
]


def test_format_tags():

    good_tags = {"satellite": {"foo": ["bar"], "boop": ["beep"]}}
    tags = profile.format_tags(SAT_TAGS)
    assert type(tags["satellite"]) == dict
    assert tags == good_tags

    good_tags = {"insights-client": {"name": ["foo"], "zone": ["bar"], "location": ["nc"]}}
    tags = profile.format_tags(CLIENT_TAGS)
    assert type(tags["insights-client"]) == dict
    assert tags == good_tags
