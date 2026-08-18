from src.puptoo.modifiers.qpc.transform_cloud_provider import TransformCloudProvider


def test_transform_cloud_provider():
    host = {"system_profile": {"cloud_provider": "google"}}
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformCloudProvider().run(host, transformed_obj)
    assert host == {"system_profile": {"cloud_provider": "gcp"}}


def test_cloud_provider_transform_method_for_non_cloud():
    host = {
        "fqdn": "virt-who-samplevpa11.mtn.co.za-1",
        "system_profile": {"infrastructure_type": "physical"},
    }
    transformed_obj = {"removed": [], "modified": [], "missing_data": []}
    TransformCloudProvider().run(host, transformed_obj)
    assert host == {
        "fqdn": "virt-who-samplevpa11.mtn.co.za-1",
        "system_profile": {"infrastructure_type": "physical"},
    }
