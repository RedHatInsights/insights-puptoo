INSTALLED_PRODUCT_CASES = [
    # Case 1: Multiple distinct products (different product IDs)
    (
        """
        Product Certificate
        Path: /etc/pki/product-default/ 479.pem
        ID: 479
        Name: Red Hat Enterprise Linux for x86_64

        Product Certificate
        Path: /etc/pki/product-default/ 49.pem
        ID: 49
        Name: Red Hat Enterprise Linux for x86_64
        """,
        [
            {"id": "479", "name": "Red Hat Enterprise Linux for x86_64"},
            {"id": "49", "name": "Red Hat Enterprise Linux for x86_64"},
        ],
    ),
    # Case 2: Single product present
    (
        """
        Product Certificate
        Path: /etc/pki/product-default/ 479.pem
        ID: 479
        Name: Red Hat Enterprise Linux for x86_64
        """,
        [
            {"id": "479", "name": "Red Hat Enterprise Linux for x86_64"},
        ],
    ),
    # Case 3: Duplicate product IDs without product name (deduplicated by ID)
    (
        """
        Product Certificate
        Path: /etc/pki/product-default/479.pem
        ID: 479
        Tags: rhel-9,rhel-9-x86_64
        Product Certificate
        Path: /etc/pki/product/479.pem
        ID: 479
        Tags: rhel-9,rhel-9-x86_64
        """,
        [{"id": "479"}],
    ),
    # Case 4: Duplicate product IDs with identical product name
    (
        """
        Product Certificate
        Path: /etc/pki/product-default/479.pem
        ID: 479
        Name: Red Hat Enterprise Linux for x86_64
        Tags: rhel-9,rhel-9-x86_64
        Product Certificate
        Path: /etc/pki/product/479.pem
        ID: 479
        Name: Red Hat Enterprise Linux for x86_64
        Tags: rhel-9,rhel-9-x86_64
        """,
        [{"id": "479", "name": "Red Hat Enterprise Linux for x86_64"}],
    ),
    # Case 5: Duplicate product IDs where only one certificate provides a name
    (
        """
        Product Certificate
        Path: /etc/pki/product-default/479.pem
        ID: 479
        Name: Red Hat Enterprise Linux for x86_64
        Tags: rhel-9,rhel-9-x86_64
        Product Certificate
        Path: /etc/pki/product/479.pem
        ID: 479
        Tags: rhel-9,rhel-9-x86_64
        """,
        [{"id": "479", "name": "Red Hat Enterprise Linux for x86_64"}],
    ),
]
