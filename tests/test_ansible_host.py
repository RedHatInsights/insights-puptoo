from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

ANSIBLE_HOST = """
some-ansible-host
""".strip()


def test_ansible_host():
    input_data = InputData().add(Specs.ansible_host, ANSIBLE_HOST)
    result = run_test(system_profile, input_data)
    assert result["ansible_host"] == "some-ansible-host"
