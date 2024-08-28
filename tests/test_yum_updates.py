from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

YUM_UPDATES_LIST = """
{
    "basearch": "x86_64",
    "build_pkgcache": false,
    "metadata_time": "2024-08-14T05:26:57Z",
    "releasever": "8",
    "update_list": {
        "acl-0:2.2.53-1.el8.x86_64": {
            "available_updates": [
                {
                    "basearch": "x86_64",
                    "erratum": "RHBA-2024:3151",
                    "package": "acl-0:2.2.53-3.el8.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                }
            ]
        },
        "audit-0:3.0.7-4.el8.x86_64": {
            "available_updates": [
                {
                    "basearch": "x86_64",
                    "erratum": "RHBA-2023:7157",
                    "package": "audit-0:3.0.7-5.el8.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                },
                {
                    "basearch": "x86_64",
                    "erratum": "RHBA-2024:3173",
                    "package": "audit-0:3.1.2-1.el8.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                }
            ]
        },
        "kernel-0:4.18.0-477.27.1.el8_8.x86_64": {
            "available_updates": [
                {
                    "basearch": "x86_64",
                    "erratum": "RHSA-2023:7077",
                    "package": "kernel-0:4.18.0-513.5.1.el8_9.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                },
                {
                    "basearch": "x86_64",
                    "erratum": "RHSA-2023:7549",
                    "package": "kernel-0:4.18.0-513.9.1.el8_9.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                },
                {
                    "basearch": "x86_64",
                    "erratum": "RHSA-2024:3138",
                    "package": "kernel-0:4.18.0-553.el8_10.x86_64",
                    "releasever": "8",
                    "repository": "rhel-8-for-x86_64-baseos-rpms"
                }
            ]
        }
    }
}
""".strip()


def test_uname():
    input_data = InputData().add(Specs.yum_updates, YUM_UPDATES_LIST)
    result = run_test(system_profile, input_data)
    assert len(result["yum_updates"]["update_list"]) == 3
    pkg = result["yum_updates"]["update_list"]["audit-0:3.0.7-4.el8.x86_64"]
    assert pkg['available_updates'][0]["erratum"] == "RHBA-2023:7157"
    assert result["releasever"] == "8"
    assert result["basearch"] == "x86_64"
