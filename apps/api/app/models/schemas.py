from __future__ import annotations

from datetime import date as date_t, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConferenceDayOut(BaseModel):
    day_num: int = Field(..., serialization_alias="num")
    dow: str
    date: date_t | None = None
    enabled: bool

    model_config = ConfigDict(populate_by_name=True)


class ConferenceOut(BaseModel):
    id: str
    name: str
    city: str | None = None
    venue: str | None = None
    start_date: date_t | None = None
    end_date: date_t | None = None
    timezone: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    days: list[ConferenceDayOut] = Field(default_factory=list)


class EventOut(BaseModel):
    """Matches the frontend Event type in apps/web/src/types/index.ts."""

    id: str
    conference_id: str
    title: str
    description: str | None = None
    start: datetime
    end: datetime
    venue: str | None = None
    tags: list[str] = Field(default_factory=list)
    url: str | None = None
    capacity: int | None = None
    attendees: int | None = None


class SuggestionOut(BaseModel):
    id: str
    conference_id: str
    kind: str
    name: str
    role: str | None = None
