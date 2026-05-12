from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import CurateRequest, CurateResponse
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.curate import curate_schedule
from app.services.curations_store import CurationsStore, get_curations_store
from app.services.llm import LLMClient, get_llm_client

router = APIRouter(prefix="/api", tags=["curate"])


def _normalise_anon_id(raw: str) -> str:
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="anon_id must be a UUID",
        ) from e


@router.post("/curate", response_model=CurateResponse)
async def curate(
    body: CurateRequest,
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    store: Annotated[CurationsStore, Depends(get_curations_store)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> CurateResponse:
    anon_id = _normalise_anon_id(body.anon_id)

    conference = repo.get_conference(body.onboarding.conferenceId)
    if conference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"conference '{body.onboarding.conferenceId}' not found",
        )
    events = repo.list_events(body.onboarding.conferenceId)

    schedule, llm_result = await curate_schedule(
        onboarding=body.onboarding,
        conference=conference,
        events=events,
        llm=llm,
        model=body.model,
    )

    store.save_anonymous(
        anon_id=anon_id,
        conference_id=conference.id,
        onboarding=body.onboarding.model_dump(),
        schedule=[item.model_dump() for item in schedule],
        tokens_used=llm_result.tokens_used,
        model=llm_result.model,
    )

    return CurateResponse(
        curate_id=anon_id,
        schedule=schedule,
        tokens_used=llm_result.tokens_used,
    )
