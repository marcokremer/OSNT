from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from osnt.companies import COMPANIES
from osnt.ingest import load_demo_snapshot, sync_ted, sync_vergabe
from osnt.people_import import parse_people_csv
from osnt.store import Store

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_DB = Path(os.environ.get("OSNT_DB", "data/osnt.db"))


def get_store() -> Store:
    return Store(DEFAULT_DB)


app = FastAPI(title="OSNT", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/meta")
def meta() -> dict:
    return {
        "companies": [{"id": c.id, "label": c.label} for c in COMPANIES],
        "linkedin_scraping": False,
        "sources": ["ted", "vergabe", "csv-import"],
    }


@app.get("/api/stats")
def stats() -> dict:
    return get_store().stats()


@app.get("/api/projects")
def projects(
    company: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    focus: bool = Query(False),
) -> list[dict]:
    notices = get_store().list_notices(company=company, tag=tag, q=q, focus_only=focus)
    return [n.model_dump() for n in notices]


@app.get("/api/customers")
def customers(company: str | None = None) -> list[dict]:
    return get_store().customers(company=company)


@app.get("/api/people")
def people(company: str | None = None) -> list[dict]:
    return [p.model_dump() for p in get_store().list_people(company=company)]


@app.post("/api/sync/demo")
def api_sync_demo() -> dict:
    return load_demo_snapshot(get_store())


@app.post("/api/sync/ted")
def api_sync_ted(limit: int = Query(25, ge=1, le=200)) -> dict:
    return sync_ted(get_store(), limit_per_company=limit)


@app.post("/api/sync/vergabe")
def api_sync_vergabe(days: int = Query(1, ge=1, le=7)) -> dict:
    return sync_vergabe(get_store(), days=days)


@app.post("/api/import/people")
async def api_import_people(file: UploadFile = File(...)) -> dict:
    raw = (await file.read()).decode("utf-8-sig")
    source = "sales-navigator" if "first name" in raw.lower() else "csv-import"
    people = parse_people_csv(raw, source=source)
    store = get_store()
    for person in people:
        store.insert_person(person)
    return {"imported": len(people), "source": source}


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "notices": get_store().notice_count()})
