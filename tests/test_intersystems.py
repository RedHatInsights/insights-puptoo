from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

IRIS_LIST = """

Configuration 'IRIS1'   (default)
    directory:    /intersystems1
    versionid:    2023.1.0.235.1com
    datadir:      /intersystems1
    conf file:    iris.cpf  (SuperServer port = 1972, WebServer = 52773)
    status:       running, since Tue Jun 27 01:55:25 2023
    state:        ok
    product:      InterSystems IRIS
Configuration 'IRIS2'   (default)
    directory:    /intersystems2
    versionid:    2023.1.0.235.1com
    datadir:      /intersystems2
    conf file:    iris.cpf  (SuperServer port = 1972, WebServer = 52773)
    status:       running, since Tue Jun 27 01:55:25 2023
    state:        ok
    product:      InterSystems IRIS
Configuration 'IRIS3'   (default)
    directory:    /intersystems3
    versionid:    2023.1.0.235.1com
    datadir:      /intersystems3
    conf file:    iris.cpf  (SuperServer port = 1972, WebServer = 52773)
    status:       down, since Tue Jun 27 01:55:25 2023
    state:        ok
    product:      InterSystems IRIS
""".strip()

IRIS_LIST_EMPTY_INSTANCE_NAME = """

Configuration   (default)
    directory:    /intersystems1
    versionid:    2023.1.0.235.1com
    datadir:      /intersystems1
    conf file:    iris.cpf  (SuperServer port = 1972, WebServer = 52773)
    status:       running, since Tue Jun 27 01:55:25 2023
    state:        ok
    product:      InterSystems IRIS
"""

IRIS_CPF_1 = """
[ConfigFile]
Product=IRIS
Version=2023.1
""".strip()

IRIS_CPF_2 = """
[ConfigFile]
Product=IRIS
Version=2023.2
""".strip()

IRIS_CPF_3 = """
[ConfigFile]
NotProduct=IRIS
NotVersion=2023.2
""".strip()


def test_intersystems():

    # As a valid Intersystems system, with running instance
    input_data = InputData()
    input_data.add(Specs.iris_list, IRIS_LIST)
    input_data.add(Specs.iris_cpf, IRIS_CPF_1, path="/intersystems1/iris.cpf")
    input_data.add(Specs.iris_cpf, IRIS_CPF_2, path="/intersystems2/iris.cpf")
    input_data.add(Specs.iris_cpf, IRIS_CPF_2, path="/intersystems3/iris.cpf")
    result = run_test(system_profile, input_data)
    assert result["workloads"]["intersystems"] == {
        "is_intersystems": True,
        "running_instances": [
            {
                "instance_name": "IRIS1",
                "product": "IRIS",
                "version": "2023.1"
            },
            {
                "instance_name": "IRIS2",
                "product": "IRIS",
                "version": "2023.2"
            }
        ]
    }

    # As a valid Intersystems system, but no running instance - 1
    input_data = InputData()
    input_data.add(Specs.iris_list, IRIS_LIST)
    input_data.add(Specs.iris_cpf, IRIS_CPF_2, path="/intersystems3/iris.cpf")
    result = run_test(system_profile, input_data)
    assert result["workloads"]["intersystems"] == {
        "is_intersystems": True
    }

    # As a valid Intersystems system, but no running instance - 2
    input_data = InputData()
    input_data.add(Specs.iris_list, IRIS_LIST)
    input_data.add(Specs.iris_cpf, IRIS_CPF_3, path="/intersystems2/iris.cpf")
    result = run_test(system_profile, input_data)
    assert result["workloads"]["intersystems"] == {
        "is_intersystems": True
    }

    # Not as a valid Intersystems system
    input_data = InputData()
    input_data.add(Specs.iris_list, "")
    input_data.add(Specs.iris_cpf, "", path="/intersystems1/iris.cpf")
    result = run_test(system_profile, input_data)
    assert "workloads" not in result
