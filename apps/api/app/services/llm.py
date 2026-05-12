"""
LLM client abstraction.

OpenRouterClient hits the real API; MockLLMClient is used in tests.
`get_llm_client` is the FastAPI dependency — tests override it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import httpx

from app.config import Settings, get_settings


@dataclass(slots=True)
class LLMResult:
    content: str
    tokens_used: int
    model: str


class LLMClient(Protocol):
    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
    ) -> LLMResult: ...


class OpenRouterClient:
    """Thin wrapper around OpenRouter's chat/completions endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._default_model = settings.openrouter_model_default

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
    ) -> LLMResult:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY not configured")

        use_model = model or self._default_model
        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            # OpenRouter recommends these for analytics; harmless if absent.
            "HTTP-Referer": "https://sidequest.app",
            "X-Title": "SideQuest",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        tokens_used = int((data.get("usage") or {}).get("total_tokens") or 0)
        return LLMResult(content=content, tokens_used=tokens_used, model=use_model)


@lru_cache
def _build_client() -> LLMClient:
    return OpenRouterClient(get_settings())


def get_llm_client() -> LLMClient:
    return _build_client()
