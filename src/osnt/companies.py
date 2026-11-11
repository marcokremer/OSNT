from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    id: str
    label: str
    aliases: tuple[str, ...]
    ted_winner_query: str


COMPANIES: tuple[Company, ...] = (
    Company(
        "accenture",
        "Accenture",
        ("accenture",),
        'winner-name="Accenture"',
    ),
    Company(
        "deloitte",
        "Deloitte",
        ("deloitte",),
        'winner-name="Deloitte"',
    ),
    Company(
        "capgemini",
        "Capgemini",
        ("capgemini",),
        'winner-name="Capgemini"',
    ),
    Company(
        "bearingpoint",
        "BearingPoint",
        ("bearingpoint", "bearing point"),
        'winner-name="BearingPoint"',
    ),
    Company(
        "t-systems",
        "T-Systems",
        ("t-systems", "t systems"),
        'winner-name="T-Systems"',
    ),
    Company(
        "bechtle",
        "Bechtle",
        ("bechtle",),
        'winner-name="Bechtle"',
    ),
    Company(
        "pwc",
        "PwC",
        ("pwc", "pricewaterhousecoopers", "pricewaterhouse coopers"),
        '(winner-name="PricewaterhouseCoopers" OR winner-name="PwC")',
    ),
    Company(
        "init",
        "]init[",
        ("]init[", "init ag für digitale", "init ag fuer digitale"),
        'winner-name="]init["',
    ),
)

COMPANY_BY_ID = {c.id: c for c in COMPANIES}


def match_companies(text: str) -> list[str]:
    """Return company ids mentioned in free text (winner names, descriptions)."""
    blob = (text or "").lower()
    if not blob:
        return []
    hits: list[str] = []
    for company in COMPANIES:
        if any(alias in blob for alias in company.aliases):
            hits.append(company.id)
    return hits
