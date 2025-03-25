from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

DNF_MODULE_LIST = """
Updating Subscription Management repositories.
Name                Stream      Profiles                                  Summary
not_enabled         1.1                                                   asdf
default             1.20 [d]    common [d]                                asdf
default_enabled     1.30 [d][e] common [d]                                asdf
default_disabled    1.40 [d][x] common [d]                                asdf
enabled             1.50 [e]                                              asdf
disabled            1.60 [x]                                              asdf
default2            1.70 [d]                                              asdf
default2            1.71                                                  asdf
default3            1.80 [d]                                              asdf
default3            1.81                                                  asdf
default3            1.82 [e]                                              asdf
default4            1.90                                                  asdf
default4            1.91 [e]                                              asdf
default4            1.92 [d]                                              asdf

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()

EXPECTED = [
    {"name": "default", "stream": "1.20"},
    {"name": "default_enabled", "stream": "1.30"},
    {"name": "enabled", "stream": "1.50"},
    {"name": "default2", "stream": "1.70"},
    {"name": "default3", "stream": "1.82"},
    {"name": "default4", "stream": "1.91"},
]

DNF_MODULE_LIST_NONE_ENABLED = """
Updating Subscription Management repositories.
Last metadata expiration check: 1:14:27 ago on Fri 21 Mar 2025 10:17:51 AM CST.
Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)
Name                           Stream                     Profiles                                                  Summary
mariadb                        10.11                      client, galera, server [d]                                MariaDB Module
maven                          3.8                        common [d]                                                Java project management and project comprehension tool
nginx                          1.22                       common [d]                                                nginx webserver
nginx                          1.24                       common [d]                                                nginx webserver
nodejs                         18                         common [d], development, minimal, s2i                     Javascript runtime
nodejs                         20                         common [d], development, minimal, s2i                     Javascript runtime
nodejs                         22                         common [d], development, minimal, s2i                     Javascript runtime
php                            8.1                        common [d], devel, minimal                                PHP scripting language
php                            8.2                        common [d], devel, minimal                                PHP scripting language
postgresql                     15                         client, server [d]                                        PostgreSQL server and client module
postgresql                     16                         client, server [d]                                        PostgreSQL server and client module
redis                          7                          common [d]                                                Redis persistent key-value database
ruby                           3.1                        common [d]                                                An interpreter of object-oriented scripting language
ruby                           3.3                        common [d]                                                An interpreter of object-oriented scripting language

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()


def test_dnf_modules():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST)
    result = run_test(system_profile, input_data)
    for module in result["dnf_modules"]:
        assert module in EXPECTED
    assert len(result["dnf_modules"]) == len(EXPECTED)


def test_dnf_modules_none_enabled():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_NONE_ENABLED)
    result = run_test(system_profile, input_data)
    assert result["dnf_modules"] == []


def test_dnf_modules_not_generated():
    input_data = InputData()
    result = run_test(system_profile, input_data)
    assert "dnf_modules" not in result
