from src.puptoo.process import validateCanonicalFacts


CANONICAL_FACTS_NORMAL = {
    "insights_id": "0b7f2eed-a894-4363-85bf-7868a418152d",
    "machine_id": "d5895976-eede-4db0-b150-5a772a71e7f5",
    "bios_uuid": "e7adacf1-cd43-4e0b-a13c-2940c0e329b7",
    "subscription_manager_id": "0b7f2eed-a894-4363-85bf-7868a418152d",
    "ip_addresses": [
        "10.73.213.207"
    ],
    "mac_addresses": [
        "52:54:00:60:ff:e2",
        "00:00:00:00:00:00"
    ],
    "fqdn": "xiaoxwan-test332-rhel95"
}

CANONICAL_FACTS_INVALID_PROVIDER_PAIR = {
    "insights_id": "0b7f2eed-a894-4363-85bf-7868a418152d",
    "machine_id": "d5895976-eede-4db0-b150-5a772a71e7f5",
    "provider_id": "some-provider_id"
}


CANONICAL_FACTS_INVALID_MISSING_ID_FACTS = {
    "ip_addresses": [
        "10.73.213.207"
    ],
    "mac_addresses": [
        "52:54:00:60:ff:e2",
        "00:00:00:00:00:00"
    ]
}

CANONICAL_FACTS_INVALID_MISSING_FACTS = {
    "provider_id": "some-provider_id",
    "provider_type": "some-provider_type"
}


def test_validate_canonical_facts():

    assert validateCanonicalFacts(CANONICAL_FACTS_NORMAL)
    assert not validateCanonicalFacts(CANONICAL_FACTS_INVALID_PROVIDER_PAIR)
    assert not validateCanonicalFacts(CANONICAL_FACTS_INVALID_MISSING_ID_FACTS)
    assert not validateCanonicalFacts(CANONICAL_FACTS_INVALID_MISSING_FACTS)
    assert not validateCanonicalFacts({})
