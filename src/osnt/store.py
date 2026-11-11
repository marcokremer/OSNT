from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from osnt.models import Person, Post

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  company TEXT,
  headline TEXT,
  location TEXT,
  profile_url TEXT,
  about TEXT,
  in_scope INTEGER,
  source TEXT
);

CREATE TABLE IF NOT EXISTS posts (
  id TEXT PRIMARY KEY,
  person_id TEXT,
  company TEXT,
  author TEXT,
  url TEXT,
  text TEXT,
  posted_at TEXT,
  tags_json TEXT,
  customers_json TEXT,
  projects_json TEXT,
  in_scope INTEGER,
  source TEXT
);

CREATE TABLE IF NOT EXISTS ingest_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT,
  stats_json TEXT
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_person(self, person: Person) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO people (id, name, company, headline, location, profile_url, about, in_scope, source)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  name=excluded.name,
                  company=excluded.company,
                  headline=excluded.headline,
                  location=excluded.location,
                  profile_url=excluded.profile_url,
                  about=excluded.about,
                  in_scope=excluded.in_scope,
                  source=excluded.source
                """,
                (
                    person.id,
                    person.name,
                    person.company,
                    person.headline,
                    person.location,
                    person.profile_url,
                    person.about,
                    int(person.in_scope),
                    person.source,
                ),
            )

    def upsert_post(self, post: Post) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO posts (
                  id, person_id, company, author, url, text, posted_at,
                  tags_json, customers_json, projects_json, in_scope, source
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  person_id=excluded.person_id,
                  company=excluded.company,
                  author=excluded.author,
                  url=excluded.url,
                  text=excluded.text,
                  posted_at=excluded.posted_at,
                  tags_json=excluded.tags_json,
                  customers_json=excluded.customers_json,
                  projects_json=excluded.projects_json,
                  in_scope=excluded.in_scope,
                  source=excluded.source
                """,
                (
                    post.id,
                    post.person_id,
                    post.company,
                    post.author,
                    post.url,
                    post.text,
                    post.posted_at,
                    json.dumps(post.tags, ensure_ascii=False),
                    json.dumps(post.customers, ensure_ascii=False),
                    json.dumps(post.projects, ensure_ascii=False),
                    int(post.in_scope),
                    post.source,
                ),
            )

    def _person(self, row: sqlite3.Row) -> Person:
        return Person(
            id=row["id"],
            name=row["name"],
            company=row["company"] or "",
            headline=row["headline"] or "",
            location=row["location"] or "",
            profile_url=row["profile_url"] or "",
            about=row["about"] or "",
            in_scope=bool(row["in_scope"]),
            source=row["source"] or "",
        )

    def _post(self, row: sqlite3.Row) -> Post:
        return Post(
            id=row["id"],
            person_id=row["person_id"] or "",
            company=row["company"] or "",
            author=row["author"] or "",
            url=row["url"] or "",
            text=row["text"] or "",
            posted_at=row["posted_at"] or "",
            tags=json.loads(row["tags_json"] or "[]"),
            customers=json.loads(row["customers_json"] or "[]"),
            projects=json.loads(row["projects_json"] or "[]"),
            in_scope=bool(row["in_scope"]),
            source=row["source"] or "",
        )

    def list_people(self, company: str | None = None, in_scope: bool | None = True) -> list[Person]:
        sql = "SELECT * FROM people WHERE 1=1"
        params: list[object] = []
        if company:
            sql += " AND company = ?"
            params.append(company)
        if in_scope is True:
            sql += " AND in_scope = 1"
        sql += " ORDER BY company, name"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._person(r) for r in rows]

    def list_posts(
        self,
        company: str | None = None,
        q: str | None = None,
        in_scope: bool | None = True,
        limit: int = 300,
    ) -> list[Post]:
        sql = "SELECT * FROM posts WHERE 1=1"
        params: list[object] = []
        if company:
            sql += " AND company = ?"
            params.append(company)
        if in_scope is True:
            sql += " AND in_scope = 1"
        if q:
            sql += " AND (text LIKE ? OR author LIKE ? OR customers_json LIKE ?)"
            like = f"%{q}%"
            params.extend([like, like, like])
        sql += " ORDER BY posted_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._post(r) for r in rows]

    def customers(self, company: str | None = None) -> list[dict]:
        posts = self.list_posts(company=company, in_scope=True, limit=2000)
        buckets: dict[str, dict] = {}
        for post in posts:
            for name in post.customers:
                bucket = buckets.setdefault(
                    name,
                    {"name": name, "mentions": 0, "people": set(), "companies": set(), "projects": set()},
                )
                bucket["mentions"] += 1
                bucket["people"].add(post.author or post.person_id)
                bucket["companies"].add(post.company)
                bucket["projects"].update(post.projects)
        rows = []
        for bucket in buckets.values():
            rows.append(
                {
                    "name": bucket["name"],
                    "mentions": bucket["mentions"],
                    "people": sorted(bucket["people"]),
                    "companies": sorted(bucket["companies"]),
                    "projects": sorted(bucket["projects"]),
                }
            )
        rows.sort(key=lambda r: r["mentions"], reverse=True)
        return rows

    def projects(self, company: str | None = None) -> list[dict]:
        posts = self.list_posts(company=company, in_scope=True, limit=2000)
        buckets: dict[str, dict] = {}
        for post in posts:
            for name in post.projects or ["(ohne Projektname, nur Kundensignal)"]:
                if not post.projects and not post.customers:
                    continue
                if not post.projects:
                    name = f"Erwähnung: {', '.join(post.customers)}"
                bucket = buckets.setdefault(
                    name,
                    {"name": name, "mentions": 0, "customers": set(), "companies": set(), "people": set()},
                )
                bucket["mentions"] += 1
                bucket["customers"].update(post.customers)
                bucket["companies"].add(post.company)
                bucket["people"].add(post.author or post.person_id)
        rows = []
        for bucket in buckets.values():
            rows.append(
                {
                    "name": bucket["name"],
                    "mentions": bucket["mentions"],
                    "customers": sorted(bucket["customers"]),
                    "companies": sorted(bucket["companies"]),
                    "people": sorted(bucket["people"]),
                }
            )
        rows.sort(key=lambda r: r["mentions"], reverse=True)
        return rows

    def stats(self) -> dict:
        with self.connect() as conn:
            people = conn.execute("SELECT COUNT(*) FROM people WHERE in_scope = 1").fetchone()[0]
            people_all = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
            posts = conn.execute("SELECT COUNT(*) FROM posts WHERE in_scope = 1").fetchone()[0]
            posts_all = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            company_rows = conn.execute(
                "SELECT company, COUNT(*) n FROM people WHERE in_scope = 1 GROUP BY company"
            ).fetchall()
        customers = self.customers()
        projects = self.projects()
        return {
            "people": people,
            "people_all": people_all,
            "posts": posts,
            "posts_all": posts_all,
            "customers": len(customers),
            "projects": len(projects),
            "by_company": {row["company"]: row["n"] for row in company_rows if row["company"]},
        }

    def record_run(self, source: str, status: str, stats: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO ingest_runs (source, started_at, finished_at, status, stats_json)
                VALUES (?,?,?,?,?)
                """,
                (source, utc_now(), utc_now(), status, json.dumps(stats, ensure_ascii=False)),
            )

    def counts(self) -> dict[str, int]:
        with self.connect() as conn:
            return {
                "people": int(conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]),
                "posts": int(conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]),
            }
