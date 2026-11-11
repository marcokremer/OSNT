from __future__ import annotations

import io
import json
import zipfile
from datetime import date, timedelta
from typing import Any, Iterable

import httpx

from osnt.classify import classify
from osnt.companies import match_companies
from osnt.models import Notice
from osnt.textutil import as_float, localized

VERGABE_EXPORT = "https://oeffentlichevergabe.de/api/notice-exports"


def _party_names(release: dict[str, Any], roles: Iterable[str] | None = None) -> list[str]:
    names: list[str] = []
    wanted = set(roles or [])
    for party in release.get("parties") or []:
        party_roles = set(party.get("roles") or [])
        if wanted and party_roles and not (party_roles & wanted):
            continue
        name = party.get("name") or (party.get("identifier") or {}).get("legalName")
        if name:
            names.append(str(name))
    return names


def parse_ocds_package(package: dict[str, Any]) -> list[Notice]:
    notices: list[Notice] = []
    for release in package.get("releases") or []:
        tender = release.get("tender") or {}
        buyer = release.get("buyer") or {}
        title = localized(tender.get("title"))
        description = localized(tender.get("description"))
        buyer_name = localized(buyer.get("name")) or localized(
            (tender.get("procuringEntity") or {}).get("name")
        )
        tenderers = [
            localized(t.get("name") or (t.get("identifier") or {}).get("legalName"))
            for t in (tender.get("tenderers") or [])
        ]
        suppliers: list[str] = []
        value = None
        for award in release.get("awards") or []:
            for supplier in award.get("suppliers") or []:
                suppliers.append(localized(supplier.get("name")))
            value = as_float((award.get("value") or {}).get("amount")) or value
        winners = [n for n in [*tenderers, *suppliers] if n]
        blob = " ".join([title, description, buyer_name, " ".join(winners)])
        companies = match_companies(blob)
        if not companies:
            continue
        cpv = []
        for item in tender.get("items") or []:
            classification = item.get("classification") or {}
            if classification.get("scheme", "").upper() == "CPV" or classification.get("id"):
                cpv.append(str(classification.get("id")))
        ocid = localized(release.get("ocid") or release.get("id") or package.get("uri"))
        published = localized(release.get("date") or package.get("publishedDate"))
        notices.append(
            Notice(
                id=f"vergabe:{ocid}",
                source="vergabe",
                source_url=localized(package.get("uri")),
                published_at=published[:10] if published else "",
                title=title,
                description=description,
                buyer_name=buyer_name,
                winners=winners,
                companies=companies,
                cpv=[c for c in cpv if c and c != "None"],
                value_eur=value,
                tags=classify(blob, cpv),
                notice_type=",".join(release.get("tag") or []) or "vergabe",
            )
        )
    return notices


class VergabeClient:
    def __init__(self, client: httpx.Client | None = None, timeout: float = 60.0):
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def download_day(self, day: date) -> bytes:
        url = f"{VERGABE_EXPORT}?pubDay={day.isoformat()}&format=ocds.zip"
        response = self.client.get(url)
        response.raise_for_status()
        return response.content

    def notices_for_day(self, day: date) -> list[Notice]:
        payload = self.download_day(day)
        if len(payload) < 100:
            return []
        notices: list[Notice] = []
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for name in archive.namelist():
                if not name.endswith(".json"):
                    continue
                package = json.loads(archive.read(name))
                notices.extend(parse_ocds_package(package))
        return notices

    def ingest_recent(self, days: int = 1, lookback: int = 10) -> dict[str, Any]:
        """Walk backwards from yesterday until `days` non-empty exports are found."""
        collected: list[Notice] = []
        used: list[str] = []
        cursor = date.today() - timedelta(days=1)
        scanned = 0
        while len(used) < days and scanned < lookback:
            scanned += 1
            try:
                batch = self.notices_for_day(cursor)
            except httpx.HTTPError:
                cursor -= timedelta(days=1)
                continue
            if batch:
                collected.extend(batch)
                used.append(cursor.isoformat())
            cursor -= timedelta(days=1)
        return {"days": used, "notices": collected, "scanned": scanned}
