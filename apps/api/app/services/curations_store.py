"""
Storage for anonymous_curations rows.

In-memory backend for local dev / tests; Supabase backend when configured.
The Phase 3 `auth.claim` flow will read from this store too — same Protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class CurationsStore(Protocol):
    def save_anonymous(
        self,
        *,
        anon_id: str,
        conference_id: str | None,
        onboarding: dict[str, Any],
        schedule: list[dict[str, Any]],
        tokens_used: int,
        model: str,
    ) -> None: ...

    def get_anonymous(self, anon_id: str) -> dict[str, Any] | None: ...


# ---------- in-memory backend ----------


class InMemoryCurationsStore:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def save_anonymous(
        self,
        *,
        anon_id: str,
        conference_id: str | None,
        onboarding: dict[str, Any],
        schedule: list[dict[str, Any]],
        tokens_used: int,
        model: str,
    ) -> None:
        with self._lock:
            self._rows[anon_id] = {
                "anon_id": anon_id,
                "conference_id": conference_id,
                "onboarding": onboarding,
                "schedule": schedule,
                "tokens_used": tokens_used,
                "model": model,
                "created_at": datetime.now(timezone.utc),
                "claimed_by": None,
                "claimed_at": None,
            }

    def get_anonymous(self, anon_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._rows.get(anon_id)
            return dict(row) if row else None


# ---------- supabase backend ----------


class SupabaseCurationsStore:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def save_anonymous(
        self,
        *,
        anon_id: str,
        conference_id: str | None,
        onboarding: dict[str, Any],
        schedule: list[dict[str, Any]],
        tokens_used: int,
        model: str,
    ) -> None:
        self._client.table("anonymous_curations").upsert(
            {
                "anon_id": anon_id,
                "conference_id": conference_id,
                "onboarding": onboarding,
                "schedule": schedule,
                "tokens_used": tokens_used,
                "model": model,
            },
            on_conflict="anon_id",
        ).execute()

    def get_anonymous(self, anon_id: str) -> dict[str, Any] | None:
        res = (
            self._client.table("anonymous_curations")
            .select("*")
            .eq("anon_id", anon_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None


# ---------- FastAPI dependency ----------


@lru_cache
def _build_store() -> CurationsStore:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseCurationsStore(settings)
    return InMemoryCurationsStore()


def get_curations_store() -> CurationsStore:
    return _build_store()
