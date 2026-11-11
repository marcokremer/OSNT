from __future__ import annotations

from typing import Any, Iterable

import httpx

from osnt.classify import classify
from osnt.companies import COMPANIES, Company, match_companies
from osnt.models import Notice
from osnt.textutil import as_float, join_text, localized

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

TED_FIELDS = [
    "publication-number",
    "publication-date",
    "notice-title",
    "notice-type",
    "buyer-name",
    "buyer-country",
    "winner-name",
    "organisation-name-tenderer",
    "classification-cpv",
    "estimated-value-proc",
    "total-value",
    "description-proc",
    "contract-title",
    "title-lot",
    "title-proc",
]

IT_FILTER = "(classification-cpv=72* OR classification-cpv=48*)"
DE_FILTER = "buyer-country=DEU"


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def parse_notice(raw: dict[str, Any], source: str = "ted") -> Notice:
    pub = localized(raw.get("publication-number")) or localized(raw.get("id"))
    winners = _unique(
        [
            *localized(raw.get("winner-name")).split("; "),
            *localized(raw.get("organisation-name-tenderer")).split("; "),
        ]
    )
    winners = [w for w in winners if w]
    title = (
        localized(raw.get("notice-title"))
        or localized(raw.get("contract-title"))
        or localized(raw.get("title-proc"))
        or localized(raw.get("title-lot"))
    )
    description = join_text(raw.get("description-proc"), raw.get("title-lot"))
    buyer = localized(raw.get("buyer-name"))
    cpv = _unique(str(c) for c in (raw.get("classification-cpv") or []))
    blob = " ".join([title, description, buyer, " ".join(winners), " ".join(cpv)])
    companies = match_companies(" ".join(winners) + " " + blob)
    tags = classify(blob, cpv)
    value = as_float(raw.get("total-value"))
    if value is None:
        value = as_float(raw.get("estimated-value-proc"))
    published = localized(raw.get("publication-date")).rstrip("Z")
    return Notice(
        id=f"ted:{pub}" if not pub.startswith("ted:") else pub,
        source=source,
        source_url=f"https://ted.europa.eu/de/notice/-/detail/{pub}" if pub else "",
        published_at=published,
        title=title,
        description=description,
        buyer_name=buyer,
        winners=winners,
        companies=companies,
        cpv=cpv,
        value_eur=value if value and value > 1 else (value if value else None),
        tags=tags,
        notice_type=localized(raw.get("notice-type")),
        extra={"publication_number": pub},
    )


class TedClient:
    def __init__(self, client: httpx.Client | None = None, timeout: float = 45.0):
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def search(self, query: str, limit: int = 25, page: int = 1) -> dict[str, Any]:
        payload = {
            "query": query,
            "page": page,
            "limit": min(limit, 50),
            "fields": TED_FIELDS,
            "scope": "ALL",
            "paginationMode": "PAGE_NUMBER",
        }
        response = self.client.post(TED_SEARCH_URL, json=payload)
        response.raise_for_status()
        return response.json()

    def company_query(self, company: Company, germany: bool = True, it_only: bool = True) -> str:
        parts = [company.ted_winner_query]
        if germany:
            parts.append(DE_FILTER)
        if it_only:
            parts.append(IT_FILTER)
        return " AND ".join(parts)

    def iter_company_notices(
        self,
        company: Company,
        limit: int = 25,
        germany: bool = True,
        it_only: bool = True,
    ) -> tuple[int, list[Notice]]:
        query = self.company_query(company, germany=germany, it_only=it_only)
        collected: list[Notice] = []
        page = 1
        total = 0
        remaining = limit
        while remaining > 0:
            batch_size = min(50, remaining)
            data = self.search(query, limit=batch_size, page=page)
            total = int(data.get("totalNoticeCount") or 0)
            raw_notices = data.get("notices") or []
            if not raw_notices:
                break
            for raw in raw_notices:
                notice = parse_notice(raw)
                if company.id not in notice.companies:
                    notice.companies = list(dict.fromkeys([*notice.companies, company.id]))
                collected.append(notice)
            remaining -= len(raw_notices)
            if len(raw_notices) < batch_size:
                break
            page += 1
        return total, collected[:limit]

    def ingest_all(self, limit_per_company: int = 25) -> dict[str, Any]:
        summary: dict[str, Any] = {"companies": {}, "notices": []}
        for company in COMPANIES:
            total, notices = self.iter_company_notices(company, limit=limit_per_company)
            summary["companies"][company.id] = {
                "label": company.label,
                "available": total,
                "ingested": len(notices),
            }
            summary["notices"].extend(notices)
        return summary
