from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

AWSPUBLICIPV4ADDRESSES = """
1.2.3.4
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
    input_data = InputData().add(Specs.aws_public_ipv4_addresses, AWSPUBLICIPV4ADDRESSES)
    result = run_test(system_profile, input_data)
    assert result["public_ipv4_addresses"] == ["1.2.3.4"]

    input_data = InputData().add(Specs.aws_public_ipv4_addresses, AWS_CURL_ERROR_1)
    result = run_test(system_profile, input_data)
    assert result.get("public_ipv4_addresses") == None

    input_data = InputData().add(Specs.aws_public_ipv4_addresses, AWS_CURL_ERROR_2)
    result = run_test(system_profile, input_data)
    assert result.get("public_ipv4_addresses") == None
