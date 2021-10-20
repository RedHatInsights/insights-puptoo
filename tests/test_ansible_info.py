from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

RPMS = """
ansible-tower-1.0.0-1.x86_64  Tue 14 Jul 2015 09:25:38 AEST   1398536494
catalog-worker-1.0.2-1.x86_64    Tue 14 Jul 2015 09:25:40 AEST   1390535634
automation-hub-1.0.3-1.x86_64       Wed 09 Nov 2016 14:52:01 AEDT   1446193355
automation-controller-1.0.1-1.x86_64   Wed 09 Nov 2016 14:52:01 AEDT   1446193355
""".strip()


def test_ansible_info():
    input_data = InputData().add(Specs.installed_rpms, RPMS)
    result = run_test(system_profile, input_data)
    assert result["ansible"]["hub_version"] == "1.0.3"
    assert result["ansible"]["catalog_worker_version"] == "1.0.2"
    assert result["ansible"]["controller_version"] == "1.0.0"
