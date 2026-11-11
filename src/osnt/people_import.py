from __future__ import annotations

import csv
import io
from typing import Iterable

from osnt.models import Person

NAME_KEYS = ("name", "full name", "fullname")
FIRST_KEYS = ("first name", "firstname", "vorname")
LAST_KEYS = ("last name", "lastname", "nachname")
COMPANY_KEYS = ("company", "current company", "firma", "organisation", "organization")
ROLE_KEYS = ("role", "title", "position", "headline", "job title")
CUSTOMER_KEYS = ("customer", "kunde", "account")
PROJECT_KEYS = ("project", "projekt")
URL_KEYS = ("profile url", "linkedin url", "url", "source_url")
NOTES_KEYS = ("notes", "notiz", "about")


def _norm(row: dict[str, str]) -> dict[str, str]:
    return {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}


def _first(row: dict[str, str], keys: Iterable[str]) -> str:
    for key in keys:
        if row.get(key):
            return row[key]
    return ""


def parse_people_csv(text: str, source: str = "csv-import") -> list[Person]:
    """Accept OSNT CSV or a Sales Navigator / Recruiter export subset."""
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    people: list[Person] = []
    for raw in reader:
        row = _norm(raw)
        name = _first(row, NAME_KEYS)
        if not name:
            first = _first(row, FIRST_KEYS)
            last = _first(row, LAST_KEYS)
            name = " ".join(part for part in (first, last) if part)
        if not name:
            continue
        people.append(
            Person(
                name=name,
                company=_first(row, COMPANY_KEYS),
                role=_first(row, ROLE_KEYS),
                customer=_first(row, CUSTOMER_KEYS),
                project=_first(row, PROJECT_KEYS),
                source=source,
                source_url=_first(row, URL_KEYS),
                notes=_first(row, NOTES_KEYS),
            )
        )
    return people
