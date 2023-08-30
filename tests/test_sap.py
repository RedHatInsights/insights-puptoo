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

SAP_DATA_2 = """
*********************************************************
 CreationClassName , String , SAPInstance
 SID , String , R4D
 SystemNumber , String , 12
 InstanceName , String , DVEBMGS12
 InstanceType , String , ABAP Instance
 Hostname , String , ####
 FullQualifiedHostname , String , data.com
 SapVersionInfo , String , 753, patch 1017, changelist 2134118
*********************************************************
 CreationClassName , String , SAPInstance
 SID , String , R4D
 SystemNumber , String , 10
 InstanceName , String , ASCS10
 InstanceType , String , Central Services Instance
 Hostname , String , ####
 FullQualifiedHostname , String , data.com
 SapVersionInfo , String , 753, patch 1017, changelist 2134118
*********************************************************
 CreationClassName , String , SAPInstance
 SID , String , WDX
 SystemNumber , String , 20
 InstanceName , String , W20
 InstanceType , String , Webdispatcher Instance
 Hostname , String , ####
 FullQualifiedHostname , String , svcz.example.com
 SapVersionInfo , String , 777, patch 435, changelist 2114624
*********************************************************
 CreationClassName , String , SAPInstance
 SID , String , SMD
 SystemNumber , String , 97
 InstanceName , String , SMDA97
 InstanceType , String , Solution Manager Diagnostic Agent
 Hostname , String , ####
 FullQualifiedHostname , String , svcz.example.com
 SapVersionInfo , String , 745, patch 400, changelist 1734487
*********************************************************
 CreationClassName , String , SAPInstance
 SID , String , SMD
 SystemNumber , String , 98
 InstanceName , String , SMDA98
 InstanceType , String , Solution Manager Diagnostic Agent
 Hostname , String , ####
 FullQualifiedHostname , String , svcz.example.com
 SapVersionInfo , String , 745, patch 400, changelist 1734487
""".strip()

SAP_DATA_3 = """
*********************************************************
 CreationClassName , String , SAPInstance 
 SID , String , SMA 
 SystemNumber , String , 93 
 InstanceName , String , SMDA93 
 InstanceType , String , Solution Manager Diagnostic Agent 
 Hostname , String , hag 
 FullQualifiedHostname , String , hag.example.com
 SapVersionInfo , String , 749, patch 200, changelist 1746260 
""".strip()

HOSTNAME = "lu0417.example.com"
HOSTNAME_2 = "svcz.example.com"
HOSTNAME_3 = "hag.example.com"


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

    expected_sap_object = {'sap_system': False}
    assert result["sap_system"] == False
    assert result.get("sap_instance_number") == None
    assert result.get("sap_sids") == None
    assert result["sap"] == expected_sap_object


    input_data = InputData()
    input_data.add(Specs.saphostctl_getcimobject_sapinstance, SAP_DATA_3)
    input_data.add(Specs.hostname, HOSTNAME_3)
    result = run_test(system_profile, input_data)

    expected_sap_object = {'sap_system': False}
    assert result["sap_system"] == False
    assert result.get("sap_instance_number") == None
    assert result.get("sap_sids") == None
    assert result["sap"] == expected_sap_object
    

    input_data = InputData()
    input_data.add(Specs.saphostctl_getcimobject_sapinstance, SAP_DATA_2)
    input_data.add(Specs.hostname, HOSTNAME_2)
    result = run_test(system_profile, input_data)

    expected_sap_object = {'instance_number': '20', 'sap_system': True, 'sids': ['WDX']}
    assert result["sap_system"] == True
    assert result["sap_instance_number"] == '20'
    assert result["sap_sids"] == ['WDX']
    assert result["sap"] == expected_sap_object
