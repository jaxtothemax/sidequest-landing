"""
Persistence for chat_messages.

Best-effort: writes happen after the SSE stream completes; failures are
logged (or silently dropped) so they don't poison the user-facing turn.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from threading import RLock
from typing import Any, Protocol

from app.config import Settings, get_settings


class ChatStore(Protocol):
    def append(
        self,
        *,
        user_id: str,
        conference_id: str | None,
        role: str,
        content: str,
    ) -> None: ...


class InMemoryChatStore:
    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []
        self._lock = RLock()

    def append(
        self,
        *,
        user_id: str,
        conference_id: str | None,
        role: str,
        content: str,
    ) -> None:
        with self._lock:
            self._rows.append(
                {
                    "user_id": user_id,
                    "conference_id": conference_id,
                    "role": role,
                    "content": content,
                    "created_at": datetime.now(timezone.utc),
                }
            )

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._rows if r["user_id"] == user_id]


class SupabaseChatStore:
    def __init__(self, settings: Settings) -> None:
        from supabase import create_client

        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    def append(
        self,
        *,
        user_id: str,
        conference_id: str | None,
        role: str,
        content: str,
    ) -> None:
        try:
            self._client.table("chat_messages").insert(
                {
                    "user_id": user_id,
                    "conference_id": conference_id,
                    "role": role,
                    "content": content,
                }
            ).execute()
        except Exception:
            # Best-effort: never fail the user-facing turn on a write error.
            pass


@lru_cache
def _build_store() -> ChatStore:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseChatStore(settings)
    return InMemoryChatStore()


def get_chat_store() -> ChatStore:
    return _build_store()
