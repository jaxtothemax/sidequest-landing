from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_user
from app.main import app
from app.services.curations_store import (
    InMemoryCurationsStore,
    get_curations_store,
)
from app.services.entitlements_store import (
    InMemoryEntitlementsStore,
    get_entitlements_store,
)
from app.services.llm import LLMClient, LLMResult, get_llm_client

USER_ID = "00000000-aaaa-bbbb-cccc-000000000001"
ANON_ID = "11111111-2222-3333-4444-555555555555"


class _MockLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def complete_json(
        self, system: str, user: str, *, model: str | None = None
    ) -> LLMResult:
        return LLMResult(
            content=json.dumps(self.payload),
            tokens_used=500,
            model=model or "anthropic/claude-sonnet-4-5",
        )


def _setup() -> tuple[InMemoryCurationsStore, InMemoryEntitlementsStore]:
    cur_store = InMemoryCurationsStore()
    ent_store = InMemoryEntitlementsStore()
    llm = _MockLLM(
        {
            "schedule": [
                {
                    "event_id": "t2049-e1",
                    "day": "2026-04-29",
                    "start": "2026-04-29T09:00:00+04:00",
                    "end": "2026-04-29T11:00:00+04:00",
                    "rationale": "Stablecoin founders.",
                    "priority": "must",
                },
                {
                    "event_id": "t2049-e3",
                    "day": "2026-04-29",
                    "start": "2026-04-29T14:00:00+04:00",
                    "end": "2026-04-29T15:00:00+04:00",
                    "rationale": "DeFi panel.",
                    "priority": "should",
                },
            ]
        }
    )
    app.dependency_overrides[get_curations_store] = lambda: cur_store
    app.dependency_overrides[get_entitlements_store] = lambda: ent_store
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[require_user] = lambda: CurrentUser(
        id=USER_ID, email="t@e.com", role=None, raw_claims={"sub": USER_ID}
    )
    return cur_store, ent_store


def _teardown() -> None:
    app.dependency_overrides.pop(get_curations_store, None)
    app.dependency_overrides.pop(get_entitlements_store, None)
    app.dependency_overrides.pop(get_llm_client, None)
    app.dependency_overrides.pop(require_user, None)


SAMPLE_ONBOARDING = {
    "conferenceId": "token2049",
    "attendance": "partial",
    "days": [29, 30],
    "role": "founder",
    "goals": ["fundraising"],
    "topics": ["DeFi"],
    "pace": 50,
    "energy": 60,
    "social": 70,
    "mustHaves": [],
}


def test_full_flow_anon_curate_claim_unlock_schedule() -> None:
    cur_store, ent_store = _setup()
    try:
        client = TestClient(app)

        # 1. Anonymous curate
        r = client.post(
            "/api/curate",
            json={"onboarding": SAMPLE_ONBOARDING, "anon_id": ANON_ID},
        )
        assert r.status_code == 200, r.text
        assert cur_store.get_anonymous(ANON_ID) is not None

        # 2. Claim — links anonymous_curation to USER_ID, creates user_curation
        r = client.post(
            "/api/auth/claim",
            json={"anon_id": ANON_ID},
            headers={"Authorization": "Bearer dummy"},  # dep overridden, value ignored
        )
        assert r.status_code == 200, r.text
        uc_id = r.json()["user_curation_id"]
        assert uc_id

        # claimed_by should be set on the anon row
        anon_row = cur_store.get_anonymous(ANON_ID)
        assert anon_row is not None
        assert anon_row["claimed_by"] == USER_ID

        # 3. Claim again → 409
        r = client.post(
            "/api/auth/claim",
            json={"anon_id": ANON_ID},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 409

        # 4. Unlock
        r = client.post("/api/unlock", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200
        assert r.json() == {"ok": True, "unlocked": True}
        assert ent_store.get(USER_ID)["unlocked"] is True

        # 5. /api/me/schedule — returns enriched events sorted by start
        r = client.get("/api/me/schedule", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["conference_id"] == "token2049"
        assert len(body["schedule"]) == 2
        # Sorted by start
        starts = [item["start"] for item in body["schedule"]]
        assert starts == sorted(starts)
        first = body["schedule"][0]
        # Enriched with event details from the catalog
        assert first["title"] == "Stable Summit IV"
        assert first["venue"] == "Sheraton · Mina A'Salam"
        assert first["rationale"] == "Stablecoin founders."
        assert first["priority"] == "must"
        assert first["inSchedule"] is True
    finally:
        _teardown()


def test_claim_unknown_anon_id_returns_404() -> None:
    _setup()
    try:
        client = TestClient(app)
        r = client.post(
            "/api/auth/claim",
            json={"anon_id": "deadbeef-dead-beef-dead-beefdeadbeef"},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 404
    finally:
        _teardown()


def test_me_schedule_without_active_curation_returns_empty() -> None:
    # Users who signed in but haven't curated yet (and have no pins) should
    # see an empty schedule, not a 404 — otherwise the frontend's pin
    # overlay machinery never engages and any persisted pins stay invisible.
    _setup()
    try:
        client = TestClient(app)
        r = client.get("/api/me/schedule", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200
        body = r.json()
        assert body["schedule"] == []
        assert body["conference_id"] is None
    finally:
        _teardown()


def test_protected_routes_require_auth() -> None:
    # Without overriding require_user, real JWKS verification kicks in and
    # rejects missing/invalid bearer tokens with 401.
    # We don't override require_user here.
    client = TestClient(app)

    r = client.get("/api/me/schedule")
    assert r.status_code == 401

    r = client.post("/api/unlock")
    assert r.status_code == 401

    r = client.post("/api/auth/claim", json={"anon_id": ANON_ID})
    assert r.status_code == 401
