"""
POST /api/webhooks/polar — receives signed events from Polar.

We care about exactly one event today: `order.paid`. On success we extract the
`{anon_id, conference_id}` we stamped into the checkout's metadata and write
an `anonymous_entitlements` row. Everything else is a 200 no-op so Polar
doesn't retry forever on event types we don't handle yet.

Signature verification uses `polar_sdk.webhooks.validate_event`, which wraps
the Standard Webhooks spec.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.services.entitlements_store import EntitlementsStore, get_entitlements_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/polar", status_code=status.HTTP_200_OK)
async def polar_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[EntitlementsStore, Depends(get_entitlements_store)],
) -> dict[str, str]:
    if not settings.polar_webhook_secret:
        # Refuse to run unsigned — silently 200-ing here would be a footgun
        # (we'd accept forged webhooks in any env that forgot to set the secret).
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="POLAR_WEBHOOK_SECRET is not configured",
        )

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    from pydantic import ValidationError
    from polar_sdk.webhooks import WebhookVerificationError, validate_event

    try:
        event = validate_event(body, headers, settings.polar_webhook_secret)
    except WebhookVerificationError as e:
        # Bad signature, replay, or malformed metadata — refuse.
        logger.warning("polar webhook signature verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid webhook signature",
        ) from e
    except ValidationError as e:
        # Signature was valid but the payload didn't match any known schema.
        # 200-ack so Polar doesn't retry forever; log so we notice schema drift.
        logger.warning("polar webhook payload validation failed: %s", e)
        return {"status": "ignored", "reason": "unrecognised payload"}

    event_type = getattr(event, "TYPE", None) or getattr(event, "type", None)

    if event_type == "order.paid":
        order = event.data
        meta = dict(order.metadata or {})
        anon_id = meta.get("anon_id")
        conference_id = meta.get("conference_id")

        if not anon_id or not conference_id:
            # Real payment but we can't attribute it — log loudly. Don't 4xx
            # (Polar would retry forever); the order will need manual repair.
            logger.error(
                "polar order.paid missing metadata anon_id/conference_id "
                "(order_id=%s, metadata=%s)",
                order.id,
                meta,
            )
            return {"status": "ignored", "reason": "missing metadata"}

        store.unlock_anon(
            str(anon_id),
            str(conference_id),
            provider="polar",
            provider_ref=order.id,
        )
        logger.info(
            "polar order.paid → anonymous_entitlements upserted "
            "(order_id=%s, anon_id=%s, conference_id=%s)",
            order.id,
            anon_id,
            conference_id,
        )
        return {"status": "ok"}

    # Any other event type — acknowledge but don't act. Polar should not
    # retry, and we won't accumulate dead-letter noise.
    return {"status": "ignored", "event": str(event_type or "unknown")}
