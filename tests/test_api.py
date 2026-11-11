from fastapi.testclient import TestClient

from osnt import web


def test_health_and_demo_seed(tmp_path, monkeypatch):
    db = tmp_path / "osnt.db"
    monkeypatch.setattr(web, "DEFAULT_DB", db)
    client = TestClient(web.app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    seeded = client.post("/api/sync/demo")
    assert seeded.status_code == 200
    assert seeded.json()["ingested"] > 0

    stats = client.get("/api/stats").json()
    assert stats["notices"] > 0
    assert stats["customers"] > 0
    assert "accenture" in stats["by_company"]

    projects = client.get("/api/projects?company=accenture").json()
    assert projects
    assert any("accenture" in p["companies"] for p in projects)

    home = client.get("/")
    assert home.status_code == 200
    assert "Kein LinkedIn-Scraper" in home.text
