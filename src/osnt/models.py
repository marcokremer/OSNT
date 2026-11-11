from __future__ import annotations

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str
    name: str
    company: str
    headline: str = ""
    location: str = ""
    profile_url: str = ""
    about: str = ""
    in_scope: bool = False
    source: str = "linkedin"


class Post(BaseModel):
    id: str
    person_id: str
    company: str
    author: str = ""
    url: str = ""
    text: str = ""
    posted_at: str = ""
    tags: list[str] = Field(default_factory=list)
    customers: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    in_scope: bool = False
    source: str = "linkedin"
