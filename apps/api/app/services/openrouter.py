"""OpenRouter client. Two patterns:

- complete()  — non-streaming, used by /curate
- stream_raw() — async generator yielding raw SSE lines, used by /chat

Streaming intentionally relays OpenRouter's `data: {...}\n\n` frames verbatim — fewer parsing
bugs, and lower TTFB to the browser.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import get_settings


async def complete(
    *,
    messages: list[dict[str, Any]],
    model: str | None = None,
    response_format: dict[str, Any] | None = None,
    temperature: float = 0.4,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    settings = get_settings()
    body: dict[str, Any] = {
        "model": model or settings.openrouter_model_default,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        body["response_format"] = response_format

    async with httpx.AsyncClient(
        base_url=settings.openrouter_base_url,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://sidequest.app",
            "X-Title": "SideQuest",
        },
        timeout=httpx.Timeout(60.0, connect=10.0),
    ) as client:
        r = await client.post("/chat/completions", json=body)
        r.raise_for_status()
        return r.json()


async def stream_raw(
    *,
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> AsyncIterator[str]:
    """Yield raw SSE lines from OpenRouter, one chunk at a time."""
    settings = get_settings()
    body = {
        "model": model or settings.openrouter_model_default,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(
        base_url=settings.openrouter_base_url,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://sidequest.app",
            "X-Title": "SideQuest",
        },
        timeout=httpx.Timeout(None, connect=10.0),
    ) as client:
        async with client.stream("POST", "/chat/completions", json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                # OpenRouter emits OpenAI-format SSE frames: `data: {...}` separated by blank line.
                if not line:
                    continue
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        yield json.dumps({"type": "done"})
                        return
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if delta:
                        yield json.dumps({"type": "delta", "content": delta})
