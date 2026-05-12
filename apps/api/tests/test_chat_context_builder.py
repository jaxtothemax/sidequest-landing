from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_user
from app.main import app
from app.models.schemas import ScheduleItem
from app.services.chat import build_system_prompt
from app.services.chat_store import InMemoryChatStore, get_chat_store
from app.services.curations_store import (
    InMemoryCurationsStore,
    get_curations_store,
)
from app.services.llm import LLMResult, get_llm_client
from app.services.pins_store import InMemoryPinsStore, get_pins_store

USER_ID = "00000000-cccc-cccc-cccc-000000000001"
DUBAI = timezone(timedelta(hours=4))


# ---------- pure system-prompt builder ----------


def _item(eid: str, title: str, hour: int, priority: str) -> ScheduleItem:
    return ScheduleItem(
        id=eid,
        conference_id="token2049",
        title=title,
        start=datetime(2026, 4, 29, hour, 0, tzinfo=DUBAI),
        end=datetime(2026, 4, 29, hour + 1, 0, tzinfo=DUBAI),
        venue="Main Stage",
        tags=["x"],
        rationale="r",
        priority=priority,
    )


def test_system_prompt_includes_onboarding_schedule_and_conference() -> None:
    onboarding = {
        "role": "founder",
        "goals": ["fundraising", "networking"],
        "topics": ["DeFi"],
        "mustHaves": ["a16zcrypto"],
        "attendance": "partial",
        "days": [29, 30],
        "pace": 50,
        "energy": 60,
        "social": 70,
    }
    schedule = [
        _item("e1", "Stable Summit IV", 9, "must"),
        _item("e3", "DeFi Liquidity Panel", 14, "should"),
    ]
    conference = {
        "id": "token2049",
        "name": "TOKEN2049 Dubai",
        "city": "Dubai",
        "start_date": "2026-04-29",
        "end_date": "2026-04-30",
    }
    prompt = build_system_prompt(
        onboarding=onboarding, schedule=schedule, conference=conference
    )
    assert "TOKEN2049 Dubai" in prompt
    assert "founder" in prompt
    assert "fundraising, networking" in prompt
    assert "DeFi" in prompt
    assert "a16zcrypto" in prompt
    assert "Stable Summit IV" in prompt
    assert "[must]" in prompt and "[should]" in prompt


def test_system_prompt_handles_empty_state() -> None:
    prompt = build_system_prompt(onboarding=None, schedule=[], conference=None)
    assert "no onboarding answers" in prompt
    assert "no events on schedule yet" in prompt


# ---------- streaming endpoint ----------


class _StreamingMockLLM:
    def __init__(self, deltas: list[str]) -> None:
        self.deltas = deltas
        self.last_messages: list[dict] | None = None

    async def complete_json(self, *a, **kw) -> LLMResult:  # not used
        raise NotImplementedError

    async def complete_stream(
        self, messages: list[dict[str, str]], *, model: str | None = None
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        for d in self.deltas:
            yield d


def _setup() -> tuple[_StreamingMockLLM, InMemoryChatStore]:
    cur = InMemoryCurationsStore()
    pins = InMemoryPinsStore()
    chat_store = InMemoryChatStore()
    llm = _StreamingMockLLM(deltas=["Hello", " ", "there!"])

    app.dependency_overrides[get_curations_store] = lambda: cur
    app.dependency_overrides[get_pins_store] = lambda: pins
    app.dependency_overrides[get_chat_store] = lambda: chat_store
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[require_user] = lambda: CurrentUser(
        id=USER_ID, email="u@e.com", role=None, raw_claims={"sub": USER_ID}
    )
    return llm, chat_store


def _teardown() -> None:
    for dep in (
        get_curations_store,
        get_pins_store,
        get_chat_store,
        get_llm_client,
        require_user,
    ):
        app.dependency_overrides.pop(dep, None)


def _parse_sse(body: str) -> list[dict | str]:
    out: list[dict | str] = []
    for line in body.splitlines():
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data:
            continue
        if data == "[DONE]":
            out.append("[DONE]")
            continue
        try:
            out.append(json.loads(data))
        except json.JSONDecodeError:
            pass
    return out


def test_chat_streams_delta_frames_then_done_then_terminator() -> None:
    llm, chat_store = _setup()
    try:
        client = TestClient(app)
        with client.stream(
            "POST",
            "/api/chat",
            json={"messages": [{"role": "user", "content": "What's good at 9am?"}]},
            headers={"Authorization": "Bearer dummy"},
        ) as resp:
            assert resp.status_code == 200
            body = "".join(resp.iter_text())

        frames = _parse_sse(body)
        # Should be: 3 deltas, one done, one [DONE] terminator
        deltas = [f for f in frames if isinstance(f, dict) and f.get("type") == "delta"]
        dones = [f for f in frames if isinstance(f, dict) and f.get("type") == "done"]
        assert [d["content"] for d in deltas] == ["Hello", " ", "there!"]
        assert len(dones) == 1
        assert "[DONE]" in frames

        # System prompt was prepended
        assert llm.last_messages is not None
        assert llm.last_messages[0]["role"] == "system"
        assert llm.last_messages[1] == {
            "role": "user",
            "content": "What's good at 9am?",
        }

        # Persistence: user + assistant rows written
        rows = chat_store.list_for_user(USER_ID)
        roles = sorted(r["role"] for r in rows)
        assert roles == ["assistant", "user"]
        assistant = next(r for r in rows if r["role"] == "assistant")
        assert assistant["content"] == "Hello there!"
    finally:
        _teardown()


def test_chat_requires_auth() -> None:
    client = TestClient(app)
    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 401
