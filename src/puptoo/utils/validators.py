PROVIDER = ['provider_id', 'provider_type']
FACTS_EXCEPT_PROVIDER = [
    'insights_id', 'subscription_manager_id', 'satellite_id',
    'bios_uuid', 'ip_addresses', 'mac_addresses', 'fqdn'
]
CANONICAL_ID_FACTS = ['provider_id', 'subscription_manager_id', 'insights_id']


def validateCanonicalFacts(facts):
    if ((all(key in facts for key in PROVIDER) or not any(key in facts for key in PROVIDER))
            and any(key in facts for key in CANONICAL_ID_FACTS)
            and any(key in facts for key in FACTS_EXCEPT_PROVIDER)):
        return True
    return False
