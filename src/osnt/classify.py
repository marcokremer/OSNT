from __future__ import annotations

import re
from typing import Iterable

IT_CPV_PREFIXES = ("48", "72")

AI_PATTERNS = (
    r"künstlich\w* intelligenz",
    r"kuenstlich\w* intelligenz",
    r"artificial intelligence",
    r"\bki\b",
    r"ki-pilot",
    r"ki-service",
    r"\bgenai\b",
    r"generative ki",
    r"generative ai",
    r"machine learning",
    r"maschinelles lernen",
    r"\bllm\b",
    r"large language",
    r"deep learning",
    r"\bnlp\b",
    r"computer vision",
    r"sprachmodell",
    r"ki-gestützt",
    r"ki gestuetzt",
    r"ki-anwendung",
    r"\bcopilot\b",
    r"\bchatbot\b",
)

PLATFORM_PATTERNS = (
    r"datenplattform",
    r"data platform",
    r"data lake",
    r"datenlake",
    r"data warehouse",
    r"datenwarehouse",
    r"databricks",
    r"snowflake",
    r"big data",
    r"analytics platform",
    r"analyseplattform",
    r"container-plattform",
    r"container plattform",
    r"kubernetes",
    r"azure",
    r"\baws\b",
    r"google cloud",
    r"sap datasphere",
    r"sap bw",
    r"microsoft fabric",
    r"cdp\b",
    r"datenhaltung",
    r"data hub",
    r"lakehouse",
)

RESELLER_PATTERNS = (
    r"produkte des herstellers",
    r"lizenz",
    r"lizenzen",
    r"hardware",
    r"endgeräte",
    r"endgeraete",
    r"notebook",
    r"pc-arbeitsplatz",
    r"pc arbeitsplatz",
)


def _compile(patterns: Iterable[str]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, re.IGNORECASE) for p in patterns)


_AI = _compile(AI_PATTERNS)
_PLATFORM = _compile(PLATFORM_PATTERNS)
_RESELLER = _compile(RESELLER_PATTERNS)


def is_it_cpv(cpv_codes: Iterable[str] | None) -> bool:
    for code in cpv_codes or []:
        digits = re.sub(r"\D", "", str(code))
        if digits.startswith(IT_CPV_PREFIXES):
            return True
    return False


def classify(text: str, cpv_codes: Iterable[str] | None = None) -> list[str]:
    """Tag LinkedIn text (and optional CPV if a notice is mixed in)."""
    blob = text or ""
    tags: list[str] = []
    if is_it_cpv(cpv_codes):
        tags.append("it")
    if any(p.search(blob) for p in _AI):
        tags.append("ai")
    if any(p.search(blob) for p in _PLATFORM):
        tags.append("data_platform")
    if any(p.search(blob) for p in _RESELLER) and "ai" not in tags:
        tags.append("reseller")
    if "it" in tags and "reseller" not in tags:
        tags.append("it_services")
    return tags


def in_focus(tags: Iterable[str]) -> bool:
    tag_set = set(tags)
    return "it" in tag_set and ("ai" in tag_set or "data_platform" in tag_set)
