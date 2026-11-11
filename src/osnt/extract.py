from __future__ import annotations

import re
from typing import Iterable

from osnt.classify import classify

CUSTOMERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ITZBund", ("itzbund", "informationstechnikzentrum bund")),
    ("BMI", ("beschaffungsamt des bmi", "bundesministerium des innern", r"\bbmi\b")),
    ("BKA", (r"\bbka\b", "bundeskriminalamt")),
    ("BSI", (r"\bbsi\b", "bundesamt für sicherheit in der informationstechnik")),
    ("BVA", (r"\bbva\b", "bundesverwaltungsamt")),
    ("Bundeswehr / BAAINBw", ("bundeswehr", "baainbw")),
    ("BA (Bundesagentur für Arbeit)", ("bundesagentur für arbeit", r"\barbeitsagentur\b")),
    ("DRV Bund", ("deutsche rentenversicherung", r"\bdrv\b")),
    ("Destatis", ("destatis", "statistisches bundesamt")),
    ("KfW", (r"\bkfw\b",)),
    ("byte Bayern", ("byte bayern", "bayerische agentur für digitales")),
    ("LGL Bayern", ("landesamt für gesundheit", r"\blgl\b")),
    ("Polizei Berlin", ("polizei berlin",)),
    ("ITZ Bund-nahe / ÖGD", ("ögd", "öffentlicher gesundheitsdienst")),
    ("Kommune / Stadtverwaltung", ("stadtverwaltung", "landeshauptstadt", "kommune")),
    ("LfU Brandenburg", ("landesamt für umwelt", r"\blfu\b")),
    ("Landesverwaltung", ("landesverwaltung",)),
)

PUBLIC_SECTOR = (
    r"öffentlich\w* sektor",
    r"öffentlich\w* verwaltung",
    r"public sector",
    r"government",
    r"bundesverwaltung",
    r"landesverwaltung",
    r"kommunal",
    r"ministerium",
    r"landesamt",
    r"bundesamt",
    r"verwaltungsdigitalisierung",
    r"onlinezugangsgesetz",
    r"\bozg\b",
    r"e-government",
    r"egovernment",
)

PROJECT_PATTERNS = (
    re.compile(r"(?:Projekt|Projektname|Projekttitel)\s+[\"„']?([A-ZÄÖÜ][\w\- /]{2,50})"),
    re.compile(r"Rahmenvertrag\s+[\"„']?([A-ZÄÖÜ][\w\- /]{2,50})"),
    re.compile(r"Einführung\s+(?:von\s+)?[\"„']?([A-ZÄÖÜ][\w\- /]{2,50})"),
)

DATA_AI_HINTS = (
    r"datenplattform",
    r"data platform",
    r"data lake",
    r"lakehouse",
    r"databricks",
    r"künstlich\w* intelligenz",
    r"\bki\b",
    r"\bai\b",
    r"machine learning",
    r"genai",
    r"llm",
    r"azure",
    r"analytics",
)


def _search(blob: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, blob, re.I) for p in patterns)


def extract_customers(text: str) -> list[str]:
    blob = text or ""
    found: list[str] = []
    for label, patterns in CUSTOMERS:
        if any(re.search(p, blob, re.I) for p in patterns):
            found.append(label)
    return found


def extract_projects(text: str) -> list[str]:
    found: list[str] = []
    for pattern in PROJECT_PATTERNS:
        for match in pattern.findall(text or ""):
            value = re.sub(r"\s+", " ", str(match)).strip(" .,;:-")
            if 3 < len(value) < 80:
                found.append(value)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for item in found:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out[:8]


def is_public_sector(text: str) -> bool:
    blob = text or ""
    return bool(extract_customers(blob)) or _search(blob, PUBLIC_SECTOR)


def is_data_or_ai(text: str) -> bool:
    tags = classify(text or "")
    return "ai" in tags or "data_platform" in tags or _search(text or "", DATA_AI_HINTS)


def analyze_post(text: str, headline: str = "") -> dict:
    blob = f"{headline}\n{text}"
    tags = classify(blob)
    customers = extract_customers(blob)
    projects = extract_projects(text)
    public = is_public_sector(blob)
    data_ai = is_data_or_ai(blob)
    if public:
        tags = list(dict.fromkeys([*tags, "public_sector"]))
    in_scope = public and data_ai
    if in_scope:
        tags = list(dict.fromkeys([*tags, "in_scope"]))
    return {
        "tags": tags,
        "customers": customers,
        "projects": projects,
        "public_sector": public,
        "data_ai": data_ai,
        "in_scope": in_scope,
    }


def person_in_scope(headline: str, about: str = "", post_texts: Iterable[str] = ()) -> bool:
    blob = " ".join([headline, about, *post_texts])
    return is_data_or_ai(blob) and is_public_sector(blob)
