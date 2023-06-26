from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

AWSPUBLICIPV4ADDRESSES = """
1.2.3.4
""".strip()

def test_aws_public_ipv4_addresses():
    input_data = InputData().add(Specs.aws_public_ipv4_addresses, AWSPUBLICIPV4ADDRESSES)
    result = run_test(system_profile, input_data)
    assert result["public_ipv4_addresses"] == ["1.2.3.4"]


