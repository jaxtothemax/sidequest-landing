from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.deps import UserClaims, verify_jwt
from app.models import ChatRequest
from app.services import openrouter
from app.services.prompts import CHAT_SYSTEM

router = APIRouter()


@router.post("/chat")
async def chat(body: ChatRequest, user: UserClaims = Depends(verify_jwt)) -> EventSourceResponse:
    """SSE stream. Each frame is a JSON object: {type, content?}.

    Frame types:
      - delta: incremental token text
      - done:  stream finished
    """
    messages = [{"role": "system", "content": CHAT_SYSTEM}]
    messages.extend(m.model_dump() for m in body.messages)

    async def gen() -> AsyncIterator[dict[str, str]]:
        try:
            async for frame in openrouter.stream_raw(
                messages=messages, model=body.model
            ):
                yield {"data": frame}
        except asyncio.CancelledError:
            # Client disconnected — let it propagate so httpx aborts the upstream.
            raise
        except Exception as exc:  # noqa: BLE001
            yield {"data": f'{{"type":"error","message":"{exc}"}}'}

    return EventSourceResponse(
        gen(),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
