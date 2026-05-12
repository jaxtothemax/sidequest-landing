from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_user
from app.main import app
from app.models.schemas import EventOut
from app.services.curations_store import (
    InMemoryCurationsStore,
    get_curations_store,
)
from app.services.pins_store import InMemoryPinsStore, get_pins_store
from app.services.schedule_merge import merge_schedule, pinned_events

USER_ID = "00000000-aaaa-bbbb-cccc-000000000001"
DUBAI = timezone(timedelta(hours=4))


def _ev(eid: str, hour: int) -> EventOut:
    return EventOut(
        id=eid,
        conference_id="token2049",
        title=f"Event {eid}",
        start=datetime(2026, 4, 29, hour, 0, tzinfo=DUBAI),
        end=datetime(2026, 4, 29, hour + 1, 0, tzinfo=DUBAI),
        tags=["x"],
    )


# ---------- pure merge tests ----------


def test_merge_with_no_pins_returns_curated_sorted_by_start() -> None:
    events = [_ev("a", 14), _ev("b", 9), _ev("c", 16)]
    curated = [
        {"event_id": "a", "rationale": "r-a", "priority": "must"},
        {"event_id": "b", "rationale": "r-b", "priority": "should"},
        {"event_id": "c", "rationale": "r-c", "priority": "maybe"},
    ]
    out = merge_schedule(curated=curated, pins=[], events=events)
    assert [s.id for s in out] == ["b", "a", "c"]
    assert out[0].rationale == "r-b"
    assert out[0].priority == "should"


def test_merge_pinned_true_adds_event_not_in_curation() -> None:
    events = [_ev("a", 14), _ev("b", 9)]
    curated = [{"event_id": "a", "rationale": "r-a", "priority": "must"}]
    pins = [{"event_id": "b", "pinned": True}]
    out = merge_schedule(curated=curated, pins=pins, events=events)
    ids = [s.id for s in out]
    assert ids == ["b", "a"]
    b = next(s for s in out if s.id == "b")
    assert b.priority == "must"
    assert "Added by you" in b.rationale


def test_merge_pinned_false_hides_curated_event() -> None:
    events = [_ev("a", 14), _ev("b", 9)]
    curated = [
        {"event_id": "a", "rationale": "r-a", "priority": "must"},
        {"event_id": "b", "rationale": "r-b", "priority": "should"},
    ]
    pins = [{"event_id": "a", "pinned": False}]
    out = merge_schedule(curated=curated, pins=pins, events=events)
    assert [s.id for s in out] == ["b"]


def test_merge_skips_curated_events_not_in_catalog() -> None:
    events = [_ev("a", 14)]
    curated = [
        {"event_id": "a", "rationale": "r-a", "priority": "must"},
        {"event_id": "missing", "rationale": "r-m", "priority": "must"},
    ]
    out = merge_schedule(curated=curated, pins=[], events=events)
    assert [s.id for s in out] == ["a"]


def test_pinned_events_returns_only_pinned_true_sorted() -> None:
    events = [_ev("a", 14), _ev("b", 9), _ev("c", 11)]
    pins = [
        {"event_id": "a", "pinned": True},
        {"event_id": "b", "pinned": False},
        {"event_id": "c", "pinned": True},
        {"event_id": "missing", "pinned": True},
    ]
    out = pinned_events(pins, events)
    assert [e.id for e in out] == ["c", "a"]


# ---------- endpoint integration ----------


def _setup_stores() -> tuple[InMemoryCurationsStore, InMemoryPinsStore]:
    cur = InMemoryCurationsStore()
    pins = InMemoryPinsStore()

    # Seed a user_curation directly so we don't have to run curate through the LLM
    cur._user_rows["uc-1"] = {  # type: ignore[attr-defined]
        "id": "uc-1",
        "user_id": USER_ID,
        "conference_id": "token2049",
        "onboarding": {},
        "schedule": [
            {
                "event_id": "t2049-e1",
                "day": "2026-04-29",
                "start": "...",
                "end": "...",
                "rationale": "curated rationale",
                "priority": "must",
            },
            {
                "event_id": "t2049-e3",
                "day": "2026-04-29",
                "start": "...",
                "end": "...",
                "rationale": "another",
                "priority": "should",
            },
        ],
        "is_active": True,
        "source_anon_id": None,
        "tokens_used": 0,
        "model": "mock",
        "created_at": datetime.now(timezone.utc),
    }

    app.dependency_overrides[get_curations_store] = lambda: cur
    app.dependency_overrides[get_pins_store] = lambda: pins
    app.dependency_overrides[require_user] = lambda: CurrentUser(
        id=USER_ID, email="t@e.com", role=None, raw_claims={"sub": USER_ID}
    )
    return cur, pins


def _teardown() -> None:
    app.dependency_overrides.pop(get_curations_store, None)
    app.dependency_overrides.pop(get_pins_store, None)
    app.dependency_overrides.pop(require_user, None)


def test_pin_then_schedule_reflects_addition() -> None:
    _setup_stores()
    try:
        client = TestClient(app)
        # Pin an event not in the curated set
        r = client.post(
            "/api/events/pin",
            json={"event_id": "t2049-e5", "pinned": True},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200, r.text

        r = client.get("/api/me/schedule", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()["schedule"]]
        assert "t2049-e5" in ids
        added = next(s for s in r.json()["schedule"] if s["id"] == "t2049-e5")
        assert added["priority"] == "must"
        assert "Added by you" in added["rationale"]
    finally:
        _teardown()


def test_unpin_curated_event_disappears_from_schedule() -> None:
    _setup_stores()
    try:
        client = TestClient(app)
        # Hide a curated event
        r = client.post(
            "/api/events/pin",
            json={"event_id": "t2049-e3", "pinned": False},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200

        r = client.get("/api/me/schedule", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()["schedule"]]
        assert "t2049-e3" not in ids
        assert "t2049-e1" in ids  # curated, still present
    finally:
        _teardown()


def test_me_events_lists_only_pinned() -> None:
    _setup_stores()
    try:
        client = TestClient(app)
        for eid, p in [("t2049-e5", True), ("t2049-e6", True), ("t2049-e1", False)]:
            client.post(
                "/api/events/pin",
                json={"event_id": eid, "pinned": p},
                headers={"Authorization": "Bearer dummy"},
            )

        r = client.get("/api/me/events", headers={"Authorization": "Bearer dummy"})
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert ids == {"t2049-e5", "t2049-e6"}
    finally:
        _teardown()


def test_pin_unknown_event_returns_404() -> None:
    _setup_stores()
    try:
        client = TestClient(app)
        r = client.post(
            "/api/events/pin",
            json={"event_id": "does-not-exist", "pinned": True},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 404
    finally:
        _teardown()
