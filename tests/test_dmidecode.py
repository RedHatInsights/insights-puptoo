from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

DMIDECODE_BIOS = """
# dmidecode 3.3
Handle 0x0000, DMI type 0, 26 bytes
BIOS Information
\tVendor: Dell Inc.
\tVersion: 2.19.0
\tRelease Date: 03/17/2023
""".strip()


def test_bios_facts_extracted():
    input_data = InputData()
    input_data.add(Specs.dmidecode, DMIDECODE_BIOS)
    result = run_test(system_profile, input_data)
    assert result["bios_vendor"] == "Dell Inc."
    assert result["bios_version"] == "2.19.0"
    assert result["bios_release_date"] == "03/17/2023"


def test_no_dmidecode_omits_bios_facts():
    input_data = InputData()
    result = run_test(system_profile, input_data)
    assert "bios_vendor" not in result
    assert "bios_version" not in result
    assert "bios_release_date" not in result
