from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

CPU_INFO_1 = """
processor       : 0
vendor_id       : GenuineIntel
cpu family      : 6
model           : 45
model name      : Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz
stepping        : 2
microcode       : 1808
cpu MHz         : 2900.000
cache size      : 20480 KB
physical id     : 0
siblings        : 1
core id         : 0
cpu cores       : 1
apicid          : 0
flags           : fpu vme de pse tsc msr pae mce
address sizes   : 40 bits physical, 48 bits virtual
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs taa itlb_multihit

processor       : 1
vendor_id       : GenuineIntel
cpu family      : 6
model           : 45
model name      : Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz
stepping        : 2
microcode       : 1808
cpu MHz         : 2900.000
cache size      : 20480 KB
physical id     : 2
siblings        : 1
core id         : 0
cpu cores       : 1
apicid          : 2
flags           : fpu vme de pse tsc msr pae mce
address sizes   : 40 bits physical, 48 bits virtual
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs taa itlb_multihit
""".strip()


def test_cpuinfo():
    input_data = InputData().add(Specs.cpuinfo, CPU_INFO_1)
    result = run_test(system_profile, input_data)
    assert result["cpu_flags"] == ["fpu",
                                  "vme",
                                  "de",
                                  "pse",
                                  "tsc",
                                  "msr",
                                  "pae",
                                  "mce"]
    assert result["cpu_model"] == "Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz"
    assert result["number_of_cpus"] == 2
    assert result["number_of_sockets"] == 2
