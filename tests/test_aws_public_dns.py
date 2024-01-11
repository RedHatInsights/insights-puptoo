from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

AWSPUBLICHOSTNAMES = """
ec2-52-95-95-95.ap-northeast-1.compute.amazonaws.com
""".strip()

AWS_CURL_ERROR_1 = """
<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title>404 - Not Found</title>
 </head>
 <body>
  <h1>404 - Not Found</h1>
 </body>
</html>
"""

AWS_CURL_ERROR_2 = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title>404 - Not Found</title>
 </head>
 <body>
  <h1>404 - Not Found</h1>
 </body>
</html>
"""


def test_aws_public_ipv4_addresses():
    input_data = InputData().add(Specs.aws_public_hostnames, AWSPUBLICHOSTNAMES)
    result = run_test(system_profile, input_data)
    assert result["public_dns"] == ["ec2-52-95-95-95.ap-northeast-1.compute.amazonaws.com"]

    input_data = InputData().add(Specs.aws_public_hostnames, AWS_CURL_ERROR_1)
    result = run_test(system_profile, input_data)
    assert result.get("public_dns") is None

    input_data = InputData().add(Specs.aws_public_hostnames, AWS_CURL_ERROR_2)
    result = run_test(system_profile, input_data)
    assert result.get("public_dns") is None
