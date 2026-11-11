from osnt.extract import analyze_post, extract_customers, extract_projects


def test_extracts_itzbund_platform_and_project():
    text = (
        "Go-Live der Datenplattform für das ITZBund. "
        "Projekt Bürgerdaten-Kern mit ersten KI-Services."
    )
    result = analyze_post(text, "Data Platform Lead Public Sector")
    assert "ITZBund" in result["customers"]
    assert result["data_ai"]
    assert result["public_sector"]
    assert result["in_scope"]
    assert any("Bürgerdaten" in p for p in result["projects"])


def test_customer_bka():
    assert "BKA" in extract_customers("Rahmenvertrag für das BKA, Los Testautomation")


def test_project_rahmenvertrag():
    names = extract_projects("Rahmenvertrag Kooperationsplattform elektronische Genehmigungsverfahren")
    assert names
