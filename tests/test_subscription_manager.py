from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

SUBSCRIPTION_MANAGER_FACTS_1 = """
aws_instance_id: 567890567890
conversions.activity: conversion
network.ipv6_address: ::1
uname.sysname: Linux
uname.version: #1 SMP PREEMPT Fri Sep 2 16:07:40 EDT 2022
virt.host_type: rhev, kvm
virt.is_guest: True
""".strip()

SUBSCRIPTION_MANAGER_FACTS_2 = """
aws_instance_id: 567890567890
conversions.activity: some-other-value
network.ipv6_address: ::1
uname.sysname: Linux
uname.version: #1 SMP PREEMPT Fri Sep 2 16:07:40 EDT 2022
virt.host_type: rhev, kvm
virt.is_guest: True
""".strip()

SUBSCRIPTION_MANAGER_FACTS_3 = """
aws_instance_id: 567890567890
network.ipv6_address: ::1
uname.sysname: Linux
uname.version: #1 SMP PREEMPT Fri Sep 2 16:07:40 EDT 2022
virt.host_type: rhev, kvm
virt.is_guest: True
""".strip()


def test_subscription_manager_facts():
    input_data = InputData("test_subscription_manager_facts_with_activity")
    input_data.add(Specs.subscription_manager_facts, SUBSCRIPTION_MANAGER_FACTS_1)
    result = run_test(system_profile, input_data)
    assert result["conversions"]["activity"] is True

    input_data = InputData("test_subscription_manager_facts_with_activity_but_false")
    input_data.add(Specs.subscription_manager_facts, SUBSCRIPTION_MANAGER_FACTS_2)
    result = run_test(system_profile, input_data)
    assert result["conversions"]["activity"] is False

    input_data = InputData("test_subscription_manager_facts_without_activity")
    input_data.add(Specs.subscription_manager_facts, SUBSCRIPTION_MANAGER_FACTS_3)
    result = run_test(system_profile, input_data)
    assert result["conversions"]["activity"] is False

    input_data = InputData("test_subscription_manager_facts_without_conversions")
    result = run_test(system_profile, input_data)
    assert "conversions" not in result
