"""
Storage for user_event_pins (pinned/hidden events).

pinned=True  → user wants this event added to their schedule
pinned=False → user wants this event explicitly hidden, even if curated
              (we keep the row instead of deleting so re-curate doesn't bring it back)
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class PinsStore(Protocol):
    def set_pin(self, user_id: str, event_id: str, pinned: bool) -> None: ...
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]: ...


class InMemoryPinsStore:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = RLock()

    def set_pin(self, user_id: str, event_id: str, pinned: bool) -> None:
        with self._lock:
            self._rows[(user_id, event_id)] = {
                "user_id": user_id,
                "event_id": event_id,
                "pinned": pinned,
                "pinned_at": datetime.now(timezone.utc),
            }

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for (u, _), r in self._rows.items() if u == user_id]


class SupabasePinsStore:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def set_pin(self, user_id: str, event_id: str, pinned: bool) -> None:
        self._client.table("user_event_pins").upsert(
            {
                "user_id": user_id,
                "event_id": event_id,
                "pinned": pinned,
                "pinned_at": "now()",
            },
            on_conflict="user_id,event_id",
        ).execute()

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return (
            self._client.table("user_event_pins")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        ) or []


@lru_cache
def _build_store() -> PinsStore:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabasePinsStore(settings)
    return InMemoryPinsStore()


def get_pins_store() -> PinsStore:
    return _build_store()
