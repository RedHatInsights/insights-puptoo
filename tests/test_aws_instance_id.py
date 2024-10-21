from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile

AWS_INSTANCE_ID_DOC_TEMPLATE = """
{
    "devpayProductCodes" : null,
    "marketplaceProductCodes" : %s,
    "availabilityZone" : "us-west-2b",
    "privateIp" : "10.158.112.84",
    "version" : "2017-09-30",
    "instanceId" : "i-1234567890abcdef0",
    "billingProducts" : %s,
    "instanceType" : "t2.micro",
    "accountId" : "123456789012",
    "imageId" : "ami-5fb8c835",
    "pendingTime" : "2016-11-19T16:32:11Z",
    "architecture" : "x86_64",
    "kernelId" : null,
    "ramdiskId" : null,
    "region" : "us-west-2"
}""".strip()

# Only marketplace_product_codes
AWS_INSTANCE_ID_DOC_1 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            '[ "1abc2defghijklm3nopqrs4tu" ]',
                            'null',
                        )
AWS_INSTANCE_ID_DOC_2 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            '[ "1abc2defghijklm3nopqrs4tu" ]',
                            '[ ]',
                        )
# Only billing_products
AWS_INSTANCE_ID_DOC_3 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # False
                            'null',
                            '[ "bp-63a5400a" ]',
                        )
AWS_INSTANCE_ID_DOC_4 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            'null',
                            '[ "bp-6ba54002" ]',
                        )
AWS_INSTANCE_ID_DOC_5 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            'null',
                            '[ "bp-6ba54002", "bp-63a5400a" ]',
                        )
# Both exist
AWS_INSTANCE_ID_DOC_6 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # False
                            '[ "1abc2defghijklm3nopqrs4tu" ]',
                            '[ "bp-63a5400a" ]',
                        )
AWS_INSTANCE_ID_DOC_7 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            '[ "1abc2defghijklm3nopqrs4tu" ]',
                            '[ "bp-6ba54002" ]',
                        )
AWS_INSTANCE_ID_DOC_8 = AWS_INSTANCE_ID_DOC_TEMPLATE % (    # True
                            '[ "1abc2defghijklm3nopqrs4tu" ]',
                            '[ "bp-6ba54002", "bp-63a5400a" ]'
                        )
# Both empty
AWS_INSTANCE_ID_DOC_EMPTY_1 = AWS_INSTANCE_ID_DOC_TEMPLATE % (  # False
                            'null',
                            'null',
                        )
AWS_INSTANCE_ID_DOC_EMPTY_2 = AWS_INSTANCE_ID_DOC_TEMPLATE % (  # False
                            '[]',
                            '[]',
                        )


def test_azure_instance_plan():

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_1)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_2)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_3)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is False

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_4)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_5)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_6)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is False

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_7)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_8)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is True

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_EMPTY_1)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is False

    input_data = InputData().add(Specs.aws_instance_id_doc, AWS_INSTANCE_ID_DOC_EMPTY_2)
    result = run_test(system_profile, input_data)
    assert result["is_marketplace"] is False
