from fastapi.testclient import TestClient

from osnt import web


def test_linkedin_demo_pipeline(tmp_path, monkeypatch):
    db = tmp_path / "osnt.db"
    monkeypatch.setattr(web, "DEFAULT_DB", db)
    client = TestClient(web.app)

    assert client.get("/health").json()["ok"] is True
    home = client.get("/")
    assert "LinkedIn" in home.text
    assert "TED live" not in home.text

    seeded = client.post("/api/sync/demo")
    assert seeded.status_code == 200
    body = seeded.json()
    assert body["posts"] >= 8

    stats = client.get("/api/stats").json()
    assert stats["people"] >= 6
    assert stats["customers"] >= 4
    assert stats["projects"] >= 1
    assert "accenture" in stats["by_company"]

    posts = client.get("/api/posts").json()
    assert any("ITZBund" in (p.get("customers") or []) for p in posts)

    costs = client.get("/api/costs").json()
    assert costs["cheapest"]["usd"] >= 0

    missing = client.post("/api/sync/apify")
    assert missing.status_code == 400
