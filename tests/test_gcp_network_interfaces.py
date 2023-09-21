from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

GCP_NIC_1 = """
[{
  "accessConfigs":[
     {
        "externalIp":"34.67.41.222",
        "type":"ONE_TO_ONE_NAT"
     }
  ],
  "dnsServers":[
     "169.254.169.254"
  ],
  "forwardedIps":[],
  "gateway":"10.128.0.1",
  "ip":"10.128.0.3",
  "ipAliases":[],
  "mac":"42:01:0a:80:00:03",
  "mtu":1460,
  "network":"projects/564421043971/networks/default",
  "subnetmask":"255.255.240.0",
  "targetInstanceIps":[]
}]
""".strip()

GCP_NIC_2 = """
[]
""".strip()

GCP_NIC_3 = """
[{
   "accessConfigs":[
      {
         "externalIp":"",
         "type":"ONE_TO_ONE_NAT"
      }
   ],
   "dnsServers":[
     "169.254.169.254"
  ]
}]
""".strip()

GCP_NIC_4 = """
[
   {
      "accessConfigs":[{
         "externalIp":"",
         "type":"ONE_TO_ONE_NAT"
      }]
   },
   {
      "accessConfigs":[{
         "externalIp":"34.67.41.222",
         "type":"ONE_TO_ONE_NAT"
      }]
   },
   {
      "accessConfigs":[{
         "externalIp":"",
         "type":"ONE_TO_ONE_NAT"
      }]
   }
]
""".strip()

def test_gcp_network_interfaces():
    input_data = InputData().add(Specs.gcp_network_interfaces, GCP_NIC_1)
    result = run_test(system_profile, input_data)
    assert result["public_ipv4_addresses"] == ["34.67.41.222"]

    input_data = InputData().add(Specs.gcp_network_interfaces, GCP_NIC_2)
    result = run_test(system_profile, input_data)
    assert result.get("public_ipv4_addresses") == None

    input_data = InputData().add(Specs.gcp_network_interfaces, GCP_NIC_3)
    result = run_test(system_profile, input_data)
    assert result.get("public_ipv4_addresses") == None

    input_data = InputData().add(Specs.gcp_network_interfaces, GCP_NIC_4)
    result = run_test(system_profile, input_data)
    assert result.get("public_ipv4_addresses") == ["34.67.41.222"]
