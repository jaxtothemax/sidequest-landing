from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import UserClaims, get_supabase, verify_jwt
from app.models import EventDTO, EventsResponse, PinRequest, PinResponse

router = APIRouter()


@router.get("/events", response_model=EventsResponse)
def list_events(conference_id: str | None = Query(default=None)) -> EventsResponse:
    """Public catalog of events. Anyone can read; scraper writes via service role."""
    try:
        sb = get_supabase()
    except HTTPException:
        # Supabase not configured — return empty so the web app doesn't crash in early dev.
        return EventsResponse(events=[], conference=None)

    q = sb.table("events").select("*")
    if conference_id:
        q = q.eq("conference_id", conference_id)
    rows = q.order("start").execute().data or []
    events = [EventDTO(**row) for row in rows]
    conf = {"id": conference_id, "name": conference_id or "", "city": ""} if conference_id else None
    return EventsResponse(events=events, conference=conf)


@router.post("/events/pin", response_model=PinResponse)
def pin_event(body: PinRequest, user: UserClaims = Depends(verify_jwt)) -> PinResponse:
    sb = get_supabase()
    if body.pinned:
        result = (
            sb.table("user_events")
            .upsert(
                {"user_id": user.sub, "event_id": body.event_id, "pinned": True},
                on_conflict="user_id,event_id",
            )
            .execute()
        )
        row = (result.data or [None])[0]
        return PinResponse(ok=True, user_event=row)
    else:
        sb.table("user_events").delete().eq("user_id", user.sub).eq(
            "event_id", body.event_id
        ).execute()
        return PinResponse(ok=True, user_event=None)


@router.get("/me/events", response_model=list[EventDTO])
def my_events(user: UserClaims = Depends(verify_jwt)) -> list[EventDTO]:
    """Return the events this user has pinned, joined with the events table."""
    sb = get_supabase()
    rows = (
        sb.table("user_events")
        .select("event_id, events(*)")
        .eq("user_id", user.sub)
        .execute()
        .data
        or []
    )
    out: list[EventDTO] = []
    for row in rows:
        ev = row.get("events")
        if ev:
            out.append(EventDTO(**ev))
    return out
