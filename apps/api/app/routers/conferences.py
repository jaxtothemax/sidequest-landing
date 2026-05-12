from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import ConferenceOut, EventOut
from app.services.catalog import CatalogRepo, get_catalog_repo

router = APIRouter(prefix="/api/conferences", tags=["conferences"])


@router.get("", response_model=list[ConferenceOut])
def list_conferences(
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> list[ConferenceOut]:
    return repo.list_conferences()


@router.get("/{conference_id}", response_model=ConferenceOut)
def get_conference(
    conference_id: str,
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> ConferenceOut:
    conf = repo.get_conference(conference_id)
    if conf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conference not found")
    return conf


@router.get("/{conference_id}/events", response_model=list[EventOut])
def list_conference_events(
    conference_id: str,
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> list[EventOut]:
    # Validate conference exists for a clean 404 — keep the contract honest.
    if repo.get_conference(conference_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conference not found")
    return repo.list_events(conference_id)
