from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    id: str
    label: str
    aliases: tuple[str, ...]
    linkedin_company: str
    search_names: tuple[str, ...]


COMPANIES: tuple[Company, ...] = (
    Company(
        "accenture",
        "Accenture",
        ("accenture",),
        "https://www.linkedin.com/company/accenture",
        ("Accenture", "Accenture GmbH"),
    ),
    Company(
        "deloitte",
        "Deloitte",
        ("deloitte",),
        "https://www.linkedin.com/company/deloitte",
        ("Deloitte", "Deloitte Consulting"),
    ),
    Company(
        "capgemini",
        "Capgemini",
        ("capgemini",),
        "https://www.linkedin.com/company/capgemini",
        ("Capgemini", "Capgemini Deutschland"),
    ),
    Company(
        "bearingpoint",
        "BearingPoint",
        ("bearingpoint", "bearing point"),
        "https://www.linkedin.com/company/bearingpoint",
        ("BearingPoint",),
    ),
    Company(
        "t-systems",
        "T-Systems",
        ("t-systems", "t systems"),
        "https://www.linkedin.com/company/t-systems",
        ("T-Systems",),
    ),
    Company(
        "bechtle",
        "Bechtle",
        ("bechtle",),
        "https://www.linkedin.com/company/bechtle-ag",
        ("Bechtle",),
    ),
    Company(
        "pwc",
        "PwC",
        ("pwc", "pricewaterhousecoopers", "pricewaterhouse coopers"),
        "https://www.linkedin.com/company/pwc",
        ("PwC", "PricewaterhouseCoopers"),
    ),
    Company(
        "init",
        "]init[",
        ("]init[", "init ag für digitale", "init ag fuer digitale"),
        "https://www.linkedin.com/company/init",
        ("]init[", "init AG"),
    ),
)

COMPANY_BY_ID = {c.id: c for c in COMPANIES}


def match_companies(text: str) -> list[str]:
    blob = (text or "").lower()
    if not blob:
        return []
    hits: list[str] = []
    for company in COMPANIES:
        if any(alias in blob for alias in company.aliases):
            hits.append(company.id)
    return hits
