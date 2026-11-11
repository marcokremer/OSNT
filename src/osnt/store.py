from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from osnt.models import Notice, Person

SCHEMA = """
CREATE TABLE IF NOT EXISTS notices (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  source_url TEXT,
  published_at TEXT,
  title TEXT,
  description TEXT,
  buyer_name TEXT,
  winners_json TEXT,
  companies_json TEXT,
  cpv_json TEXT,
  value_eur REAL,
  tags_json TEXT,
  notice_type TEXT,
  extra_json TEXT
);

CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  company TEXT,
  role TEXT,
  customer TEXT,
  project TEXT,
  source TEXT,
  source_url TEXT,
  notes TEXT,
  UNIQUE(name, company, role, customer)
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

    def upsert_notice(self, notice: Notice) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO notices (
                  id, source, source_url, published_at, title, description,
                  buyer_name, winners_json, companies_json, cpv_json, value_eur,
                  tags_json, notice_type, extra_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  source=excluded.source,
                  source_url=excluded.source_url,
                  published_at=excluded.published_at,
                  title=excluded.title,
                  description=excluded.description,
                  buyer_name=excluded.buyer_name,
                  winners_json=excluded.winners_json,
                  companies_json=excluded.companies_json,
                  cpv_json=excluded.cpv_json,
                  value_eur=excluded.value_eur,
                  tags_json=excluded.tags_json,
                  notice_type=excluded.notice_type,
                  extra_json=excluded.extra_json
                """,
                (
                    notice.id,
                    notice.source,
                    notice.source_url,
                    notice.published_at,
                    notice.title,
                    notice.description,
                    notice.buyer_name,
                    json.dumps(notice.winners, ensure_ascii=False),
                    json.dumps(notice.companies, ensure_ascii=False),
                    json.dumps(notice.cpv, ensure_ascii=False),
                    notice.value_eur,
                    json.dumps(notice.tags, ensure_ascii=False),
                    notice.notice_type,
                    json.dumps(notice.extra, ensure_ascii=False),
                ),
            )

    def _row_to_notice(self, row: sqlite3.Row) -> Notice:
        return Notice(
            id=row["id"],
            source=row["source"],
            source_url=row["source_url"] or "",
            published_at=row["published_at"] or "",
            title=row["title"] or "",
            description=row["description"] or "",
            buyer_name=row["buyer_name"] or "",
            winners=json.loads(row["winners_json"] or "[]"),
            companies=json.loads(row["companies_json"] or "[]"),
            cpv=json.loads(row["cpv_json"] or "[]"),
            value_eur=row["value_eur"],
            tags=json.loads(row["tags_json"] or "[]"),
            notice_type=row["notice_type"] or "",
            extra=json.loads(row["extra_json"] or "{}"),
        )

    def list_notices(
        self,
        company: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        focus_only: bool = False,
        limit: int = 200,
    ) -> list[Notice]:
        sql = "SELECT * FROM notices WHERE 1=1"
        params: list[object] = []
        if company:
            sql += " AND companies_json LIKE ?"
            params.append(f'%"{company}"%')
        if tag:
            sql += " AND tags_json LIKE ?"
            params.append(f'%"{tag}"%')
        if focus_only:
            sql += " AND (tags_json LIKE '%\"ai\"%' OR tags_json LIKE '%\"data_platform\"%')"
        if q:
            sql += " AND (title LIKE ? OR description LIKE ? OR buyer_name LIKE ?)"
            like = f"%{q}%"
            params.extend([like, like, like])
        sql += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_notice(r) for r in rows]

    def stats(self) -> dict[str, object]:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
            people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
            customers = conn.execute(
                "SELECT COUNT(DISTINCT buyer_name) FROM notices WHERE buyer_name != ''"
            ).fetchone()[0]
            by_company = conn.execute(
                "SELECT companies_json FROM notices"
            ).fetchall()
            by_tag = conn.execute("SELECT tags_json FROM notices").fetchall()
        company_counts: dict[str, int] = {}
        for (payload,) in by_company:
            for cid in json.loads(payload or "[]"):
                company_counts[cid] = company_counts.get(cid, 0) + 1
        tag_counts: dict[str, int] = {}
        for (payload,) in by_tag:
            for tag in json.loads(payload or "[]"):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return {
            "notices": total,
            "customers": customers,
            "people": people,
            "by_company": company_counts,
            "by_tag": tag_counts,
        }

    def customers(self, company: str | None = None) -> list[dict[str, object]]:
        notices = self.list_notices(company=company, limit=2000)
        buckets: dict[str, dict[str, object]] = {}
        for notice in notices:
            name = notice.buyer_name or "Unbekannt"
            bucket = buckets.setdefault(
                name,
                {"name": name, "projects": 0, "companies": set(), "value_eur": 0.0},
            )
            bucket["projects"] = int(bucket["projects"]) + 1
            companies = bucket["companies"]
            assert isinstance(companies, set)
            companies.update(notice.companies)
            if notice.value_eur:
                bucket["value_eur"] = float(bucket["value_eur"]) + notice.value_eur
        rows = []
        for bucket in buckets.values():
            companies = bucket["companies"]
            assert isinstance(companies, set)
            rows.append(
                {
                    "name": bucket["name"],
                    "projects": bucket["projects"],
                    "companies": sorted(companies),
                    "value_eur": bucket["value_eur"],
                }
            )
        rows.sort(key=lambda r: int(r["projects"]), reverse=True)
        return rows

    def insert_person(self, person: Person) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO people
                  (name, company, role, customer, project, source, source_url, notes)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    person.name.strip(),
                    person.company.strip(),
                    person.role.strip(),
                    person.customer.strip(),
                    person.project.strip(),
                    person.source,
                    person.source_url,
                    person.notes,
                ),
            )

    def list_people(self, company: str | None = None) -> list[Person]:
        sql = "SELECT * FROM people"
        params: list[object] = []
        if company:
            sql += " WHERE lower(company) LIKE ?"
            params.append(f"%{company.lower()}%")
        sql += " ORDER BY company, name"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            Person(
                id=row["id"],
                name=row["name"],
                company=row["company"] or "",
                role=row["role"] or "",
                customer=row["customer"] or "",
                project=row["project"] or "",
                source=row["source"] or "",
                source_url=row["source_url"] or "",
                notes=row["notes"] or "",
            )
            for row in rows
        ]

    def record_run(self, source: str, status: str, stats: dict[str, object]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO ingest_runs (source, started_at, finished_at, status, stats_json)
                VALUES (?,?,?,?,?)
                """,
                (source, utc_now(), utc_now(), status, json.dumps(stats, ensure_ascii=False)),
            )

    def notice_count(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0])
