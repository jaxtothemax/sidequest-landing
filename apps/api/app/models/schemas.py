from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OnboardingState(BaseModel):
    conference_id: str
    attendance: Literal["full", "partial", "side-only"] | None = None
    days: list[int] = Field(default_factory=list)
    role: str | None = None
    goals: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    pace: int = 50
    energy: int = 50
    social: int = 50
    must_haves: list[str] = Field(default_factory=list, alias="mustHaves")

    model_config = {"populate_by_name": True}


class EventDTO(BaseModel):
    id: str
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
    source: str | None = None


class CuratedItem(BaseModel):
    event_id: str
    day: str
    start: str
    end: str
    rationale: str
    priority: Literal["must", "should", "maybe"] = "should"


class CurateRequest(BaseModel):
    onboarding: OnboardingState
    model: str | None = None


class CurateResponse(BaseModel):
    schedule: list[CuratedItem]
    tokens_used: int = 0


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: dict[str, str] | None = None
    model: str | None = None


class PinRequest(BaseModel):
    event_id: str
    pinned: bool = True


class PinResponse(BaseModel):
    ok: bool
    user_event: dict[str, str | bool | None] | None = None


class EventsResponse(BaseModel):
    events: list[EventDTO]
    conference: dict[str, str] | None = None
