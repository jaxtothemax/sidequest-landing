"""Global scheduler on/off state. Singleton row in `scheduler_settings`.

The scheduler tick consults `get_enabled()` on every iteration so flipping
the flag from the admin UI takes effect at most one tick later.
"""

from __future__ import annotations

from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class SchedulerSettingsRepo(Protocol):
    def get_enabled(self) -> bool: ...
    def set_enabled(self, enabled: bool, *, updated_by: str | None = None) -> bool: ...


class InMemorySchedulerSettingsRepo:
    def __init__(self) -> None:
        self._enabled = False
        self._lock = RLock()

    def get_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def set_enabled(self, enabled: bool, *, updated_by: str | None = None) -> bool:
        with self._lock:
            self._enabled = enabled
            return self._enabled


class SupabaseSchedulerSettingsRepo:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def get_enabled(self) -> bool:
        rows = (
            self._client.table("scheduler_settings")
            .select("enabled")
            .eq("id", "singleton")
            .limit(1)
            .execute()
            .data
        ) or []
        if not rows:
            return False
        return bool(rows[0].get("enabled"))

    def set_enabled(self, enabled: bool, *, updated_by: str | None = None) -> bool:
        payload: dict[str, Any] = {"enabled": enabled}
        if updated_by is not None:
            payload["updated_by"] = updated_by
        res = (
            self._client.table("scheduler_settings")
            .update(payload)
            .eq("id", "singleton")
            .execute()
        )
        rows = res.data or []
        return bool(rows[0].get("enabled")) if rows else enabled


@lru_cache
def _build_repo() -> SchedulerSettingsRepo:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseSchedulerSettingsRepo(settings)
    return InMemorySchedulerSettingsRepo()


def get_scheduler_settings_repo() -> SchedulerSettingsRepo:
    return _build_repo()
