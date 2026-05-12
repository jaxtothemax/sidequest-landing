from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_user
from app.models.schemas import ScheduleResponse
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.curations_store import CurationsStore, get_curations_store
from app.services.pins_store import PinsStore, get_pins_store
from app.services.schedule_merge import merge_schedule

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/schedule", response_model=ScheduleResponse)
def get_my_schedule(
    user: Annotated[CurrentUser, Depends(require_user)],
    store: Annotated[CurationsStore, Depends(get_curations_store)],
    pins: Annotated[PinsStore, Depends(get_pins_store)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    conference_id: str | None = None,
) -> ScheduleResponse:
    curation = store.get_active_user_curation(user.id, conference_id)
    if curation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no active curation for this user",
        )
    conf_id = curation["conference_id"]
    events = repo.list_events(conf_id) if conf_id else []
    user_pins = pins.list_for_user(user.id)
    schedule = merge_schedule(
        curated=curation["schedule"] or [],
        pins=user_pins,
        events=events,
    )
    return ScheduleResponse(conference_id=conf_id, schedule=schedule)
