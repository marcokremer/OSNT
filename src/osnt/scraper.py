"""LinkedIn collection via commercial scraper APIs — no LinkedIn login, no cookies.

DIY Playwright/session scraping against linkedin.com is not implemented.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from osnt.queries import apify_post_search_input, serper_queries

APIFY_POST_SEARCH = "harvestapi~linkedin-post-search"
APIFY_PROFILE_POSTS = "harvestapi~linkedin-profile-posts"
BRIGHTDATA_SCRAPE = "https://api.brightdata.com/datasets/v3/scrape"
BRIGHTDATA_POSTS = "gd_lyy3tktm25m4avu764"
SERPER_URL = "https://google.serper.dev/search"


class MissingCredentials(RuntimeError):
    pass


def _apify_token() -> str:
    token = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise MissingCredentials("APIFY_TOKEN fehlt — HarvestAPI-Lauf nicht gestartet.")
    return token


def _brightdata_key() -> str:
    key = os.environ.get("BRIGHTDATA_API_KEY") or os.environ.get("BRIGHT_DATA_API_KEY")
    if not key:
        raise MissingCredentials("BRIGHTDATA_API_KEY fehlt.")
    return key


def _serper_key() -> str:
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        raise MissingCredentials("SERPER_API_KEY fehlt.")
    return key


def normalize_apify_post(item: dict[str, Any], source: str = "apify") -> dict[str, Any]:
    author = item.get("author") or item.get("poster") or {}
    if isinstance(author, str):
        author_name = author
        author_url = ""
        company = ""
        headline = ""
    else:
        author_name = author.get("name") or author.get("fullName") or ""
        author_url = author.get("linkedinUrl") or author.get("url") or ""
        company = (
            author.get("companyName")
            or (author.get("experience") or [{}])[0].get("companyName")
            if isinstance(author.get("experience"), list) and author.get("experience")
            else author.get("companyName") or ""
        )
        headline = author.get("headline") or author.get("occupation") or ""
    text = item.get("text") or item.get("content") or item.get("commentary") or ""
    url = item.get("linkedinUrl") or item.get("url") or item.get("postUrl") or ""
    posted = item.get("postedAt") or item.get("postedDate") or item.get("date") or ""
    if isinstance(posted, dict):
        posted = posted.get("date") or posted.get("timestamp") or ""
    return {
        "id": url or f"{source}:{hash((author_name, text[:80]))}",
        "author": author_name,
        "profile_url": author_url,
        "headline": headline,
        "company": company,
        "text": text,
        "url": url,
        "posted_at": str(posted),
        "source": source,
    }


def run_apify_post_search(max_posts: int = 40, client: httpx.Client | None = None) -> list[dict]:
    token = _apify_token()
    url = (
        f"https://api.apify.com/v2/acts/{APIFY_POST_SEARCH}/run-sync-get-dataset-items"
        f"?token={token}"
    )
    payload = apify_post_search_input(max_posts=max_posts)
    owned = client is None
    http = client or httpx.Client(timeout=180.0)
    try:
        response = http.post(url, json=payload)
        response.raise_for_status()
        items = response.json()
        if not isinstance(items, list):
            items = items.get("items") or []
        return [normalize_apify_post(item, source="apify-post-search") for item in items]
    finally:
        if owned:
            http.close()


def run_serper(client: httpx.Client | None = None) -> list[dict]:
    key = _serper_key()
    owned = client is None
    http = client or httpx.Client(timeout=30.0)
    posts: list[dict] = []
    try:
        for query in serper_queries():
            response = http.post(
                SERPER_URL,
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": query, "num": 10, "gl": "de", "hl": "de"},
            )
            response.raise_for_status()
            for item in response.json().get("organic") or []:
                link = item.get("link") or ""
                if "linkedin.com" not in link:
                    continue
                posts.append(
                    {
                        "id": link,
                        "author": "",
                        "profile_url": "",
                        "headline": "",
                        "company": "",
                        "text": f"{item.get('title') or ''}\n{item.get('snippet') or ''}",
                        "url": link,
                        "posted_at": "",
                        "source": "serper",
                    }
                )
        return posts
    finally:
        if owned:
            http.close()


def configured_providers() -> list[str]:
    found = ["demo"]
    if os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN"):
        found.append("apify")
    if os.environ.get("BRIGHTDATA_API_KEY") or os.environ.get("BRIGHT_DATA_API_KEY"):
        found.append("brightdata")
    if os.environ.get("SERPER_API_KEY"):
        found.append("serper")
    return found
