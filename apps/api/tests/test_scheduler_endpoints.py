"""GET/PUT /api/admin/scheduler — admin toggle endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_admin, require_user
from app.main import app
from app.services.scheduler_settings_repo import (
    InMemorySchedulerSettingsRepo,
    get_scheduler_settings_repo,
)

ADMIN_ID = "00000000-aaaa-aaaa-aaaa-000000000001"


def _admin() -> CurrentUser:
    return CurrentUser(
        id=ADMIN_ID, email="admin@e.com", role="admin", raw_claims={"sub": ADMIN_ID}
    )


def _setup() -> InMemorySchedulerSettingsRepo:
    repo = InMemorySchedulerSettingsRepo()
    app.dependency_overrides[get_scheduler_settings_repo] = lambda: repo
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[require_user] = _admin
    return repo


def _teardown() -> None:
    for dep in (get_scheduler_settings_repo, require_admin, require_user):
        app.dependency_overrides.pop(dep, None)


def test_get_scheduler_returns_default_off() -> None:
    _setup()
    try:
        client = TestClient(app)
        resp = client.get("/api/admin/scheduler")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["enabled"] is False
        assert isinstance(body["tick_seconds"], int)
        assert body["tick_seconds"] > 0
    finally:
        _teardown()


def test_put_scheduler_enables_and_persists() -> None:
    repo = _setup()
    try:
        client = TestClient(app)
        resp = client.put("/api/admin/scheduler", json={"enabled": True})
        assert resp.status_code == 200, resp.text
        assert resp.json()["enabled"] is True
        assert repo.get_enabled() is True

        # Round-trip via GET
        resp2 = client.get("/api/admin/scheduler")
        assert resp2.json()["enabled"] is True
    finally:
        _teardown()


def test_put_scheduler_disables() -> None:
    repo = _setup()
    repo.set_enabled(True)
    try:
        client = TestClient(app)
        resp = client.put("/api/admin/scheduler", json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        assert repo.get_enabled() is False
    finally:
        _teardown()
