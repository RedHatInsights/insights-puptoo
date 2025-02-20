from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

PS_AUXCWW_IBM_DB2 = """
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  19356  1544 ?        Ss   May31   0:01 init
root      1821  0.0  0.0      0     0 ?        S    May31   0:29 kondemand/0
root     20357  0.0  0.0   9120   832 ?        Ss   10:09   0:00 dhclient
root      1821  0.0  0.0      0     0 ?        S    May31   0:25 [kondemand/0]
dbp1    161530  0.1  1.3 2306928 314076 ?      Sl   Apr19   8:42 db2sysc
dbp2    161531  0.1  1.3 2306928 314076 ?      Sl   Apr19   8:42 db2sysc
root    161532  0.1  1.3 2306928 314076 ?      Sl   Apr19   8:42 db2sysc
""".strip()

PS_AUXCWW_ORACLE_DB = """
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  19356  1544 ?        Ss   May31   0:01 init
oracle   25673  5.4  0.2 255468 32960 pts/2    S+   13:35   0:04 ora_pmon_XXXX
oracle   25058  0.3  1.2 1042992 146352 tty2   Sl+  13:02   0:07 ora_smon_YYYY
root      1821  0.0  0.0      0     0 ?        S    May31   0:25 [kondemand/0]
""".strip()

PS_AUXCWW_NO_DB = """
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  19356  1544 ?        Ss   May31   0:01 init
root      1821  0.0  0.0      0     0 ?        S    May31   0:29 kondemand/0
root     20357  0.0  0.0   9120   832 ?        Ss   10:09   0:00 dhclient
""".strip()


def test_db_workloads():

    input_data = InputData()
    input_data.add(Specs.ps_auxcww, PS_AUXCWW_IBM_DB2)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["ibm_db2"] == {"is_running": True}

    input_data = InputData()
    input_data.add(Specs.ps_auxcww, PS_AUXCWW_ORACLE_DB)
    result = run_test(system_profile, input_data)
    assert result["workloads"]["oracle_db"] == {"is_running": True}

    input_data = InputData()
    input_data.add(Specs.ps_auxcww, PS_AUXCWW_NO_DB)
    result = run_test(system_profile, input_data)
    assert "workloads" not in result
