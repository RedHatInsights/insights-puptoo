import json
from insights.specs import Specs
from insights.tests import InputData, run_test
from insights.tests import context_wrap
from insights.parsers.branch_info import BranchInfo
from src.puptoo.process.profile import format_tags,system_profile


BRANCH_INFO_1 = """
{"remote_leaf": "9b53c93a-88ea-4168-9edf-b58e6c2ba66d", "remote_branch": "a3c84dea-6992-49a5-bdef-62cdc69b0ddc", "display_name": "EXD", "hostname": "sat-server-01.hosts.prod.psi.pek2.redhat.com", "product": {"type": "Satellite", "major_version": "6", "minor_version": "11"}, "organization_id": 1, "satellite_instance_id": "ab11b6cc-5816-47c3-9d14-e459db9f4462", "labels": [{"namespace": "satellite", "key": "location", "value": "PEK2"}, {"namespace": "satellite", "key": "location", "value": "PEK2"}, {"namespace": "satellite", "key": "hostgroup", "value": "exd"}, {"namespace": "satellite", "key": "hostgroup", "value": "rhv"}, {"namespace": "satellite", "key": "hostgroup", "value": "psi_rhv-01_vms"}, {"namespace": "satellite", "key": "hostgroup", "value": "exd/rhv/psi_rhv-01_vms"}, {"namespace": "satellite", "key": "organization", "value": "EXD"}, {"namespace": "satellite", "key": "lifecycle_environment", "value": "Library"}, {"namespace": "satellite", "key": "content_view", "value": "Default Organization View"}, {"namespace": "satellite", "key": "activation_key", "value": "exd-default"}, {"namespace": "satellite", "key": "satellite_instance_id", "value": "ab11b6cc-5816-47c3-9d14-e459db9f4462"}, {"namespace": "satellite", "key": "organization_id", "value": "1"}]}
""".strip()

BRANCH_INFO_2 = """
{"remote_branch": -1, "remote_leaf": -1}
""".strip()

def test_branch_info():
    input_data = InputData().add(Specs.branch_info, BRANCH_INFO_1)
    result = run_test(system_profile, input_data)
    del result['tags']['insights-client']
    assert result['satellite_managed'] == True
    assert result['satellite_id'] == "9b53c93a-88ea-4168-9edf-b58e6c2ba66d"
    assert result['tags'] == format_tags((json.loads(BRANCH_INFO_1))['labels'])

    input_data = InputData().add(Specs.branch_info, BRANCH_INFO_2)
    result = run_test(system_profile, input_data)
    assert result['satellite_managed'] == False