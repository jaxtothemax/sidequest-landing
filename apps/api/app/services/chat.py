"""
Chat orchestration.

build_system_prompt assembles a system message from the user's onboarding
answers + their active (pin-merged) schedule + conference metadata.

stream_chat is the FastAPI-facing generator that yields SSE frame dicts
({type: 'delta', content} ... {type: 'done'}) for sse-starlette.

Persistence to chat_messages happens post-stream, best-effort.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.models.schemas import ScheduleItem
from app.services.llm import LLMClient


SYSTEM_PREAMBLE = """You are SideQuest, a helpful conference companion.

You help the user navigate their conference week — answering questions
about events on their personalised schedule, suggesting alternatives, and
helping them prepare. Be concise, friendly, and reference specific events
by title when relevant.

Below is the context the user has shared with you. If they ask you to
modify their schedule, explain what you'd recommend but note that you
can't yet make changes directly — they should use the pin/unpin actions
in the app."""


def _summarise_onboarding(onboarding: dict[str, Any]) -> str:
    parts = []
    role = onboarding.get("role")
    goals = onboarding.get("goals") or []
    topics = onboarding.get("topics") or []
    must_haves = onboarding.get("mustHaves") or []
    pace = onboarding.get("pace")
    energy = onboarding.get("energy")
    social = onboarding.get("social")
    attendance = onboarding.get("attendance")
    days = onboarding.get("days") or []

    if role:
        parts.append(f"role: {role}")
    if goals:
        parts.append(f"goals (ranked): {', '.join(goals)}")
    if topics:
        parts.append(f"topics: {', '.join(topics)}")
    if must_haves:
        parts.append(f"must-meet: {', '.join(must_haves)}")
    if attendance:
        parts.append(f"attendance: {attendance}")
    if days:
        parts.append(f"days attending: {', '.join(map(str, days))}")
    if pace is not None or energy is not None or social is not None:
        parts.append(
            f"sliders: pace={pace}, energy={energy}, social={social} (0-100)"
        )
    return "\n".join(parts) if parts else "(no onboarding answers provided)"


def _summarise_schedule(schedule: list[ScheduleItem]) -> str:
    if not schedule:
        return "(no events on schedule yet)"
    lines = []
    for item in schedule:
        when = item.start.strftime("%a %d %b · %H:%M")
        lines.append(
            f"- [{item.priority}] {when}  {item.title}  @ {item.venue or '?'}  ({item.id})"
        )
    return "\n".join(lines)


def build_system_prompt(
    *,
    onboarding: dict[str, Any] | None,
    schedule: list[ScheduleItem],
    conference: dict[str, Any] | None,
) -> str:
    sections = [SYSTEM_PREAMBLE, ""]
    if conference:
        sections.append(
            f"## Conference\n{conference.get('name', '?')} "
            f"({conference.get('city', '?')}, {conference.get('start_date', '?')} – {conference.get('end_date', '?')})"
        )
    sections.append(f"\n## User profile\n{_summarise_onboarding(onboarding or {})}")
    sections.append(f"\n## Current schedule\n{_summarise_schedule(schedule)}")
    return "\n".join(sections)


async def stream_chat(
    *,
    user_messages: list[dict[str, str]],
    system_prompt: str,
    llm: LLMClient,
    model: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE frame dicts. Final frame is {'type':'done'}."""

    messages = [{"role": "system", "content": system_prompt}, *user_messages]

    try:
        async for delta in llm.complete_stream(messages, model=model):
            yield {"type": "delta", "content": delta}
    except Exception as e:  # noqa: BLE001 — surface to caller as a frame
        yield {"type": "error", "content": f"{type(e).__name__}: {e}"}
    yield {"type": "done"}


# Used by the router to format an SSE EventSourceResponse payload from the
# dict frames. sse-starlette accepts either strings or dicts with `data`/`event`,
# so we serialize each frame to JSON and emit as `data:`.


def to_sse_frames(
    frames: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[dict[str, str]]:
    async def _iter() -> AsyncIterator[dict[str, str]]:
        async for f in frames:
            yield {"data": json.dumps(f, separators=(",", ":"))}
        # Append the OpenAI-style [DONE] terminator the frontend looks for.
        yield {"data": "[DONE]"}

    return _iter()
