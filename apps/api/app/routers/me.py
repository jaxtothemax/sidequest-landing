from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

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
    user_pins = pins.list_for_user(user.id)

    # Resolve which conference's events we need to enrich pins/curation.
    # Prefer the curation; if there's none, derive from the user's pins so
    # users who pinned without (or before) curating still see their picks.
    conf_id: str | None = None
    if curation is not None:
        conf_id = curation.get("conference_id")
    elif user_pins:
        pin_event_ids = {p["event_id"] for p in user_pins if p.get("pinned")}
        if pin_event_ids:
            for c in repo.list_conferences():
                if any(e.id in pin_event_ids for e in repo.list_events(c.id)):
                    conf_id = c.id
                    break

    # No curation AND no resolvable pins → empty schedule (200, not 404).
    if conf_id is None:
        return ScheduleResponse(conference_id=None, schedule=[])

    events = repo.list_events(conf_id)
    curated = curation["schedule"] if curation else []
    schedule = merge_schedule(
        curated=curated or [],
        pins=user_pins,
        events=events,
    )
    return ScheduleResponse(conference_id=conf_id, schedule=schedule)
