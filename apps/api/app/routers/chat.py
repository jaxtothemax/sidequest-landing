from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.deps import CurrentUser, require_user
from app.models.schemas import ChatRequest, ScheduleItem
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.chat import build_system_prompt, stream_chat
from app.services.chat_store import ChatStore, get_chat_store
from app.services.curations_store import CurationsStore, get_curations_store
from app.services.llm import LLMClient, get_llm_client
from app.services.pins_store import PinsStore, get_pins_store
from app.services.schedule_merge import merge_schedule

router = APIRouter(prefix="/api", tags=["chat"])


def _resolve_context(
    user_id: str,
    conference_id: str | None,
    curations: CurationsStore,
    pins: PinsStore,
    repo: CatalogRepo,
) -> tuple[dict[str, Any] | None, list[ScheduleItem], dict[str, Any] | None]:
    """Pull onboarding answers, merged schedule, and conference metadata."""
    curation = curations.get_active_user_curation(user_id, conference_id)
    onboarding = curation["onboarding"] if curation else None
    conf_id = (curation or {}).get("conference_id") or conference_id

    schedule: list[ScheduleItem] = []
    conference_meta: dict[str, Any] | None = None
    if conf_id:
        conf = repo.get_conference(conf_id)
        if conf is not None:
            conference_meta = conf.model_dump()
        if curation:
            events = repo.list_events(conf_id)
            user_pins = pins.list_for_user(user_id)
            schedule = merge_schedule(
                curated=curation["schedule"] or [], pins=user_pins, events=events
            )
    return onboarding, schedule, conference_meta


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    curations: Annotated[CurationsStore, Depends(get_curations_store)],
    pins: Annotated[PinsStore, Depends(get_pins_store)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    chat_store: Annotated[ChatStore, Depends(get_chat_store)],
) -> EventSourceResponse:
    onboarding, schedule, conference = _resolve_context(
        user.id, body.conference_id, curations, pins, repo
    )
    system_prompt = build_system_prompt(
        onboarding=onboarding, schedule=schedule, conference=conference
    )
    user_messages = [m.model_dump() for m in body.messages]

    # Capture last user message for persistence after the stream.
    last_user = next(
        (m.content for m in reversed(body.messages) if m.role == "user"), None
    )
    conf_id = (conference or {}).get("id")

    async def event_iter() -> AsyncIterator[dict[str, str]]:
        assistant_chunks: list[str] = []
        frames = stream_chat(
            user_messages=user_messages,
            system_prompt=system_prompt,
            llm=llm,
            model=body.model,
        )
        async for frame in frames:
            if frame.get("type") == "delta" and isinstance(frame.get("content"), str):
                assistant_chunks.append(frame["content"])
            yield {"data": json.dumps(frame, separators=(",", ":"))}
        yield {"data": "[DONE]"}

        # Best-effort persistence after the stream completes
        if last_user:
            chat_store.append(
                user_id=user.id,
                conference_id=conf_id,
                role="user",
                content=last_user,
            )
        if assistant_chunks:
            chat_store.append(
                user_id=user.id,
                conference_id=conf_id,
                role="assistant",
                content="".join(assistant_chunks),
            )

    return EventSourceResponse(
        event_iter(),
        headers={"X-Accel-Buffering": "no"},  # disable nginx buffering for SSE
    )
