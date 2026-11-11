from osnt.ted import parse_notice


def test_parse_notice_localizes_and_matches_company():
    notice = parse_notice(
        {
            "publication-number": "175483-2024",
            "publication-date": "2024-03-25Z",
            "notice-title": {
                "deu": "ÖGD Bürgerportal",
                "eng": "Public health portal",
            },
            "buyer-name": {"deu": ["Landesamt für Gesundheit und Lebensmittelsicherheit"]},
            "winner-name": {"deu": ["Accenture GmbH"]},
            "classification-cpv": ["72000000", "72212200"],
            "total-value": 9259790,
            "description-proc": {"deu": "Websoftware-Portal für den ÖGD"},
            "notice-type": "can-standard",
        }
    )
    assert notice.id == "ted:175483-2024"
    assert notice.buyer_name.startswith("Landesamt")
    assert "accenture" in notice.companies
    assert notice.value_eur == 9259790
    assert "it" in notice.tags
    assert notice.source_url.endswith("175483-2024")
