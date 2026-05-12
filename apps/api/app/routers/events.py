from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_user
from app.models.schemas import EventOut, PinRequest, PinResponse
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.curations_store import CurationsStore, get_curations_store
from app.services.pins_store import PinsStore, get_pins_store
from app.services.schedule_merge import pinned_events

router = APIRouter(prefix="/api", tags=["events"])


@router.post("/events/pin", response_model=PinResponse)
def pin_event(
    body: PinRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    pins: Annotated[PinsStore, Depends(get_pins_store)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> PinResponse:
    # Verify event exists in some conference. Cheap check: scan all conferences
    # we know about. With one real conference this is fine; if it scales we'll
    # add a CatalogRepo.get_event(event_id) method.
    conferences = repo.list_conferences()
    found = False
    for c in conferences:
        if any(e.id == body.event_id for e in repo.list_events(c.id)):
            found = True
            break
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"event '{body.event_id}' not found",
        )
    pins.set_pin(user.id, body.event_id, body.pinned)
    return PinResponse(event_id=body.event_id, pinned=body.pinned)


@router.get("/me/events", response_model=list[EventOut])
def list_my_pinned_events(
    user: Annotated[CurrentUser, Depends(require_user)],
    pins: Annotated[PinsStore, Depends(get_pins_store)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    curations: Annotated[CurationsStore, Depends(get_curations_store)],
) -> list[EventOut]:
    user_pins = pins.list_for_user(user.id)
    if not user_pins:
        return []
    # Look up events from the user's active conference (if any) — falls back to
    # any conference the pinned events belong to. With one real conference this
    # is trivially the active one.
    active = curations.get_active_user_curation(user.id)
    conf_id = active.get("conference_id") if active else None
    if conf_id:
        events = repo.list_events(conf_id)
    else:
        # Cross-conference fallback: union all conference event lists.
        events = []
        for c in repo.list_conferences():
            events.extend(repo.list_events(c.id))
    return pinned_events(user_pins, events)
