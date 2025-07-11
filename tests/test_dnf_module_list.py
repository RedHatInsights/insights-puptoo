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
    {"name": "default", "stream": "1.20", "status": ["default"]},
    {"name": "default_enabled", "stream": "1.30", "status": ["default", "enabled"]},
    {"name": "enabled", "stream": "1.50", "status": ["enabled"]},
    {"name": "default2", "stream": "1.70", "status": ["default"]},
    {"name": "default3", "stream": "1.82", "status": ["enabled"]},
    {"name": "default4", "stream": "1.91", "status": ["enabled"]},
]

DNF_MODULE_LIST_WITH_INSTALLED_1 = """
Last metadata expiration check: 2:30:21 ago on Tue 08 Jul 2025 02:04:51 PM CST.
Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)
Name                 Stream             Profiles                                                        Summary
mariadb              10.11              client, galera, server [d]                                      MariaDB Module
maven                3.8                common [d]                                                      Java project management and project comprehension tool
maven                3.9                common [d], openjdk11, openjdk17, openjdk21, openjdk8           Java project management and project comprehension tool
mysql                8.4                api, client, filter, server [d]                                 MySQL Module
nginx                1.22               common [d]                                                      nginx webserver
nginx                1.24 [e]           common [d]                                                      nginx webserver
nginx                1.26               common [d]                                                      nginx webserver
nodejs               18                 common [d], development, minimal, s2i                           Javascript runtime
nodejs               20                 common [d], development, minimal, s2i                           Javascript runtime
nodejs               22                 common [d], development, minimal, s2i                           Javascript runtime
php                  8.1                common [d], devel, minimal                                      PHP scripting language
php                  8.2                common [d], devel, minimal                                      PHP scripting language
php                  8.3 [e]            common [d] [i], devel, minimal                                  PHP scripting language
postgresql           15                 client, server [d]                                              PostgreSQL server and client module
postgresql           16                 client, server [d]                                              PostgreSQL server and client module
redis                7                  common [d]                                                      Redis persistent key-value database
ruby                 3.1                common [d]                                                      An interpreter of object-oriented scripting language
ruby                 3.3                common [d]                                                      An interpreter of object-oriented scripting language

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()
EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_1 = [
    {"name": "nginx", "stream": "1.24", "status": ["enabled"]},
    {"name": "php", "stream": "8.3", "status": ["enabled", "installed"]},
]

DNF_MODULE_LIST_WITH_INSTALLED_2 = """
Last metadata expiration check: 1:03:35 ago on Wed 09 Jul 2025 02:11:26 PM CST.
Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)
Name                 Stream          Profiles                                 Summary
389-ds               1.4                                                      389 Directory Server (base)
ant                  1.10 [d]        common [d]                               Java build tool
httpd                2.4 [d][e]      common [d], devel, minimal               Apache HTTP Server
mariadb              10.3 [d][x]     client, galera, server [d]               MariaDB Module
mariadb              10.5 [x]        client, galera, server [d]               MariaDB Module
mariadb              10.11 [x]       client, galera, server [d]               MariaDB Module
nginx                1.24 [e]        common [d]                               nginx webserver
perl                 5.24            common [d], minimal                      Practical Extraction and Report Language
perl                 5.26 [d][e]     common [d], minimal                      Practical Extraction and Report Language
perl                 5.30            common [d], minimal                      Practical Extraction and Report Language
perl                 5.32            common [d], minimal                      Practical Extraction and Report Language
php                  7.2 [d]         common [d], devel, minimal               PHP scripting language
php                  7.3             common [d], devel, minimal               PHP scripting language
php                  7.4             common [d], devel, minimal               PHP scripting language
php                  8.0 [e]         common [d] [i], devel, minimal           PHP scripting language
php                  8.2             common [d], devel, minimal               PHP scripting language
redis                5 [d]           common [d]                               Redis persistent key-value database
redis                6               common [d]                               Redis persistent key-value database

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()
EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_2 = [
    {"name": "ant", "stream": "1.10", "status": ["default"]},
    {"name": "httpd", "stream": "2.4", "status": ["default", "enabled"]},
    {"name": "nginx", "stream": "1.24", "status": ["enabled"]},
    {"name": "perl", "stream": "5.26", "status": ["default", "enabled"]},
    {"name": "php", "stream": "8.0", "status": ["enabled", "installed"]},
    {"name": "redis", "stream": "5", "status": ["default"]},
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

DNF_MODULE_LIST_MULTI_SECTIONS_1 = """
Last metadata expiration check: 1:37:02 ago on Wed Mar 26 09:50:23 2025.
RHEL-9.x-optional-latest
Name       Stream   Profiles                              Summary
mariadb    10.11    client, galera, server [d]            MariaDB Module
maven      3.8      common [d]                            Java project management and project comprehension tool
nginx      1.22 [e] common [d]                            nginx webserver
nginx      1.24     common [d]                            nginx webserver
redis      7        common [d]                            Redis persistent key-value database
ruby       3.1      common [d]                            An interpreter of object-oriented scripting language
ruby       3.3      common [d]                            An interpreter of object-oriented scripting language

Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)
Name       Stream   Profiles                              Summary
mariadb    10.11    client, galera, server [d]            MariaDB Module
maven      3.8      common [d]                            Java project management and project comprehension tool
nginx      1.22 [e] common [d]                            nginx webserver
nginx      1.24     common [d]                            nginx webserver
redis      7        common [d]                            Redis persistent key-value database
ruby       3.1      common [d]                            An interpreter of object-oriented scripting language
ruby       3.3      common [d]                            An interpreter of object-oriented scripting language

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()

DNF_MODULE_LIST_MULTI_SECTIONS_2 = """
Last metadata expiration check: 1:37:02 ago on Wed Mar 26 09:50:23 2025.
RHEL-9.x-optional-latest
Name       Stream   Profiles                              Summary
mariadb    10.11    client, galera, server [d]            MariaDB Module
maven      3.8      common [d]                            Java project management and project comprehension tool
nginx      1.22     common [d]                            nginx webserver
nginx      1.24     common [d]                            nginx webserver
redis      7        common [d]                            Redis persistent key-value database
ruby       3.1      common [d]                            An interpreter of object-oriented scripting language
ruby       3.3      common [d]                            An interpreter of object-oriented scripting language

Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)
Name       Stream   Profiles                              Summary
mariadb    10.11    client, galera, server [d]            MariaDB Module
maven      3.8      common [d]                            Java project management and project comprehension tool
nginx      1.22 [e] common [d]                            nginx webserver
nginx      1.24     common [d]                            nginx webserver
redis      7        common [d]                            Redis persistent key-value database
ruby       3.1      common [d]                            An interpreter of object-oriented scripting language
ruby       3.3      common [d]                            An interpreter of object-oriented scripting language

Hint: [d]efault, [e]nabled, [x]disabled, [i]nstalled
""".strip()


def test_dnf_modules():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST)
    result = run_test(system_profile, input_data)
    for module in result["dnf_modules"]:
        assert module in EXPECTED
    assert len(result["dnf_modules"]) == len(EXPECTED)

    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_WITH_INSTALLED_1)
    result = run_test(system_profile, input_data)
    for module in result["dnf_modules"]:
        assert module in EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_1
    assert len(result["dnf_modules"]) == len(EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_1)

    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_WITH_INSTALLED_2)
    result = run_test(system_profile, input_data)
    for module in result["dnf_modules"]:
        assert module in EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_2
    assert len(result["dnf_modules"]) == len(EXPECTED_DNF_MODULE_LIST_WITH_INSTALLED_2)


def test_dnf_modules_multi_sections():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_MULTI_SECTIONS_1)
    result = run_test(system_profile, input_data)
    assert result["dnf_modules"] == [{'name': 'nginx', 'stream': '1.22', "status": ["enabled"]}]

    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_MULTI_SECTIONS_2)
    result = run_test(system_profile, input_data)
    assert result["dnf_modules"] == [{'name': 'nginx', 'stream': '1.22', "status": ["enabled"]}]


def test_dnf_modules_none_enabled():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST_NONE_ENABLED)
    result = run_test(system_profile, input_data)
    assert result["dnf_modules"] == []


def test_dnf_modules_not_generated():
    input_data = InputData()
    result = run_test(system_profile, input_data)
    assert "dnf_modules" not in result
