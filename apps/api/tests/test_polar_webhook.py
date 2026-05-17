"""POST /api/webhooks/polar — integration tests against signed fixture payloads."""

from __future__ import annotations

import base64
import json
import os
import secrets
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from standardwebhooks import Webhook

from app.config import get_settings
from app.main import app
from app.services.entitlements_store import (
    InMemoryEntitlementsStore,
    get_entitlements_store,
)

ANON_ID = "11111111-2222-3333-4444-555555555555"


# Standard-webhooks secrets are conventionally `whsec_<base64>`. We mint a
# fresh random one per test session and inject it via env so get_settings
# (lru_cache) picks it up.
_WHSEC = "whsec_" + base64.b64encode(secrets.token_bytes(24)).decode()


@pytest.fixture(autouse=True)
def _configure_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", _WHSEC)
    # Settings is lru_cached — clear so the new env var is picked up.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def ent_store() -> InMemoryEntitlementsStore:
    store = InMemoryEntitlementsStore()
    app.dependency_overrides[get_entitlements_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_entitlements_store, None)


def _sign(body: bytes) -> dict[str, str]:
    """Return Standard-Webhooks headers for the given raw body.

    Polar's `validate_event` wraps the secret as base64(secret_bytes) before
    handing it to Standard-Webhooks. We mirror that here so the signature the
    test produces matches what the SDK will compute on verify.
    """
    base64_secret = base64.b64encode(_WHSEC.encode()).decode()
    wh = Webhook(base64_secret)
    msg_id = f"msg_{uuid.uuid4().hex}"
    ts = datetime.now(timezone.utc)
    signature = wh.sign(msg_id, ts, body.decode())
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": str(int(ts.timestamp())),
        "webhook-signature": signature,
        "content-type": "application/json",
    }


def _order_paid_payload(
    *, anon_id: str = ANON_ID, conference_id: str = "token2049", order_id: str = "ord_test_1"
) -> bytes:
    """An order.paid payload with all the fields Polar's strict schema requires.

    The handler only reads `data.id`, `data.metadata`, and the event type — but
    `validate_event` runs full pydantic validation, so every required field
    needs a plausible value or the test errors out before the handler runs.
    """
    now = datetime.now(timezone.utc).isoformat()
    customer = {
        "id": "cust_test",
        "created_at": now,
        "modified_at": now,
        "metadata": {},
        "email_verified": True,
        "type": "individual",
        "name": "Test Customer",
        "billing_address": None,
        "tax_id": None,
        "organization_id": "org_test",
        "deleted_at": None,
        "avatar_url": "https://example.com/a.png",
        "email": "test@example.com",
    }
    return json.dumps(
        {
            "type": "order.paid",
            "timestamp": now,
            "data": {
                "id": order_id,
                "status": "paid",
                "paid": True,
                "metadata": {
                    "anon_id": anon_id,
                    "conference_id": conference_id,
                },
                "created_at": now,
                "modified_at": now,
                "currency": "usd",
                "net_amount": 999,
                "subtotal_amount": 999,
                "tax_amount": 0,
                "discount_amount": 0,
                "refunded_amount": 0,
                "refunded_tax_amount": 0,
                "total_amount": 999,
                "applied_balance_amount": 0,
                "due_amount": 0,
                "platform_fee_amount": 0,
                "platform_fee_currency": "usd",
                "customer_id": "cust_test",
                "product_id": "prod_test",
                "checkout_id": "co_test",
                "discount_id": None,
                "subscription_id": None,
                "discount": None,
                "subscription": None,
                "items": [],
                "billing_reason": "purchase",
                "billing_address": None,
                "billing_name": None,
                "is_invoice_generated": False,
                "invoice_number": "INV-TEST-1",
                "customer": customer,
                "product": None,
                "description": "test order",
            },
        }
    ).encode()


def test_signed_order_paid_unlocks_anonymous_entitlement(
    ent_store: InMemoryEntitlementsStore,
) -> None:
    body = _order_paid_payload(order_id="ord_test_happy")
    r = TestClient(app).post("/api/webhooks/polar", content=body, headers=_sign(body))

    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok"}

    row = ent_store.get_for_anon(ANON_ID, "token2049")
    assert row is not None
    assert row["unlocked"] is True
    assert row["provider"] == "polar"
    assert row["provider_ref"] == "ord_test_happy"


def test_bad_signature_returns_401(ent_store: InMemoryEntitlementsStore) -> None:
    body = _order_paid_payload()
    headers = _sign(body)
    # Flip a byte in the signature
    headers["webhook-signature"] = headers["webhook-signature"][:-3] + "AAA"
    r = TestClient(app).post("/api/webhooks/polar", content=body, headers=headers)
    assert r.status_code == 401
    assert ent_store.get_for_anon(ANON_ID, "token2049") is None


def test_unknown_event_is_no_op(ent_store: InMemoryEntitlementsStore) -> None:
    """Polar fires lots of event types; signature-valid but schema-malformed
    events are 200-acknowledged so Polar doesn't keep retrying."""
    body = json.dumps(
        {
            "type": "subscription.created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {},
        }
    ).encode()
    r = TestClient(app).post("/api/webhooks/polar", content=body, headers=_sign(body))
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    assert ent_store.get_for_anon(ANON_ID, "token2049") is None


def test_missing_metadata_is_logged_not_unlocked(
    ent_store: InMemoryEntitlementsStore,
) -> None:
    body = _order_paid_payload(anon_id="", conference_id="")
    # Build the body with empty metadata values
    parsed = json.loads(body)
    parsed["data"]["metadata"] = {}
    body = json.dumps(parsed).encode()

    r = TestClient(app).post("/api/webhooks/polar", content=body, headers=_sign(body))
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    # Nothing should be unlocked.
    assert ent_store.get_for_anon(ANON_ID, "token2049") is None


def test_unconfigured_secret_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POLAR_WEBHOOK_SECRET", raising=False)
    get_settings.cache_clear()
    body = _order_paid_payload()
    r = TestClient(app).post(
        "/api/webhooks/polar",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 503
