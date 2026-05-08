from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_events_public_no_auth() -> None:
    with TestClient(app) as client:
        r = client.get("/api/events")
        assert r.status_code == 200
        body = r.json()
        assert "events" in body


def test_pin_requires_auth() -> None:
    with TestClient(app) as client:
        r = client.post("/api/events/pin", json={"event_id": "x", "pinned": True})
        assert r.status_code == 401
