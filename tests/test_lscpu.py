from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

LSCPU_1 = """
Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                2
On-line CPU(s) list:   0,1
Thread(s) per core:    2
Core(s) per socket:    1
Socket(s):             1
NUMA node(s):          1
Vendor ID:             GenuineIntel
CPU family:            6
Model:                 60
Model name:            Intel Core Processor (Haswell, no TSX)
Stepping:              1
CPU MHz:               2793.530
BogoMIPS:              5587.06
Hypervisor vendor:     KVM
Virtualization type:   full
L1d cache:             32K
L1i cache:             32K
L2 cache:              4096K
NUMA node0 CPU(s):     0,1
""".strip()


def test_lscpu():
    input_data = InputData().add(Specs.lscpu, LSCPU_1)
    result = run_test(system_profile, input_data)
    assert result["cores_per_socket"] == 1
