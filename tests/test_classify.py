from osnt.classify import classify


def test_ai_and_platform_tags():
    tags = classify(
        "Aufbau einer Datenplattform mit künstlicher Intelligenz auf Azure",
        ["72000000"],
    )
    assert "ai" in tags
    assert "data_platform" in tags
    assert "it" in tags
    assert "public_sector" not in tags
