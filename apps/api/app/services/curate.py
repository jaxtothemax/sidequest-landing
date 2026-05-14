"""
Curation orchestration.

1. Pre-filter candidate events to days the user is attending (the only
   rule-based filter; the rest is the LLM's call).
2. Build prompt + call LLM.
3. Parse JSON, validate against the candidate set.
4. Return CuratedItem[] to the router, which persists and responds.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status

from app.models.schemas import ConferenceOut, CuratedItem, EventOut, OnboardingState
from app.services.llm import LLMClient, LLMResult

VALID_PRIORITY = {"must", "should", "maybe"}

SYSTEM_PROMPT = """You are SideQuest, an expert conference schedule curator.

Given a user's onboarding answers and a list of candidate events for the
conference, return the BEST schedule for them as strict JSON. Output ONLY
a JSON object with this exact shape:

{
  "schedule": [
    {
      "event_id": "<id from candidate_events>",
      "day": "<YYYY-MM-DD of the event>",
      "start": "<ISO 8601 datetime, same as candidate>",
      "end":   "<ISO 8601 datetime, same as candidate>",
      "rationale": "<1-2 sentences on why this event matters for THIS user>",
      "priority": "must" | "should" | "maybe"
    }
  ]
}

Rules:
- Use ONLY event_ids that appear in candidate_events. Never invent events.
- Respect time conflicts: do not put two events at the same time unless
  one is clearly a "drop-in" and you flag it as "maybe".
- Pace: target events/day = round(3 + (pace/100) * 6) — so pace=0 → 3/day,
  pace=50 → 6/day, pace=100 → 9/day. Use it as a soft target.
- Energy (0=evening person, 100=morning person): weight earlier slots more
  as energy rises.
- Social (0=deep 1:1s, 100=big rooms): when picking between competing
  events at the same time, lean toward the one that matches.
- Goals are ordered by priority — the first goal weighs most.
- mustHaves names people/companies/speakers the user wants to meet. Boost
  events that match (in title, description, or tags).
- Topics are interest signals. Weight tag/title overlap heavily.
- Rationale must reference THIS user's specific goals/topics/mustHaves —
  not generic phrases like "great networking opportunity".
- Output JSON only. No markdown, no commentary, no code fences."""


def _attended_days(onboarding: OnboardingState, conference: ConferenceOut) -> set[int]:
    """Day-of-month numbers the user is attending."""
    if onboarding.attendance == "full":
        return {d.day_num for d in conference.days if d.enabled}
    # 'partial' or 'side-only' or null → use the explicit days list, fall back to enabled
    if onboarding.days:
        return set(onboarding.days)
    return {d.day_num for d in conference.days if d.enabled}


def filter_candidates(
    events: list[EventOut], onboarding: OnboardingState, conference: ConferenceOut
) -> list[EventOut]:
    days = _attended_days(onboarding, conference)
    if not days:
        return list(events)
    return [e for e in events if e.start.day in days]


def _event_to_candidate(e: EventOut) -> dict[str, Any]:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "start": e.start.isoformat(),
        "end": e.end.isoformat(),
        "venue": e.venue,
        "tags": list(e.tags),
        "attendees": e.attendees,
    }


def build_user_message(onboarding: OnboardingState, candidates: list[EventOut]) -> str:
    payload = {
        "onboarding": onboarding.model_dump(),
        "candidate_events": [_event_to_candidate(e) for e in candidates],
    }
    return json.dumps(payload, separators=(",", ":"), default=str)


def _strip_fences(raw: str) -> str:
    """Claude (via OpenRouter) sometimes wraps JSON in ```json ... ``` fences."""
    s = raw.strip()
    if s.startswith("```"):
        # drop first line (``` or ```json) and trailing fence
        first_newline = s.find("\n")
        if first_newline != -1:
            s = s[first_newline + 1 :]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def parse_schedule(raw: str, valid_ids: set[str]) -> list[CuratedItem]:
    """Parse the LLM's JSON; reject ids that aren't in the candidate set."""
    cleaned = _strip_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Surface the first 200 chars so the operator can see what came back.
        preview = (raw[:200] + "…") if len(raw) > 200 else raw
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM returned non-JSON ({e}): {preview!r}",
        ) from e

    items = data.get("schedule") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM JSON missing 'schedule' list",
        )

    out: list[CuratedItem] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        event_id = raw_item.get("event_id")
        if not isinstance(event_id, str) or event_id not in valid_ids:
            continue  # silently skip hallucinated ids
        priority = raw_item.get("priority")
        if priority not in VALID_PRIORITY:
            priority = "should"
        out.append(
            CuratedItem(
                event_id=event_id,
                day=str(raw_item.get("day", "")),
                start=str(raw_item.get("start", "")),
                end=str(raw_item.get("end", "")),
                rationale=str(raw_item.get("rationale", "")),
                priority=priority,
            )
        )
    return out


async def curate_schedule(
    *,
    onboarding: OnboardingState,
    conference: ConferenceOut,
    events: list[EventOut],
    llm: LLMClient,
    model: str | None = None,
) -> tuple[list[CuratedItem], LLMResult]:
    candidates = filter_candidates(events, onboarding, conference)
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="no candidate events for the selected days",
        )

    user_msg = build_user_message(onboarding, candidates)
    result = await llm.complete_json(SYSTEM_PROMPT, user_msg, model=model)
    valid_ids = {e.id for e in candidates}
    schedule = parse_schedule(result.content, valid_ids)
    return schedule, result
