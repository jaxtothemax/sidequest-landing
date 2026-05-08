"""Thin wrappers around the Supabase service-role client for the API routes + scraper.

Kept narrow — most route handlers should call `get_supabase()` from `app.deps` and use the
fluent client directly. These helpers just centralise the table names + any common queries.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def service_client():
    from supabase import create_client  # type: ignore[import-not-found]

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


TABLE_PROFILES = "profiles"
TABLE_ONBOARDING = "onboarding_state"
TABLE_EVENTS = "events"
TABLE_USER_EVENTS = "user_events"
TABLE_CHAT = "chat_messages"


def upsert_events(rows: list[dict[str, Any]]) -> None:
    """Bulk upsert events from a scraper run. Uses service-role client."""
    if not rows:
        return
    sb = service_client()
    sb.table(TABLE_EVENTS).upsert(rows, on_conflict="id").execute()
