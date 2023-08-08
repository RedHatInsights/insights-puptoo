from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

SAP_DATA = """
*********************************************************
SID , String , D89
SystemNumber , String , 88
InstanceName , String , HDB88
InstanceType , String , HANA Test
Hostname , String , lu0417
FullQualifiedHostname , String , lu0417.example.com
IPAddress , String , 10.0.0.88
SapVersionInfo , String , 749, patch 211, changelist 1754007
*********************************************************
SID , String , D90
SystemNumber , String , 90
InstanceName , String , HDB90
InstanceType , String , HANA Test
Hostname , String , hdb90
FullQualifiedHostname , String , hdb90.example.com
IPAddress , String , 10.0.0.90
SapVersionInfo , String , 749, patch 211, changelist 1754007
""".strip()

SAP_DATA_1 = """
*********************************************************
SID , String , D90
SystemNumber , String , 90
InstanceName , String , HDB90
InstanceType , String , HANA Test
Hostname , String , hdb90
FullQualifiedHostname , String , hdb90.example.com
IPAddress , String , 10.0.0.90
SapVersionInfo , String , 749, patch 211, changelist 1754007
""".strip()

HOSTNAME = """
lu0417.example.com
""".strip()

def test_sap():

    input_data = InputData()
    input_data.add(Specs.saphostctl_getcimobject_sapinstance, SAP_DATA)
    input_data.add(Specs.hostname, HOSTNAME)
    result = run_test(system_profile, input_data)
    
    expected_sap_object = {'instance_number': '88', 'sap_system': True, 'sids': ['D89']}
    assert result["sap_system"] == True
    assert result["sap_instance_number"] == '88'
    assert result["sap_sids"] == ['D89']
    assert result["sap"] == expected_sap_object


    input_data = InputData()
    input_data.add(Specs.saphostctl_getcimobject_sapinstance, SAP_DATA_1)
    input_data.add(Specs.hostname, HOSTNAME)
    result = run_test(system_profile, input_data)
    
    expected_sap_object = {'sap_system': True}
    assert result["sap_system"] == True
    assert result.get("sap_instance_number") == None
    assert result.get("sap_sids") == None
    assert result["sap"] == expected_sap_object



