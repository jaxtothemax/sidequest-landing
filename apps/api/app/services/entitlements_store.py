"""
Storage for paywall entitlements.

Two tables, two flows:

- `anonymous_entitlements` — payment happens before signup; anon_id is the secret.
- `user_entitlements`      — populated by `claim()` when the user signs up.

Both are keyed per-conference (one-time unlock per event), matching the post-pivot
SideQuest model. Same dual-backend pattern as `curations_store`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class EntitlementsStore(Protocol):
    def unlock_anon(
        self,
        anon_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None: ...

    def unlock_user(
        self,
        user_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None: ...

    def get_for_anon(
        self, anon_id: str, conference_id: str
    ) -> dict[str, Any] | None: ...

    def get_for_user(
        self, user_id: str, conference_id: str
    ) -> dict[str, Any] | None: ...

    def claim(self, anon_id: str, user_id: str) -> list[str]:
        """Move any anonymous_entitlements rows for anon_id to user_entitlements.

        Returns the list of conference_ids that were claimed. Idempotent: rows
        already claimed (claimed_by set) are skipped.
        """
        ...


# ---------- in-memory backend ----------


class InMemoryEntitlementsStore:
    def __init__(self) -> None:
        # keyed by (anon_id, conference_id) and (user_id, conference_id)
        self._anon: dict[tuple[str, str], dict[str, Any]] = {}
        self._user: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = RLock()

    def unlock_anon(
        self,
        anon_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None:
        with self._lock:
            self._anon[(anon_id, conference_id)] = {
                "anon_id": anon_id,
                "conference_id": conference_id,
                "unlocked": True,
                "unlocked_at": datetime.now(timezone.utc),
                "provider": provider,
                "provider_ref": provider_ref,
                "expires_at": None,
                "claimed_by": None,
                "claimed_at": None,
            }

    def unlock_user(
        self,
        user_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None:
        with self._lock:
            self._user[(user_id, conference_id)] = {
                "user_id": user_id,
                "conference_id": conference_id,
                "unlocked": True,
                "unlocked_at": datetime.now(timezone.utc),
                "provider": provider,
                "provider_ref": provider_ref,
                "expires_at": None,
                "source_anon_id": None,
            }

    def get_for_anon(
        self, anon_id: str, conference_id: str
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self._anon.get((anon_id, conference_id))
            return dict(row) if row else None

    def get_for_user(
        self, user_id: str, conference_id: str
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self._user.get((user_id, conference_id))
            return dict(row) if row else None

    def claim(self, anon_id: str, user_id: str) -> list[str]:
        claimed: list[str] = []
        with self._lock:
            for (a_id, conf_id), row in list(self._anon.items()):
                if a_id != anon_id or row.get("claimed_by") is not None:
                    continue
                self._user[(user_id, conf_id)] = {
                    "user_id": user_id,
                    "conference_id": conf_id,
                    "unlocked": True,
                    "unlocked_at": row["unlocked_at"],
                    "provider": row["provider"],
                    "provider_ref": row["provider_ref"],
                    "expires_at": row["expires_at"],
                    "source_anon_id": anon_id,
                }
                row["claimed_by"] = user_id
                row["claimed_at"] = datetime.now(timezone.utc)
                claimed.append(conf_id)
        return claimed


# ---------- supabase backend ----------


class SupabaseEntitlementsStore:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def unlock_anon(
        self,
        anon_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None:
        self._client.table("anonymous_entitlements").upsert(
            {
                "anon_id": anon_id,
                "conference_id": conference_id,
                "unlocked": True,
                "unlocked_at": "now()",
                "provider": provider,
                "provider_ref": provider_ref,
            },
            on_conflict="anon_id,conference_id",
        ).execute()

    def unlock_user(
        self,
        user_id: str,
        conference_id: str,
        *,
        provider: str = "stub",
        provider_ref: str | None = None,
    ) -> None:
        self._client.table("user_entitlements").upsert(
            {
                "user_id": user_id,
                "conference_id": conference_id,
                "unlocked": True,
                "unlocked_at": "now()",
                "provider": provider,
                "provider_ref": provider_ref,
            },
            on_conflict="user_id,conference_id",
        ).execute()

    def get_for_anon(
        self, anon_id: str, conference_id: str
    ) -> dict[str, Any] | None:
        rows = (
            self._client.table("anonymous_entitlements")
            .select("*")
            .eq("anon_id", anon_id)
            .eq("conference_id", conference_id)
            .limit(1)
            .execute()
            .data
        ) or []
        return rows[0] if rows else None

    def get_for_user(
        self, user_id: str, conference_id: str
    ) -> dict[str, Any] | None:
        rows = (
            self._client.table("user_entitlements")
            .select("*")
            .eq("user_id", user_id)
            .eq("conference_id", conference_id)
            .limit(1)
            .execute()
            .data
        ) or []
        return rows[0] if rows else None

    def claim(self, anon_id: str, user_id: str) -> list[str]:
        unclaimed = (
            self._client.table("anonymous_entitlements")
            .select("*")
            .eq("anon_id", anon_id)
            .is_("claimed_by", "null")
            .execute()
            .data
        ) or []
        claimed: list[str] = []
        for row in unclaimed:
            conf_id = row["conference_id"]
            self._client.table("user_entitlements").upsert(
                {
                    "user_id": user_id,
                    "conference_id": conf_id,
                    "unlocked": True,
                    "unlocked_at": row.get("unlocked_at") or "now()",
                    "provider": row.get("provider"),
                    "provider_ref": row.get("provider_ref"),
                    "expires_at": row.get("expires_at"),
                    "source_anon_id": anon_id,
                },
                on_conflict="user_id,conference_id",
            ).execute()
            self._client.table("anonymous_entitlements").update(
                {"claimed_by": user_id, "claimed_at": "now()"}
            ).eq("anon_id", anon_id).eq("conference_id", conf_id).execute()
            claimed.append(conf_id)
        return claimed


@lru_cache
def _build_store() -> EntitlementsStore:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseEntitlementsStore(settings)
    return InMemoryEntitlementsStore()


def get_entitlements_store() -> EntitlementsStore:
    return _build_store()
