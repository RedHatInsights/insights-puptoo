from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.mq import msgs

from src.puptoo.process.profile import system_profile

DATA_0 = """
{
    "version": "1.0.0",
    "idHash": "e38277334d0f6b6fdc6f3b831fb102cdd70f04faab5c38b0be36fb1aacb4236e",
    "basic": {
        "app.user.dir": "/opt/t_eap/jboss-eap-7.4",
        "java.specification.version": "1.8",
        "java.runtime.version": "1.8.0_362-b09",
        "java.class.path": "/opt/t_eap/jboss-eap-7.4/jboss-modules.jar",
        "system.os.version": "4.18.0-425.13.1.el8_7.x86_64",
        "jvm.args": [
            "-D[Standalone]",
            "-verbose:gc",
            "-Xloggc:/opt/t_eap/jboss-eap-7.4/standalone/log/gc.log",
            "-Djboss.modules.system.pkgs=org.jboss.byteman",
            "-Dorg.jboss.boot.log.file=/opt/t_eap/jboss-eap-7.4/standalone/log/server.log",
            "-Dlogging.configuration=file:/opt/t_eap/jboss-eap-7.4/standalone/configuration/logging.properties"
            ]
        }
}
""".strip()

def test_is_runtimes():

    input_data = InputData().add(Specs.eap_json_reports, None)
    result = run_test(system_profile, input_data)
    assert result.get("is_runtimes") == None

    input_data = InputData().add(Specs.eap_json_reports, DATA_0)
    result = run_test(system_profile, input_data)
    assert result.get("is_runtimes") == True

    operation = "add_host"
    data = {
                "insights_id": "cdbd-2e23-cdef-1234",
                "fqdn": "something.example.com",
                "ip_addresses": ["192.168.0.1", "127.0.0.1"],
                "bios_uuid": "12335kjlj"
           }
    metadata = {
                    "account": "123456",
                    "org_id": "654321",
                    "request_id": "abcd-1234",
                    "is_runtimes": result["is_runtimes"]
               }

    message = msgs.inv_message(operation, data, metadata)
    assert message["platform_metadata"]["is_runtimes"] == True
