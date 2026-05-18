"""POST /api/checkout — unit test against a fake Polar client."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.polar_client import PolarClient, _build_client, get_polar_client

ANON_ID = "11111111-2222-3333-4444-555555555555"


class _FakePolar:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def product_id_for_conference(self, conference_id: str) -> str:
        if conference_id != "token2049":
            from app.services.polar_client import PolarConfigError

            raise PolarConfigError(f"no product for {conference_id}")
        return "prod_test_token2049"

    def create_checkout(
        self, *, product_id: str, success_url: str, metadata: dict[str, str]
    ) -> str:
        self.calls.append(
            {"product_id": product_id, "success_url": success_url, "metadata": metadata}
        )
        return "https://sandbox.polar.sh/checkout/abc123"


def _override_with(fake: _FakePolar) -> None:
    app.dependency_overrides[get_polar_client] = lambda: fake  # type: ignore[assignment]


def _teardown() -> None:
    app.dependency_overrides.pop(get_polar_client, None)


def test_checkout_returns_polar_url_with_metadata() -> None:
    fake = _FakePolar()
    _override_with(fake)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/checkout",
            json={"anon_id": ANON_ID, "conference_id": "token2049"},
        )
        assert r.status_code == 200, r.text
        assert r.json() == {"checkout_url": "https://sandbox.polar.sh/checkout/abc123"}

        assert len(fake.calls) == 1
        call = fake.calls[0]
        assert call["product_id"] == "prod_test_token2049"
        assert call["metadata"] == {
            "anon_id": ANON_ID,
            "conference_id": "token2049",
        }
        # success_url must include the Polar {CHECKOUT_ID} template token
        assert "{CHECKOUT_ID}" in call["success_url"]
        assert "/paywall/thanks" in call["success_url"]
    finally:
        _teardown()


def test_checkout_unknown_conference_returns_400() -> None:
    fake = _FakePolar()
    _override_with(fake)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/checkout",
            json={"anon_id": ANON_ID, "conference_id": "doesnotexist"},
        )
        assert r.status_code == 400
        assert fake.calls == []
    finally:
        _teardown()


def test_checkout_invalid_anon_id_returns_400() -> None:
    fake = _FakePolar()
    _override_with(fake)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/checkout",
            json={"anon_id": "not-a-uuid", "conference_id": "token2049"},
        )
        assert r.status_code == 400
    finally:
        _teardown()


def test_checkout_endpoint_does_not_require_auth() -> None:
    """The whole point of pre-signup checkout is that it's anonymous."""
    fake = _FakePolar()
    _override_with(fake)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/checkout",
            json={"anon_id": ANON_ID, "conference_id": "token2049"},
        )
        # No Authorization header — should still succeed.
        assert r.status_code == 200
    finally:
        _teardown()


def test_polar_client_falls_back_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without POLAR_ACCESS_TOKEN, the dependency surfaces a config error.

    We explicitly unset the env var because the dev `.env` (read by
    pydantic-settings at import time) usually has it set.
    """
    _teardown()
    monkeypatch.setenv("POLAR_ACCESS_TOKEN", "")
    # Both Settings and PolarClient are lru_cached — clear so the empty token
    # is observed.
    get_settings.cache_clear()
    _build_client.cache_clear()

    # raise_server_exceptions=False so PolarConfigError comes through as a 5xx
    # status instead of being re-raised by TestClient.
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post(
        "/api/checkout",
        json={"anon_id": ANON_ID, "conference_id": "token2049"},
    )
    # Acceptable as long as it doesn't 200 with garbage — config error → 5xx.
    assert r.status_code >= 500

    # Don't leak the cleared caches to other tests.
    get_settings.cache_clear()
    _build_client.cache_clear()
