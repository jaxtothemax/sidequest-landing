"""Slice B — PATCH /api/admin/sources/{id} semantics.

Specifically verifies that the router can:
- set scrape_interval_minutes to a number
- clear scrape_interval_minutes back to NULL (explicit null in JSON)
- leave it alone when the field is omitted
- reject out-of-range values
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import CurrentUser, require_admin, require_user
from app.main import app
from app.services.scrape_sources_repo import (
    InMemoryScrapeSourcesRepo,
    get_scrape_sources_repo,
)

ADMIN_ID = "00000000-aaaa-aaaa-aaaa-000000000001"


def _admin() -> CurrentUser:
    return CurrentUser(
        id=ADMIN_ID, email="admin@e.com", role="admin", raw_claims={"sub": ADMIN_ID}
    )


def _setup() -> InMemoryScrapeSourcesRepo:
    repo = InMemoryScrapeSourcesRepo()
    app.dependency_overrides[get_scrape_sources_repo] = lambda: repo
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[require_user] = _admin
    return repo


def _teardown() -> None:
    for dep in (get_scrape_sources_repo, require_admin, require_user):
        app.dependency_overrides.pop(dep, None)


def test_patch_sets_interval() -> None:
    repo = _setup()
    try:
        row = repo.create(conference_id="c1", url="https://lu.ma/x")
        assert row["scrape_interval_minutes"] is None

        client = TestClient(app)
        resp = client.patch(
            f"/api/admin/sources/{row['id']}",
            json={"scrape_interval_minutes": 60},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["scrape_interval_minutes"] == 60
    finally:
        _teardown()


def test_patch_clears_interval_with_explicit_null() -> None:
    repo = _setup()
    try:
        row = repo.create(
            conference_id="c1", url="https://lu.ma/x", scrape_interval_minutes=60
        )
        assert row["scrape_interval_minutes"] == 60

        client = TestClient(app)
        resp = client.patch(
            f"/api/admin/sources/{row['id']}",
            json={"scrape_interval_minutes": None},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["scrape_interval_minutes"] is None
    finally:
        _teardown()


def test_patch_omits_interval_leaves_it_alone() -> None:
    repo = _setup()
    try:
        row = repo.create(
            conference_id="c1", url="https://lu.ma/x", scrape_interval_minutes=60
        )

        client = TestClient(app)
        resp = client.patch(
            f"/api/admin/sources/{row['id']}",
            json={"enabled": False},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["enabled"] is False
        assert body["scrape_interval_minutes"] == 60  # untouched
    finally:
        _teardown()


def test_patch_rejects_out_of_range_interval() -> None:
    repo = _setup()
    try:
        row = repo.create(conference_id="c1", url="https://lu.ma/x")
        client = TestClient(app)
        # Zero minutes is below the floor (1)
        resp = client.patch(
            f"/api/admin/sources/{row['id']}",
            json={"scrape_interval_minutes": 0},
        )
        assert resp.status_code == 422
    finally:
        _teardown()
