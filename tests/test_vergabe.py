from osnt.vergabe import parse_ocds_package


def test_parse_ocds_keeps_competitor_awards():
    package = {
        "uri": "https://oeffentlichevergabe.de/api/notices/abc",
        "publishedDate": "2026-11-06T00:00:00+01:00",
        "releases": [
            {
                "ocid": "ocds-test-1",
                "date": "2026-11-06T00:00:00+01:00",
                "buyer": {"name": "Beschaffungsamt des BMI"},
                "tender": {
                    "title": "Organisationsberatung",
                    "description": "Digitalisierung der Verwaltung",
                    "tenderers": [{"name": "PricewaterhouseCoopers GmbH"}],
                },
                "awards": [{"id": "LOT-0000"}],
            }
        ],
    }
    notices = parse_ocds_package(package)
    assert len(notices) == 1
    assert notices[0].companies == ["pwc"]
    assert notices[0].buyer_name.startswith("Beschaffungsamt")


def test_parse_ocds_drops_unrelated():
    package = {
        "releases": [
            {
                "ocid": "x",
                "buyer": {"name": "Stadt X"},
                "tender": {"title": "Straßenbau", "tenderers": [{"name": "Baufirma GmbH"}]},
            }
        ]
    }
    assert parse_ocds_package(package) == []
