from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from osnt.models import Notice
from osnt.store import Store
from osnt.ted import TedClient, parse_notice
from osnt.vergabe import VergabeClient

def _demo_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "data" / "demo" / "ted-snapshot.json",
        Path.cwd() / "data" / "demo" / "ted-snapshot.json",
        here.parent / "data" / "ted-snapshot.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("TED demo snapshot not found; expected data/demo/ted-snapshot.json")


def persist_notices(store: Store, notices: list[Notice]) -> int:
    for notice in notices:
        store.upsert_notice(notice)
    return len(notices)


def sync_ted(store: Store, limit_per_company: int = 25, client: TedClient | None = None) -> dict[str, Any]:
    owned = client is None
    ted = client or TedClient()
    try:
        summary = ted.ingest_all(limit_per_company=limit_per_company)
        count = persist_notices(store, summary["notices"])
        stats = {"ingested": count, "companies": summary["companies"]}
        store.record_run("ted", "ok", stats)
        return stats
    finally:
        if owned:
            ted.close()


def sync_vergabe(store: Store, days: int = 1, client: VergabeClient | None = None) -> dict[str, Any]:
    owned = client is None
    vergabe = client or VergabeClient()
    try:
        summary = vergabe.ingest_recent(days=days)
        count = persist_notices(store, summary["notices"])
        stats = {"ingested": count, "days": summary["days"], "scanned": summary["scanned"]}
        store.record_run("vergabe", "ok", stats)
        return stats
    finally:
        if owned:
            vergabe.close()


def load_demo_snapshot(store: Store, path: Path | None = None) -> dict[str, Any]:
    snapshot_path = path or _demo_path()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    notices: list[Notice] = []
    available: dict[str, int] = {}
    for company_label, block in payload.items():
        available[company_label] = int(block.get("totalNoticeCount") or 0)
        for raw in block.get("notices") or []:
            notices.append(parse_notice(raw, source="ted-demo"))
    count = persist_notices(store, notices)
    stats = {"ingested": count, "available": available, "source": str(snapshot_path)}
    store.record_run("ted-demo", "ok", stats)
    return stats
