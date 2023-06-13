from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

SYSTEMCTLSTATUSALL = """
* redhat.test.com
    State: degraded
     Jobs: 0 queued
   Failed: 2 units
    Since: Thu 2021-09-23 12:03:43 UTC; 3h 7min ago
   CGroup: /
           |-user.slice
           | `-user-1000.slice
           |   |-user@1000.service

* proc-sys-fs-binfmt_misc.automount - Arbitrary Executable File Formats File System Automount Point
   Loaded: loaded (/usr/lib/systemd/system/proc-sys-fs-binfmt_misc.automount; static; vendor preset: disabled)
   Active: active (running) since Thu 2021-09-23 12:03:43 UTC; 3h 7min ago
    Where: /proc/sys/fs/binfmt_misc
     Docs: https://www.kernel.org/doc/html/latest/admin-guide/binfmt-misc.html
           https://www.freedesktop.org/wiki/Software/systemd/APIFileSystems

Sep 23 15:11:07 redhat.test.com systemd[1]: proc-sys-fs-binfmt_misc.automount: Automount point already active?
Sep 23 15:11:07 redhat.test.com systemd[1]: proc-sys-fs-binfmt_misc.automount: Got automount request for /proc/sys/fs/binfmt_mis
""".strip()

def test_systemctl_status():
    input_data = InputData().add(Specs.systemctl_status_all, SYSTEMCTLSTATUSALL)
    result = run_test(system_profile, input_data)
    
    assert result['systemd']['failed'] == 2
    assert result['systemd']['jobs_queued'] == 0
    assert result['systemd']['state'] == 'degraded'

