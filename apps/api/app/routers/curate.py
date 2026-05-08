from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import UserClaims, get_supabase, verify_jwt
from app.models import CurateRequest, CurateResponse, CuratedItem, EventDTO
from app.services import openrouter
from app.services.prompts import CURATE_SYSTEM

router = APIRouter()


@router.post("/curate", response_model=CurateResponse)
async def curate(body: CurateRequest, user: UserClaims = Depends(verify_jwt)) -> CurateResponse:
    # 1. Pull the relevant event catalogue.
    try:
        sb = get_supabase()
        catalogue_rows = (
            sb.table("events")
            .select("*")
            .eq("conference_id", body.onboarding.conference_id)
            .execute()
            .data
            or []
        )
    except HTTPException:
        catalogue_rows = []

    catalogue = [EventDTO(**row) for row in catalogue_rows]

    if not catalogue:
        # Cold start before scraper has run — return empty schedule so the UI degrades gracefully.
        return CurateResponse(schedule=[], tokens_used=0)

    # 2. Ask the LLM for a curated subset.
    user_payload = {
        "onboarding": body.onboarding.model_dump(by_alias=True),
        "catalogue": [e.model_dump(mode="json") for e in catalogue],
    }

    try:
        result = await openrouter.complete(
            messages=[
                {"role": "system", "content": CURATE_SYSTEM},
                {"role": "user", "content": json.dumps(user_payload, default=str)},
            ],
            model=body.model,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2500,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"OpenRouter error: {exc}"
        ) from exc

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    tokens_used = result.get("usage", {}).get("total_tokens", 0)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "LLM returned non-JSON response"
        ) from None

    schedule_raw = parsed.get("schedule", [])
    valid_ids = {e.id for e in catalogue}
    schedule = [
        CuratedItem(**item) for item in schedule_raw if item.get("event_id") in valid_ids
    ]

    # 3. Persist the picks as pins.
    if schedule:
        try:
            sb = get_supabase()
            sb.table("user_events").upsert(
                [
                    {
                        "user_id": user.sub,
                        "event_id": item.event_id,
                        "pinned": True,
                        "priority": item.priority,
                        "rationale": item.rationale,
                    }
                    for item in schedule
                ],
                on_conflict="user_id,event_id",
            ).execute()
        except HTTPException:
            pass  # supabase not configured in early dev

    return CurateResponse(schedule=schedule, tokens_used=tokens_used)
