from __future__ import annotations

from typing import Any


def localized(value: Any) -> str:
    """Flatten TED multilingual maps and nested lists into one German/English string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [localized(item) for item in value]
        return "; ".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("deu", "DEU", "eng", "ENG"):
            if key in value:
                return localized(value[key])
        return localized(next(iter(value.values()), ""))
    return str(value).strip()


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list) and value:
        return as_float(value[0])
    if isinstance(value, dict):
        for key in ("amount", "value", "deu", "eng"):
            if key in value:
                return as_float(value[key])
        return as_float(next(iter(value.values()), None))
    try:
        return float(str(value).replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


def join_text(*parts: Any) -> str:
    return " \n ".join(localized(part) for part in parts if localized(part))
