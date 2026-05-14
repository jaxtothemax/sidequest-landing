"""
Storage for conference_scrape_sources.

Used by the admin UI today (CRUD + manual-trigger stub) and by the scraper
once it lands (Slice 3). Keeping the repo separate from admin_repo to make
the future scraper a pure consumer of this layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class ScrapeSourcesRepo(Protocol):
    def list_for_conference(self, conference_id: str) -> list[dict[str, Any]]: ...
    def get(self, source_id: str) -> dict[str, Any] | None: ...
    def create(
        self,
        *,
        conference_id: str,
        url: str,
        source_type: str = "luma",
        enabled: bool = True,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any]: ...
    def update(
        self,
        source_id: str,
        *,
        url: str | None = None,
        enabled: bool | None = None,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any] | None: ...
    def delete(self, source_id: str) -> bool: ...
    def record_scrape(
        self,
        source_id: str,
        *,
        status: str,
        error: str | None = None,
        events_added: int = 0,
        events_updated: int = 0,
    ) -> None: ...


# ---------- in-memory ----------


class InMemoryScrapeSourcesRepo:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def list_for_conference(self, conference_id: str) -> list[dict[str, Any]]:
        with self._lock:
            out = [
                dict(r)
                for r in self._rows.values()
                if r["conference_id"] == conference_id
            ]
        out.sort(key=lambda r: r["created_at"])
        return out

    def get(self, source_id: str) -> dict[str, Any] | None:
        with self._lock:
            r = self._rows.get(source_id)
            return dict(r) if r else None

    def create(
        self,
        *,
        conference_id: str,
        url: str,
        source_type: str = "luma",
        enabled: bool = True,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            sid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            row = {
                "id": sid,
                "conference_id": conference_id,
                "source_type": source_type,
                "url": url,
                "enabled": enabled,
                "last_scraped_at": None,
                "last_status": None,
                "last_error": None,
                "events_added": 0,
                "events_updated": 0,
                "scrape_interval_minutes": scrape_interval_minutes,
                "created_at": now,
                "updated_at": now,
            }
            self._rows[sid] = row
            return dict(row)

    def update(
        self,
        source_id: str,
        *,
        url: str | None = None,
        enabled: bool | None = None,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            r = self._rows.get(source_id)
            if r is None:
                return None
            if url is not None:
                r["url"] = url
            if enabled is not None:
                r["enabled"] = enabled
            if scrape_interval_minutes is not None:
                r["scrape_interval_minutes"] = scrape_interval_minutes
            r["updated_at"] = datetime.now(timezone.utc)
            return dict(r)

    def delete(self, source_id: str) -> bool:
        with self._lock:
            return self._rows.pop(source_id, None) is not None

    def record_scrape(
        self,
        source_id: str,
        *,
        status: str,
        error: str | None = None,
        events_added: int = 0,
        events_updated: int = 0,
    ) -> None:
        with self._lock:
            r = self._rows.get(source_id)
            if r is None:
                return
            r["last_scraped_at"] = datetime.now(timezone.utc)
            r["last_status"] = status
            r["last_error"] = error
            r["events_added"] = events_added
            r["events_updated"] = events_updated
            r["updated_at"] = datetime.now(timezone.utc)


# ---------- supabase ----------


_COLS = (
    "id,conference_id,source_type,url,enabled,last_scraped_at,last_status,"
    "last_error,events_added,events_updated,scrape_interval_minutes,created_at,updated_at"
)


class SupabaseScrapeSourcesRepo:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def list_for_conference(self, conference_id: str) -> list[dict[str, Any]]:
        return (
            self._client.table("conference_scrape_sources")
            .select(_COLS)
            .eq("conference_id", conference_id)
            .order("created_at")
            .execute()
            .data
        ) or []

    def get(self, source_id: str) -> dict[str, Any] | None:
        rows = (
            self._client.table("conference_scrape_sources")
            .select(_COLS)
            .eq("id", source_id)
            .limit(1)
            .execute()
            .data
        ) or []
        return rows[0] if rows else None

    def create(
        self,
        *,
        conference_id: str,
        url: str,
        source_type: str = "luma",
        enabled: bool = True,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "conference_id": conference_id,
            "source_type": source_type,
            "url": url,
            "enabled": enabled,
            "scrape_interval_minutes": scrape_interval_minutes,
        }
        res = (
            self._client.table("conference_scrape_sources")
            .insert(payload)
            .execute()
        )
        return (res.data or [payload])[0]

    def update(
        self,
        source_id: str,
        *,
        url: str | None = None,
        enabled: bool | None = None,
        scrape_interval_minutes: int | None = None,
    ) -> dict[str, Any] | None:
        patch: dict[str, Any] = {}
        if url is not None:
            patch["url"] = url
        if enabled is not None:
            patch["enabled"] = enabled
        if scrape_interval_minutes is not None:
            patch["scrape_interval_minutes"] = scrape_interval_minutes
        if not patch:
            return self.get(source_id)
        res = (
            self._client.table("conference_scrape_sources")
            .update(patch)
            .eq("id", source_id)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None

    def delete(self, source_id: str) -> bool:
        res = (
            self._client.table("conference_scrape_sources")
            .delete()
            .eq("id", source_id)
            .execute()
        )
        return bool(res.data)

    def record_scrape(
        self,
        source_id: str,
        *,
        status: str,
        error: str | None = None,
        events_added: int = 0,
        events_updated: int = 0,
    ) -> None:
        self._client.table("conference_scrape_sources").update(
            {
                "last_scraped_at": "now()",
                "last_status": status,
                "last_error": error,
                "events_added": events_added,
                "events_updated": events_updated,
            }
        ).eq("id", source_id).execute()


@lru_cache
def _build_repo() -> ScrapeSourcesRepo:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseScrapeSourcesRepo(settings)
    return InMemoryScrapeSourcesRepo()


def get_scrape_sources_repo() -> ScrapeSourcesRepo:
    return _build_repo()
