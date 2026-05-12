"""
Storage for user_entitlements (paywall state).

Same dual-backend pattern as the other stores. /api/unlock writes here;
later phases (chat, schedule access checks) will read from it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class EntitlementsStore(Protocol):
    def unlock(self, user_id: str, *, provider: str = "stub") -> None: ...
    def get(self, user_id: str) -> dict[str, Any] | None: ...


class InMemoryEntitlementsStore:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def unlock(self, user_id: str, *, provider: str = "stub") -> None:
        with self._lock:
            self._rows[user_id] = {
                "user_id": user_id,
                "unlocked": True,
                "unlocked_at": datetime.now(timezone.utc),
                "provider": provider,
                "provider_ref": None,
                "expires_at": None,
            }

    def get(self, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._rows.get(user_id)
            return dict(row) if row else None


class SupabaseEntitlementsStore:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def unlock(self, user_id: str, *, provider: str = "stub") -> None:
        self._client.table("user_entitlements").upsert(
            {
                "user_id": user_id,
                "unlocked": True,
                "unlocked_at": "now()",
                "provider": provider,
            },
            on_conflict="user_id",
        ).execute()

    def get(self, user_id: str) -> dict[str, Any] | None:
        rows = (
            self._client.table("user_entitlements")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
        ) or []
        return rows[0] if rows else None


@lru_cache
def _build_store() -> EntitlementsStore:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseEntitlementsStore(settings)
    return InMemoryEntitlementsStore()


def get_entitlements_store() -> EntitlementsStore:
    return _build_store()
