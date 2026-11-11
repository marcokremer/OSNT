from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from osnt.companies import COMPANIES
from osnt.costs import estimate
from osnt.ingest import scrape
from osnt.scraper import MissingCredentials, configured_providers
from osnt.store import Store

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_DB = Path(os.environ.get("OSNT_DB", "data/osnt.db"))


def get_store() -> Store:
    return Store(DEFAULT_DB)


app = FastAPI(title="OSNT LinkedIn OSINT", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/meta")
def meta() -> dict:
    return {
        "companies": [
            {"id": c.id, "label": c.label, "linkedin": c.linkedin_company} for c in COMPANIES
        ],
        "providers": configured_providers(),
        "focus": "LinkedIn-Posts: Data Platforms & KI × Public Sector",
    }


@app.get("/api/stats")
def stats() -> dict:
    return get_store().stats()


@app.get("/api/posts")
def posts(company: str | None = None, q: str | None = None, scope: str = "in") -> list[dict]:
    in_scope = True if scope == "in" else None
    return [
        p.model_dump()
        for p in get_store().list_posts(company=company, q=q, in_scope=in_scope)
    ]


@app.get("/api/people")
def people(company: str | None = None, scope: str = "in") -> list[dict]:
    in_scope = True if scope == "in" else None
    return [p.model_dump() for p in get_store().list_people(company=company, in_scope=in_scope)]


@app.get("/api/customers")
def customers(company: str | None = None) -> list[dict]:
    return get_store().customers(company=company)


@app.get("/api/projects")
def projects(company: str | None = None) -> list[dict]:
    return get_store().projects(company=company)


@app.get("/api/costs")
def costs(
    people: int = Query(400, ge=10, le=5000),
    posts_per_person: int = Query(12, ge=1, le=50),
    post_search_hits: int = Query(1600, ge=50, le=20000),
) -> dict:
    return estimate(people=people, posts_per_person=posts_per_person, post_search_hits=post_search_hits)


@app.post("/api/sync/{provider}")
def api_sync(provider: str, max_posts: int = Query(40, ge=5, le=200)) -> dict:
    try:
        return scrape(get_store(), provider=provider, max_posts=max_posts)
    except MissingCredentials as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, **get_store().counts()})
