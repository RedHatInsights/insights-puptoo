from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

PMLOG_SUMMARY_OUTPUT = """
disk.dev.total ["vda"] 1.245 count / sec
hinv.ncpu  2.000 none
kernel.all.cpu.idle  1.984 none
mem.physmem  4638616.000 Kbyte
mem.util.available  3493705.629 Kbyte
""".strip()

PCP_RAW_DATA_FAKE_FILE = "some fake content"

INSIGHTS_CLIENT_CONF_ROS_COLLECT_HIT = """
[insights-client]
#authmethod=BASIC
# username to use when authmethod is BASIC
# password ******** use when authmethod is BASIC
#auto_update=True
#core_collect=True
ros_collect=True
""".strip()

INSIGHTS_CLIENT_CONF_ROS_COLLECT_UNHIT_1 = """
[insights-client]
#authmethod=BASIC
# username to use when authmethod is BASIC
# password ******** use when authmethod is BASIC
#auto_update=True
#core_collect=True
""".strip()

INSIGHTS_CLIENT_CONF_ROS_COLLECT_UNHIT_2 = """
[some-other-section]
#authmethod=BASIC
# username to use when authmethod is BASIC
# password ******** use when authmethod is BASIC
#auto_update=True
#core_collect=True
""".strip()


def test_ros():
    # ### test for old collection way ###

    input_data = InputData("test_pmlog_summary")
    input_data.add(Specs.pmlog_summary, PMLOG_SUMMARY_OUTPUT)
    result = run_test(system_profile, input_data)
    assert result["is_ros"] is True
    assert result["is_pcp_raw_data_collected"] is False

    # ### test for new collection way ###

    input_data = InputData("test_pmlog_summary_pcp_zeroconf_only")
    input_data.add(Specs.pmlog_summary_pcp_zeroconf, PMLOG_SUMMARY_OUTPUT)
    result = run_test(system_profile, input_data)
    assert result["is_ros"] is True
    assert result["is_pcp_raw_data_collected"] is False

    input_data = InputData("test_pmlog_summary_pcp_zeroconf_with_pcp_raw_data")
    input_data.add(Specs.pmlog_summary_pcp_zeroconf, PMLOG_SUMMARY_OUTPUT)
    input_data.add(Specs.pcp_raw_data, PCP_RAW_DATA_FAKE_FILE, path="var/log/pcp/pmlogger/20240401.index")
    result = run_test(system_profile, input_data)
    assert result["is_ros"] is True
    assert result["is_pcp_raw_data_collected"] is True

    input_data = InputData("test_ros_collect_only")
    input_data.add(Specs.insights_client_conf, INSIGHTS_CLIENT_CONF_ROS_COLLECT_HIT)
    result = run_test(system_profile, input_data)
    assert result["is_ros"] is True
    assert result["is_pcp_raw_data_collected"] is False

    input_data = InputData("test_ros_collect_and_pmlog_summary_pcp_zeroconf_with_pcp_raw_data")
    input_data.add(Specs.pmlog_summary_pcp_zeroconf, PMLOG_SUMMARY_OUTPUT)
    input_data.add(Specs.insights_client_conf, INSIGHTS_CLIENT_CONF_ROS_COLLECT_HIT)
    input_data.add(Specs.pcp_raw_data, PCP_RAW_DATA_FAKE_FILE, path="var/log/pcp/pmlogger/20240401.index")
    result = run_test(system_profile, input_data)
    assert result["is_ros"] is True
    assert result["is_pcp_raw_data_collected"] is True

    input_data = InputData("test_ros_collect_but_nothit_1")
    input_data.add(Specs.insights_client_conf, INSIGHTS_CLIENT_CONF_ROS_COLLECT_UNHIT_1)
    result = run_test(system_profile, input_data)
    assert "is_ros" not in result
    assert "is_pcp_raw_data_collected" not in result

    input_data = InputData("test_ros_collect_but_nothit_2")
    input_data.add(Specs.insights_client_conf, INSIGHTS_CLIENT_CONF_ROS_COLLECT_UNHIT_2)
    input_data.add(Specs.pcp_raw_data, PCP_RAW_DATA_FAKE_FILE, path="var/log/pcp/pmlogger/20240401.index")
    result = run_test(system_profile, input_data)
    assert "is_ros" not in result
    assert "is_pcp_raw_data_collected" not in result

    input_data = InputData("test_not_ros_related_data")
    result = run_test(system_profile, input_data)
    assert "is_ros" not in result
    assert "is_pcp_raw_data_collected" not in result
