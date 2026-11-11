from osnt.classify import classify, in_focus, is_it_cpv


def test_ai_and_platform_tags():
    tags = classify(
        "Aufbau einer Datenplattform mit künstlicher Intelligenz auf Azure",
        ["72000000"],
    )
    assert "ai" in tags
    assert "data_platform" in tags
    assert "it" in tags
    assert in_focus(tags)


def test_reseller_without_ai():
    tags = classify("Produkte des Herstellers Red Hat und Lizenzen", ["48000000"])
    assert "reseller" in tags
    assert "ai" not in tags
    assert not in_focus(tags)


def test_it_cpv():
    assert is_it_cpv(["72200000"])
    assert not is_it_cpv(["45000000"])
