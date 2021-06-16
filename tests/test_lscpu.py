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

LSCPU_2 = """
Architecture:        aarch64
Byte Order:          Little Endian
CPU(s):              4
On-line CPU(s) list: 0-3
Thread(s) per core:  1
Core(s) per cluster: 4
Socket(s):           1
Cluster(s):          1
NUMA node(s):        1
Vendor ID:           ARM
BIOS Vendor ID:      QEMU
Model:               1
Model name:          Neoverse-N1
BIOS Model name:     virt-4.2
Stepping:            r3p1
BogoMIPS:            50.00
NUMA node0 CPU(s):   0-3
Flags:               fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm lrcpc dcpop asimddp ssbs
""".strip()


def test_lscpu():
    input_data = InputData().add(Specs.lscpu, LSCPU_1)
    result = run_test(system_profile, input_data)
    assert result["cores_per_socket"] == 1

    input_data = InputData().add(Specs.lscpu, LSCPU_2)
    result = run_test(system_profile, input_data)
    assert result.get("cores_per_socket") is None
