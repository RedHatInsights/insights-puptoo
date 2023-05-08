from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

GCP_LICENSE_CODES_1 = """
[{"id": "4720191914037931587"}]
""".strip()

GCP_LICENSE_CODES_2 = """
[{"id":"1000006"}]
""".strip()

GCP_LICENSE_CODES_BAD = """
[{"id": "324234"}]
""".strip()


def test_gcp_license_codes():
    input_data = InputData().add(Specs.gcp_license_codes, GCP_LICENSE_CODES_1)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False

    input_data = InputData().add(Specs.gcp_license_codes, GCP_LICENSE_CODES_2)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.gcp_license_codes, GCP_LICENSE_CODES_BAD)
    result = run_test(system_profile, input_data)
    assert result.get("is_marketplace") is False
