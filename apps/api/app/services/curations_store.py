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

    def mark_claimed(self, anon_id: str, user_id: str) -> None: ...

    def claim_anonymous(self, anon_id: str, user_id: str) -> str:
        """Copy anonymous_curations[anon_id] into user_curations for user_id.

        Returns the new user_curation id. Raises KeyError if not found,
        ValueError if already claimed.
        """
        ...

    def get_active_user_curation(
        self, user_id: str, conference_id: str | None = None
    ) -> dict[str, Any] | None: ...


# ---------- in-memory backend ----------


class InMemoryCurationsStore:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._user_rows: dict[str, dict[str, Any]] = {}  # keyed by user_curation_id
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

    def mark_claimed(self, anon_id: str, user_id: str) -> None:
        with self._lock:
            if anon_id in self._rows:
                self._rows[anon_id]["claimed_by"] = user_id
                self._rows[anon_id]["claimed_at"] = datetime.now(timezone.utc)

    def claim_anonymous(self, anon_id: str, user_id: str) -> str:
        import uuid as _uuid

        with self._lock:
            row = self._rows.get(anon_id)
            if row is None:
                raise KeyError(anon_id)
            if row.get("claimed_by") is not None:
                raise ValueError("already claimed")
            uc_id = str(_uuid.uuid4())
            conf_id = row["conference_id"]
            # deactivate prior actives for this (user, conference)
            for prior in self._user_rows.values():
                if prior["user_id"] == user_id and prior["conference_id"] == conf_id:
                    prior["is_active"] = False
            self._user_rows[uc_id] = {
                "id": uc_id,
                "user_id": user_id,
                "conference_id": conf_id,
                "onboarding": row["onboarding"],
                "schedule": row["schedule"],
                "is_active": True,
                "source_anon_id": anon_id,
                "tokens_used": row["tokens_used"],
                "model": row["model"],
                "created_at": datetime.now(timezone.utc),
            }
            row["claimed_by"] = user_id
            row["claimed_at"] = datetime.now(timezone.utc)
            return uc_id

    def get_active_user_curation(
        self, user_id: str, conference_id: str | None = None
    ) -> dict[str, Any] | None:
        with self._lock:
            candidates = [
                r
                for r in self._user_rows.values()
                if r["user_id"] == user_id
                and r.get("is_active")
                and (conference_id is None or r["conference_id"] == conference_id)
            ]
            if not candidates:
                return None
            candidates.sort(key=lambda r: r["created_at"], reverse=True)
            return dict(candidates[0])


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

    def mark_claimed(self, anon_id: str, user_id: str) -> None:
        self._client.table("anonymous_curations").update(
            {"claimed_by": user_id, "claimed_at": "now()"}
        ).eq("anon_id", anon_id).execute()

    def claim_anonymous(self, anon_id: str, user_id: str) -> str:
        import uuid as _uuid

        row = self.get_anonymous(anon_id)
        if row is None:
            raise KeyError(anon_id)
        if row.get("claimed_by") is not None:
            raise ValueError("already claimed")

        # Deactivate prior active curations for the same (user, conference)
        self._client.table("user_curations").update({"is_active": False}).eq(
            "user_id", user_id
        ).eq("conference_id", row["conference_id"]).execute()

        uc_id = str(_uuid.uuid4())
        self._client.table("user_curations").insert(
            {
                "id": uc_id,
                "user_id": user_id,
                "conference_id": row["conference_id"],
                "onboarding": row["onboarding"],
                "schedule": row["schedule"],
                "is_active": True,
                "source_anon_id": anon_id,
                "tokens_used": row.get("tokens_used"),
                "model": row.get("model"),
            }
        ).execute()
        self.mark_claimed(anon_id, user_id)
        return uc_id

    def get_active_user_curation(
        self, user_id: str, conference_id: str | None = None
    ) -> dict[str, Any] | None:
        q = (
            self._client.table("user_curations")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
        )
        if conference_id is not None:
            q = q.eq("conference_id", conference_id)
        rows = (q.order("created_at", desc=True).limit(1).execute().data) or []
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
