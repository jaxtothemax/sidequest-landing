from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_admin, require_user
from app.main import app
from app.services.admin_repo import (
    InMemoryEventsAdminRepo,
    get_events_admin_repo,
)

ADMIN_ID = "00000000-aaaa-aaaa-aaaa-000000000001"
NON_ADMIN_ID = "00000000-bbbb-bbbb-bbbb-000000000002"


def _admin() -> CurrentUser:
    return CurrentUser(
        id=ADMIN_ID, email="admin@e.com", role="admin", raw_claims={"sub": ADMIN_ID}
    )


def _non_admin() -> CurrentUser:
    return CurrentUser(
        id=NON_ADMIN_ID, email="u@e.com", role=None, raw_claims={"sub": NON_ADMIN_ID}
    )


def _setup_admin() -> InMemoryEventsAdminRepo:
    repo = InMemoryEventsAdminRepo()
    app.dependency_overrides[get_events_admin_repo] = lambda: repo
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[require_user] = _admin
    return repo


def _setup_non_admin() -> InMemoryEventsAdminRepo:
    repo = InMemoryEventsAdminRepo()
    app.dependency_overrides[get_events_admin_repo] = lambda: repo
    # Note: we deliberately do NOT override require_admin — the real dep
    # should reject this user with 403 because role is not 'admin'.
    app.dependency_overrides[require_user] = _non_admin
    return repo


def _teardown() -> None:
    for dep in (get_events_admin_repo, require_admin, require_user):
        app.dependency_overrides.pop(dep, None)


def _new_event_body() -> dict:
    return {
        "id": "manual-test-1",
        "conference_id": "token2049",
        "title": "Manual Side Party",
        "starts_at": "2026-04-29T20:00:00+04:00",
        "ends_at": "2026-04-29T23:00:00+04:00",
        "venue": "Some Rooftop",
        "tags": ["Side Events", "Mixer"],
    }


# ---------- auth ----------


def test_admin_endpoints_reject_non_admin_users() -> None:
    _setup_non_admin()
    try:
        client = TestClient(app)
        for path, method, body in [
            ("/api/admin/events", "GET", None),
            ("/api/admin/events", "POST", _new_event_body()),
            ("/api/admin/events/x", "PATCH", {"title": "x"}),
            ("/api/admin/events/x", "DELETE", None),
            ("/api/admin/events/x/lock", "POST", {"locked": True}),
        ]:
            r = client.request(method, path, json=body, headers={"Authorization": "Bearer dummy"})
            assert r.status_code == 403, (path, r.status_code, r.text)
    finally:
        _teardown()


# ---------- CRUD + lock semantics ----------


def test_admin_create_event_is_manual_and_locked() -> None:
    repo = _setup_admin()
    try:
        client = TestClient(app)
        r = client.post(
            "/api/admin/events",
            json=_new_event_body(),
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["is_manual"] is True
        assert body["locked"] is True
        assert body["updated_by"] == ADMIN_ID

        # repo state matches
        row = repo.get_event("manual-test-1")
        assert row is not None and row["is_manual"] and row["locked"]
    finally:
        _teardown()


def test_admin_patch_flips_lock_to_true_on_unlocked_row() -> None:
    repo = _setup_admin()
    try:
        # Seed a scraper-style row (locked=false, is_manual=false)
        repo.scraper_upsert(
            {
                "id": "scraped-1",
                "conference_id": "token2049",
                "title": "Scraped event",
                "starts_at": "2026-04-29T10:00:00+04:00",
                "ends_at": "2026-04-29T11:00:00+04:00",
            }
        )
        assert repo.get_event("scraped-1")["locked"] is False

        client = TestClient(app)
        r = client.patch(
            "/api/admin/events/scraped-1",
            json={"venue": "Hand-corrected venue"},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["venue"] == "Hand-corrected venue"
        assert body["locked"] is True  # auto-locked
        assert body["is_manual"] is False  # still scraper-origin

        # scraper now no-ops on this row
        applied = repo.scraper_upsert(
            {
                "id": "scraped-1",
                "conference_id": "token2049",
                "title": "Scraped event (replaced title)",
                "venue": "WRONG-overwriting-venue",
                "starts_at": "2026-04-29T10:00:00+04:00",
                "ends_at": "2026-04-29T11:00:00+04:00",
            }
        )
        assert applied is False
        # confirm venue was NOT clobbered
        assert repo.get_event("scraped-1")["venue"] == "Hand-corrected venue"
    finally:
        _teardown()


def test_admin_explicit_lock_toggle() -> None:
    repo = _setup_admin()
    try:
        repo.scraper_upsert(
            {
                "id": "scraped-2",
                "conference_id": "token2049",
                "title": "x",
                "starts_at": "2026-04-29T10:00:00+04:00",
                "ends_at": "2026-04-29T11:00:00+04:00",
            }
        )
        client = TestClient(app)

        r = client.post(
            "/api/admin/events/scraped-2/lock",
            json={"locked": True},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200
        assert r.json()["locked"] is True
        assert repo.scraper_upsert(
            {"id": "scraped-2", "conference_id": "token2049", "title": "y", "starts_at": "2026-04-29T10:00:00+04:00", "ends_at": "2026-04-29T11:00:00+04:00"}
        ) is False

        r = client.post(
            "/api/admin/events/scraped-2/lock",
            json={"locked": False},
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200
        assert r.json()["locked"] is False
        # scraper is allowed again
        assert repo.scraper_upsert(
            {"id": "scraped-2", "conference_id": "token2049", "title": "z", "starts_at": "2026-04-29T10:00:00+04:00", "ends_at": "2026-04-29T11:00:00+04:00"}
        ) is True
        assert repo.get_event("scraped-2")["title"] == "z"
    finally:
        _teardown()


def test_admin_delete_event() -> None:
    repo = _setup_admin()
    try:
        repo.create_event(fields=_new_event_body(), updated_by=ADMIN_ID)
        client = TestClient(app)

        r = client.delete(
            "/api/admin/events/manual-test-1",
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 204
        assert repo.get_event("manual-test-1") is None

        r = client.delete(
            "/api/admin/events/manual-test-1",
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 404
    finally:
        _teardown()


def test_admin_list_filters() -> None:
    repo = _setup_admin()
    try:
        repo.create_event(fields=_new_event_body(), updated_by=ADMIN_ID)
        repo.scraper_upsert(
            {
                "id": "scraped-3",
                "conference_id": "token2049",
                "title": "scraped",
                "starts_at": "2026-04-29T10:00:00+04:00",
                "ends_at": "2026-04-29T11:00:00+04:00",
            }
        )
        client = TestClient(app)

        r = client.get(
            "/api/admin/events?is_manual=true",
            headers={"Authorization": "Bearer dummy"},
        )
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()]
        assert "manual-test-1" in ids and "scraped-3" not in ids

        r = client.get(
            "/api/admin/events?locked=false",
            headers={"Authorization": "Bearer dummy"},
        )
        ids = [e["id"] for e in r.json()]
        assert "scraped-3" in ids and "manual-test-1" not in ids
    finally:
        _teardown()


def test_scraper_upsert_new_row_inserts_unlocked() -> None:
    repo = InMemoryEventsAdminRepo()
    assert repo.scraper_upsert(
        {
            "id": "new-1",
            "conference_id": "token2049",
            "title": "fresh",
            "starts_at": "2026-04-29T10:00:00+04:00",
            "ends_at": "2026-04-29T11:00:00+04:00",
        }
    ) is True
    row = repo.get_event("new-1")
    assert row is not None
    assert row["locked"] is False
    assert row["is_manual"] is False
