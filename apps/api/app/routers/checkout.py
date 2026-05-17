"""
POST /api/checkout — creates a Polar hosted checkout session and returns
the URL the client should redirect to.

This endpoint is intentionally unauthenticated: payment happens *before* signup
in the SideQuest flow. The anon_id (already the secret for /api/curate) is
propagated through Polar's `metadata` so the eventual webhook can attribute
the payment.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.models.schemas import CheckoutCreateRequest, CheckoutCreateResponse
from app.services.polar_client import PolarClient, PolarConfigError, get_polar_client

router = APIRouter(prefix="/api", tags=["checkout"])


def _normalise_anon_id(raw: str) -> str:
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="anon_id must be a UUID",
        ) from e


@router.post("/checkout", response_model=CheckoutCreateResponse)
def create_checkout(
    body: CheckoutCreateRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    polar: Annotated[PolarClient, Depends(get_polar_client)],
) -> CheckoutCreateResponse:
    anon_id = _normalise_anon_id(body.anon_id)
    try:
        product_id = polar.product_id_for_conference(body.conference_id)
    except PolarConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # success_url comes back to the web app; the actual entitlement write
    # happens via the Polar webhook (Phase 3), so we just need the URL to
    # land on a "we're confirming your payment" view.
    success_url = (
        f"{settings.public_web_base_url.rstrip('/')}"
        f"/paywall/thanks?checkout_id={{CHECKOUT_ID}}"
    )

    try:
        url = polar.create_checkout(
            product_id=product_id,
            success_url=success_url,
            metadata={
                "anon_id": anon_id,
                "conference_id": body.conference_id,
            },
        )
    except PolarConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    return CheckoutCreateResponse(checkout_url=url)
