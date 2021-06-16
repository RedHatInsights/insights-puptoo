from src.puptoo.app import clean_macs


GOOD_MACS = {"mac_addresses": ["52:54:00:fd:be:d0",
             "b4:6b:fc:9e:ae:0d"]}

BAD_MACS = {"mac_addresses": ["0.0.0.0",
            "52:54:00:fd:be:d0",
             "b4:6b:fc:9e:ae:0d",
             "0.0.0.0"]}


def test_clean_macs():
    result = clean_macs(GOOD_MACS)
    assert result["mac_addresses"] == ["52:54:00:fd:be:d0", "b4:6b:fc:9e:ae:0d"]

    result = clean_macs(BAD_MACS)
    assert result["mac_addresses"] == ["52:54:00:fd:be:d0", "b4:6b:fc:9e:ae:0d"]
