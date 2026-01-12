from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

INSTALLED_PRODUCTS_1 = """
Product Certificate
path: /etc/pki/product-default/69.pem
id: 69
Name: Red Hat Enterprise Linux Server
brand_type:
brand_name:
tags: rhel-7,rhel-7-server
Product Certificate
path: /etc/pki/product/479.pem
id: 479
Name: Red Hat Enterprise Linux for x86_64
tags: rhel-8,rhel-8-x86_64
brand_type:
brand_name:
""".strip()

INSTALLED_PRODUCTS_2 = """
+-------------------------------------------+
Product Certificate
+-------------------------------------------+

Certificate:
    Path: /etc/pki/product-default/69.pem
    Version: 1.0
    Serial: 12750047592154749739
    Start Date: 2017-06-28 18:05:10+00:00
    End Date: 2037-06-23 18:05:10+00:00

Subject:
    CN: Red Hat Product ID [4f9995e0-8dc4-4b4f-acfe-4ef1264b94f3]

Issuer:
    C: US
    CN: Red Hat Entitlement Product Authority
    O: Red Hat, Inc.
    OU: Red Hat Network
    ST: North Carolina
    emailAddress: ca-support@redhat.com

Product:
    ID: 69
    Name: Red Hat Enterprise Linux Server
    Version: 7.4
    Arch: x86_64
    Tags: rhel-7,rhel-7-server
    Brand Type:
    Brand Name:
""".strip()

INSTALLED_PRODUCTS_3 = """
Product Certificate
path: /etc/pki/product-default/69.pem
id: 69
Product Certificate
path: /etc/pki/product/479.pem
id: 479
""".strip()


def test_installed_products():

    input_data = InputData()
    input_data.add(Specs.subscription_manager_installed_product_ids, INSTALLED_PRODUCTS_1)
    result = run_test(system_profile, input_data)
    assert result["installed_products"] == [
            {"id": "479", "name": "Red Hat Enterprise Linux for x86_64"},
            {"id": "69", "name": "Red Hat Enterprise Linux Server"},
        ]

    input_data = InputData()
    input_data.add(Specs.subscription_manager_installed_product_ids, INSTALLED_PRODUCTS_2)
    result = run_test(system_profile, input_data)
    assert result["installed_products"] == [
            {"id": "69", "name": "Red Hat Enterprise Linux Server"},
        ]

    input_data = InputData()
    input_data.add(Specs.subscription_manager_installed_product_ids, INSTALLED_PRODUCTS_3)
    result = run_test(system_profile, input_data)
    assert result["installed_products"] == [{"id": "479"}, {"id": "69"}]

    input_data = InputData()
    input_data.add(Specs.subscription_manager_installed_product_ids, "some random data")
    result = run_test(system_profile, input_data)
    assert "installed_products" not in result
