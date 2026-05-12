from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_user
from app.models.schemas import ClaimRequest, ClaimResponse, UnlockResponse
from app.services.curations_store import CurationsStore, get_curations_store
from app.services.entitlements_store import EntitlementsStore, get_entitlements_store

router = APIRouter(prefix="/api", tags=["auth"])


def _normalise_anon_id(raw: str) -> str:
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="anon_id must be a UUID",
        ) from e


@router.post("/auth/claim", response_model=ClaimResponse)
def claim(
    body: ClaimRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    store: Annotated[CurationsStore, Depends(get_curations_store)],
) -> ClaimResponse:
    anon_id = _normalise_anon_id(body.anon_id)
    try:
        uc_id = store.claim_anonymous(anon_id, user.id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="anonymous curation not found",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="anonymous curation already claimed",
        ) from e
    return ClaimResponse(user_curation_id=uc_id)


@router.post("/unlock", response_model=UnlockResponse)
def unlock(
    user: Annotated[CurrentUser, Depends(require_user)],
    store: Annotated[EntitlementsStore, Depends(get_entitlements_store)],
) -> UnlockResponse:
    # Stub: no payment integration yet — see plan §"Payment provider integration".
    store.unlock(user.id, provider="stub")
    return UnlockResponse(unlocked=True)
