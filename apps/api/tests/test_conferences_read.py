from fastapi.testclient import TestClient

from app.main import app


def test_list_conferences_returns_three_seeded() -> None:
    client = TestClient(app)
    resp = client.get("/api/conferences")
    assert resp.status_code == 200
    data = resp.json()
    ids = {c["id"] for c in data}
    assert ids == {"token2049", "ethglobal", "consensus"}


def test_token2049_has_attendable_days_only_for_29_and_30() -> None:
    client = TestClient(app)
    resp = client.get("/api/conferences/token2049")
    assert resp.status_code == 200
    conf = resp.json()
    assert conf["name"] == "TOKEN2049 Dubai"
    assert conf["timezone"] == "Asia/Dubai"

    # Frontend Conference.days uses `num`; backend exposes via serialization_alias.
    enabled_days = sorted(d["num"] for d in conf["days"] if d["enabled"])
    assert enabled_days == [29, 30]


def test_token2049_events_count_and_shape() -> None:
    client = TestClient(app)
    resp = client.get("/api/conferences/token2049/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 12

    first = events[0]
    assert {"id", "conference_id", "title", "start", "end", "venue", "tags"} <= set(first.keys())
    assert first["conference_id"] == "token2049"
    assert isinstance(first["tags"], list)
    # Times serialized as ISO 8601 (datetime)
    assert "T" in first["start"]


def test_unknown_conference_returns_404() -> None:
    client = TestClient(app)
    assert client.get("/api/conferences/does-not-exist").status_code == 404
    assert client.get("/api/conferences/does-not-exist/events").status_code == 404


def test_ethglobal_and_consensus_have_no_seeded_events_yet() -> None:
    client = TestClient(app)
    assert client.get("/api/conferences/ethglobal/events").json() == []
    assert client.get("/api/conferences/consensus/events").json() == []
