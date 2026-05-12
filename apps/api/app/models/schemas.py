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


# ============================================================================
# Onboarding + curation — mirrors apps/web/src/stores/onboardingStore.ts
# ============================================================================


class OnboardingState(BaseModel):
    """Exact mirror of the frontend OnboardingState. Field names match the TS."""

    conferenceId: str
    attendance: str | None = None  # 'full' | 'partial' | 'side-only'
    days: list[int] = Field(default_factory=list)
    role: str | None = None
    goals: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    pace: int = 50
    energy: int = 50
    social: int = 50
    mustHaves: list[str] = Field(default_factory=list)


class CuratedItem(BaseModel):
    event_id: str
    day: str
    start: str
    end: str
    rationale: str
    priority: str  # 'must' | 'should' | 'maybe'


class CurateRequest(BaseModel):
    onboarding: OnboardingState
    anon_id: str  # client-generated UUID v4
    model: str | None = None


class CurateResponse(BaseModel):
    curate_id: str
    schedule: list[CuratedItem]
    tokens_used: int
