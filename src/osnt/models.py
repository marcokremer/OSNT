from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Notice(BaseModel):
    id: str
    source: str
    source_url: str = ""
    published_at: str = ""
    title: str = ""
    description: str = ""
    buyer_name: str = ""
    winners: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    cpv: list[str] = Field(default_factory=list)
    value_eur: float | None = None
    tags: list[str] = Field(default_factory=list)
    notice_type: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class Person(BaseModel):
    id: int | None = None
    name: str
    company: str = ""
    role: str = ""
    customer: str = ""
    project: str = ""
    source: str = "import"
    source_url: str = ""
    notes: str = ""
