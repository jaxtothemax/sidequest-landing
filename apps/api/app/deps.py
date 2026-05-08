"""FastAPI dependencies — JWT verification, Supabase client, OpenRouter client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from app.config import Settings, get_settings


@dataclass(frozen=True)
class UserClaims:
    sub: str
    email: str | None
    raw: dict[str, Any]


_JWKS_CACHE: dict[str, tuple[PyJWKClient, float]] = {}
_JWKS_TTL_SECONDS = 600


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    now = time.time()
    cached = _JWKS_CACHE.get(jwks_url)
    if cached and (now - cached[1]) < _JWKS_TTL_SECONDS:
        return cached[0]
    client = PyJWKClient(jwks_url, cache_keys=True)
    _JWKS_CACHE[jwks_url] = (client, now)
    return client


def verify_jwt(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> UserClaims:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()

    try:
        client = _get_jwks_client(settings.jwks_url)
        signing_key = client.get_signing_key_from_jwt(token).key
        # Supabase issues ES256 (asymmetric) JWTs by default since 2024.
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["ES256", "RS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing sub")

    return UserClaims(sub=sub, email=payload.get("email"), raw=payload)


CurrentUser = Depends(verify_jwt)


def get_supabase():
    """Return a service-role Supabase client. Imported lazily so tests can patch."""
    from supabase import create_client  # type: ignore[import-not-found]

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Supabase not configured (set SUPABASE_URL + SUPABASE_SERVICE_KEY)",
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_openrouter_client() -> httpx.AsyncClient:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OpenRouter not configured (set OPENROUTER_API_KEY)",
        )
    return httpx.AsyncClient(
        base_url=settings.openrouter_base_url,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://sidequest.app",
            "X-Title": "SideQuest",
        },
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
