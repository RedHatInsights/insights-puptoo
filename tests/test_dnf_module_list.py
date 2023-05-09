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

EXPECTED =  [
    {"name": "default", "stream": "1.20"},
    {"name": "default_enabled", "stream": "1.30"},
    {"name": "enabled", "stream": "1.50"},
    {"name": "default2", "stream": "1.70"},
    {"name": "default3", "stream": "1.82"},
    {"name": "default4", "stream": "1.91"},
]

def test_dnf_modules():
    input_data = InputData().add(Specs.dnf_module_list, DNF_MODULE_LIST)
    result = run_test(system_profile, input_data)
    for module in result["dnf_modules"]:
        assert module in EXPECTED
    assert len(result["dnf_modules"]) == len(EXPECTED)
