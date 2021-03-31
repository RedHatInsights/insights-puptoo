from src.puptoo.process import profile

CLIENT_TAGS = [
    {"key": "name", "value": "foo", "namespace": "insights-client"},
    {"key": "zone", "value": "bar", "namespace": "insights-client"},
    {"key": "location", "value": "nc", "namespace": "insights-client"}
]


SAT_TAGS = [
        {
            "namespace": "Satellite",
            "key": "foo",
            "value": "bar"
        },
        {
            "namespace": "Satellite",
            "key": "boop",
            "value": "beep"
        }
]


def test_format_tags():

    tags = profile.format_tags(SAT_TAGS)
    assert type(tags["satellite"]) == dict
    assert tags["satellite"]["foo"] == ["bar"]
    assert tags["satellite"]["boop"] == ["beep"]
    
    tags = profile.format_tags(CLIENT_TAGS)
    assert type(tags["insights-client"]) == dict
    assert tags["insights-client"]["name"] == ["foo"]
    assert tags["insights-client"]["zone"] == ["bar"]