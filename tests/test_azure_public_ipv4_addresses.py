from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

AZURE_DATA = """
{
  "loadbalancer": {
    "publicIpAddresses": [
      {
        "frontendIpAddress": "137.116.118.209",
        "privateIpAddress": "10.0.0.4"
      }
    ],
    "inboundRules": [],
    "outboundRules": []
  }
}
""".strip()

def test_azure_public_ipv4_addresses():
    input_data = InputData().add(Specs.azure_load_balancer, AZURE_DATA)
    result = run_test(system_profile, input_data)
    assert result["public_ipv4_addresses"] == ["137.116.118.209"]

