"""Scraper integration boundary.

A new scraper drops a file under `app/scraper/sources/<id>.py` that exports a class
satisfying `EventSource`. Register it in `registry.py`.

The user's existing scraper code can be pasted into a new source module and wrapped to match
this protocol — the scraper itself doesn't have to be rewritten, just adapted to return
`EventDTO`s and accept a `conference_id`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class EventDTO(BaseModel):
    id: str  # stable id, e.g. "{conference}:{slug}"
    conference_id: str
    title: str
    description: str = ""
    start: datetime
    end: datetime
    venue: str = ""
    tags: list[str] = Field(default_factory=list)
    url: str | None = None
    capacity: int | None = None
    attendees: int | None = None
    source: str | None = None  # which scraper produced this row


@runtime_checkable
class EventSource(Protocol):
    """A scrape target. Implementations live in `app/scraper/sources/`."""

    id: str

    async def fetch_events(self, conference_id: str) -> list[EventDTO]: ...
