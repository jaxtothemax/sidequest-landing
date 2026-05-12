from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.curations_store import (
    InMemoryCurationsStore,
    get_curations_store,
)
from app.services.llm import LLMClient, LLMResult, get_llm_client


class _MockLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, str | None]] = []

    async def complete_json(
        self, system: str, user: str, *, model: str | None = None
    ) -> LLMResult:
        self.calls.append((system, user, model))
        return LLMResult(
            content=json.dumps(self.payload),
            tokens_used=1234,
            model=model or "anthropic/claude-sonnet-4-5",
        )


SAMPLE_ONBOARDING = {
    "conferenceId": "token2049",
    "attendance": "partial",
    "days": [29, 30],
    "role": "founder",
    "goals": ["fundraising", "networking", "partnerships"],
    "topics": ["DeFi", "AI / ML"],
    "pace": 50,
    "energy": 60,
    "social": 70,
    "mustHaves": ["a16zcrypto", "hayden"],
}

ANON_ID = "11111111-2222-3333-4444-555555555555"


def _override(llm_payload: dict) -> tuple[_MockLLM, InMemoryCurationsStore]:
    mock_llm = _MockLLM(llm_payload)
    fresh_store = InMemoryCurationsStore()
    app.dependency_overrides[get_llm_client] = lambda: mock_llm  # type: ignore[assignment]
    app.dependency_overrides[get_curations_store] = lambda: fresh_store  # type: ignore[assignment]
    return mock_llm, fresh_store


def _clear() -> None:
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(get_curations_store, None)


def test_curate_persists_anon_row_and_returns_schedule() -> None:
    mock_llm, store = _override(
        {
            "schedule": [
                {
                    "event_id": "t2049-e1",
                    "day": "2026-04-29",
                    "start": "2026-04-29T09:00:00+04:00",
                    "end": "2026-04-29T11:00:00+04:00",
                    "rationale": "Stablecoin founders match your fundraising goal.",
                    "priority": "must",
                },
                {
                    "event_id": "t2049-e3",
                    "day": "2026-04-29",
                    "start": "2026-04-29T14:00:00+04:00",
                    "end": "2026-04-29T15:00:00+04:00",
                    "rationale": "DeFi panel matches your top topic.",
                    "priority": "should",
                },
            ]
        }
    )
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/curate",
            json={"onboarding": SAMPLE_ONBOARDING, "anon_id": ANON_ID},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["curate_id"] == ANON_ID
        assert body["tokens_used"] == 1234
        assert len(body["schedule"]) == 2
        assert body["schedule"][0]["event_id"] == "t2049-e1"
        assert body["schedule"][0]["priority"] == "must"

        # Row persisted with full onboarding + schedule
        row = store.get_anonymous(ANON_ID)
        assert row is not None
        assert row["conference_id"] == "token2049"
        assert row["onboarding"]["role"] == "founder"
        assert len(row["schedule"]) == 2

        # LLM saw exactly 2 candidates (filtered to days 29 + 30 = all 12 events)
        # — sanity-check that the prompt JSON parses and contains candidate_events
        _, user_msg, _ = mock_llm.calls[0]
        prompt = json.loads(user_msg)
        assert prompt["onboarding"]["conferenceId"] == "token2049"
        candidate_ids = {c["id"] for c in prompt["candidate_events"]}
        assert "t2049-e1" in candidate_ids and "t2049-e3" in candidate_ids
    finally:
        _clear()


def test_curate_filters_to_attended_days() -> None:
    mock_llm, _ = _override({"schedule": []})
    try:
        client = TestClient(app)
        body = {
            "onboarding": {**SAMPLE_ONBOARDING, "days": [29]},  # only day 29
            "anon_id": "22222222-2222-2222-2222-222222222222",
        }
        resp = client.post("/api/curate", json=body)
        assert resp.status_code == 200

        prompt = json.loads(mock_llm.calls[0][1])
        days = {c["start"][:10] for c in prompt["candidate_events"]}
        assert days == {"2026-04-29"}, days
    finally:
        _clear()


def test_curate_rejects_hallucinated_event_ids() -> None:
    _override(
        {
            "schedule": [
                {
                    "event_id": "FAKE-ID-NOT-IN-CANDIDATES",
                    "day": "2026-04-29",
                    "start": "x",
                    "end": "y",
                    "rationale": "should be dropped",
                    "priority": "must",
                },
                {
                    "event_id": "t2049-e5",
                    "day": "2026-04-29",
                    "start": "2026-04-29T19:30:00+04:00",
                    "end": "2026-04-29T23:00:00+04:00",
                    "rationale": "real one",
                    "priority": "must",
                },
            ]
        }
    )
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/curate",
            json={
                "onboarding": SAMPLE_ONBOARDING,
                "anon_id": "33333333-3333-3333-3333-333333333333",
            },
        )
        assert resp.status_code == 200
        ids = [s["event_id"] for s in resp.json()["schedule"]]
        assert ids == ["t2049-e5"]
    finally:
        _clear()


def test_curate_rejects_unknown_conference() -> None:
    _override({"schedule": []})
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/curate",
            json={
                "onboarding": {**SAMPLE_ONBOARDING, "conferenceId": "does-not-exist"},
                "anon_id": "44444444-4444-4444-4444-444444444444",
            },
        )
        assert resp.status_code == 404
    finally:
        _clear()


def test_curate_rejects_bad_anon_id() -> None:
    _override({"schedule": []})
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/curate",
            json={"onboarding": SAMPLE_ONBOARDING, "anon_id": "not-a-uuid"},
        )
        assert resp.status_code == 400
    finally:
        _clear()
