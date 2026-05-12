from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_user
from app.models.schemas import EventOut, ScheduleItem, ScheduleResponse
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.curations_store import CurationsStore, get_curations_store

router = APIRouter(prefix="/api/me", tags=["me"])


def _merge_curation_with_events(
    curated: list[dict], events: list[EventOut]
) -> list[ScheduleItem]:
    by_id = {e.id: e for e in events}
    out: list[ScheduleItem] = []
    for item in curated:
        ev = by_id.get(item.get("event_id"))
        if ev is None:
            # Event might have been removed; skip silently. Phase 5+ may surface this.
            continue
        out.append(
            ScheduleItem(
                id=ev.id,
                conference_id=ev.conference_id,
                title=ev.title,
                description=ev.description,
                start=ev.start,
                end=ev.end,
                venue=ev.venue,
                tags=list(ev.tags),
                url=ev.url,
                capacity=ev.capacity,
                attendees=ev.attendees,
                rationale=item.get("rationale", ""),
                priority=item.get("priority", "should"),
                inSchedule=True,
            )
        )
    out.sort(key=lambda s: s.start)
    return out


@router.get("/schedule", response_model=ScheduleResponse)
def get_my_schedule(
    user: Annotated[CurrentUser, Depends(require_user)],
    store: Annotated[CurationsStore, Depends(get_curations_store)],
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
    schedule = _merge_curation_with_events(curation["schedule"] or [], events)
    return ScheduleResponse(conference_id=conf_id, schedule=schedule)
