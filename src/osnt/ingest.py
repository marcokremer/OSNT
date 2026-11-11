from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from osnt.companies import match_companies
from osnt.extract import analyze_post, person_in_scope
from osnt.models import Person, Post
from osnt.scraper import MissingCredentials, run_apify_post_search, run_serper
from osnt.store import Store

DEMO_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "data" / "demo" / "linkedin-demo.json",
    Path.cwd() / "data" / "demo" / "linkedin-demo.json",
)


def _demo_path() -> Path:
    for path in DEMO_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("data/demo/linkedin-demo.json fehlt")


def _company_id(raw_company: str, blob: str) -> str:
    hits = match_companies(f"{raw_company} {blob}")
    return hits[0] if hits else (raw_company or "").lower()


def persist_raw_posts(store: Store, raw_posts: list[dict[str, Any]], source: str) -> dict:
    people_seen: dict[str, Person] = {}
    stored_posts = 0
    in_scope_posts = 0
    for raw in raw_posts:
        text = raw.get("text") or ""
        headline = raw.get("headline") or ""
        analysis = analyze_post(text, headline)
        company = _company_id(raw.get("company") or "", f"{text} {headline}")
        person_id = raw.get("profile_url") or raw.get("person_id") or f"person:{raw.get('author')}"
        person = Person(
            id=person_id,
            name=raw.get("author") or "Unbekannt",
            company=company,
            headline=headline,
            location=raw.get("location") or "",
            profile_url=raw.get("profile_url") or "",
            about=raw.get("about") or "",
            in_scope=False,
            source=source,
        )
        people_seen.setdefault(person_id, person)
        post = Post(
            id=str(raw.get("id") or raw.get("url") or f"{source}:{stored_posts}"),
            person_id=person_id,
            company=company,
            author=person.name,
            url=raw.get("url") or "",
            text=text,
            posted_at=str(raw.get("posted_at") or ""),
            tags=analysis["tags"],
            customers=analysis["customers"],
            projects=analysis["projects"],
            in_scope=analysis["in_scope"],
            source=source,
        )
        store.upsert_post(post)
        stored_posts += 1
        if post.in_scope:
            in_scope_posts += 1

    by_person_posts: dict[str, list[str]] = {}
    for post in store.list_posts(in_scope=None, limit=5000):
        by_person_posts.setdefault(post.person_id, []).append(post.text)

    in_scope_people = 0
    for person_id, person in people_seen.items():
        person.in_scope = person_in_scope(
            person.headline, person.about, by_person_posts.get(person_id, [])
        )
        store.upsert_person(person)
        if person.in_scope:
            in_scope_people += 1

    stats = {
        "source": source,
        "posts": stored_posts,
        "posts_in_scope": in_scope_posts,
        "people": len(people_seen),
        "people_in_scope": in_scope_people,
    }
    store.record_run(source, "ok", stats)
    return stats


def load_demo(store: Store) -> dict:
    payload = json.loads(_demo_path().read_text(encoding="utf-8"))
    raw_posts = [
        {
            **post,
            "author": post.get("author"),
            "profile_url": post.get("person_id"),
            "company": post.get("company"),
            "headline": post.get("headline") or "",
        }
        for post in payload.get("posts") or []
    ]
    stats = persist_raw_posts(store, raw_posts, source="demo")
    for person in payload.get("people") or []:
        store.upsert_person(Person(**person))
    return stats


def scrape(store: Store, provider: str, max_posts: int = 40) -> dict:
    if provider == "demo":
        return load_demo(store)
    if provider == "apify":
        raw = run_apify_post_search(max_posts=max_posts)
        return persist_raw_posts(store, raw, source="apify")
    if provider == "serper":
        raw = run_serper()
        return persist_raw_posts(store, raw, source="serper")
    if provider == "brightdata":
        raise MissingCredentials(
            "Bright Data ist verdrahtet über BRIGHTDATA_API_KEY, der Batch-Trigger "
            "braucht einen bezahlten Account. Für den ersten Lauf Apify Post-Search "
            "oder Demo nutzen."
        )
    raise ValueError(f"Unbekannter Provider: {provider}")
