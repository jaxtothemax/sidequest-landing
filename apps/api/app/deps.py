from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings


@dataclass(slots=True)
class CurrentUser:
    id: str
    email: str | None
    role: str | None  # 'admin' if app_metadata.role == 'admin'
    raw_claims: dict[str, Any]


_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0, "url": ""}
_JWKS_TTL_SECONDS = 60 * 60  # 1h


async def _load_jwks(jwks_url: str) -> list[dict[str, Any]]:
    now = time.time()
    if (
        _jwks_cache["keys"] is not None
        and _jwks_cache["url"] == jwks_url
        and now - _jwks_cache["fetched_at"] < _JWKS_TTL_SECONDS
    ):
        return _jwks_cache["keys"]  # type: ignore[no-any-return]

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        data = resp.json()

    keys = data.get("keys", [])
    _jwks_cache.update({"keys": keys, "fetched_at": now, "url": jwks_url})
    return keys


def _signing_key_for(token: str, jwks_keys: list[dict[str, Any]]) -> Any:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for k in jwks_keys:
        if k.get("kid") == kid:
            return jwt.PyJWK(k).key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="signing key not found in JWKS",
    )


async def _verify_jwt(token: str, settings: Settings) -> dict[str, Any]:
    jwks_url = settings.jwks_url
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWKS not configured",
        )
    keys = await _load_jwks(jwks_url)
    key = _signing_key_for(token, keys)
    try:
        return jwt.decode(  # type: ignore[no-any-return]
            token,
            key=key,
            algorithms=["ES256", "RS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {e}",
        ) from e


def _claims_to_user(claims: dict[str, Any]) -> CurrentUser:
    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing sub claim")
    app_meta = claims.get("app_metadata") or {}
    role = app_meta.get("role") if isinstance(app_meta, dict) else None
    return CurrentUser(
        id=sub,
        email=claims.get("email"),
        role=role if isinstance(role, str) else None,
        raw_claims=claims,
    )


async def require_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()
    claims = await _verify_jwt(token, settings)
    return _claims_to_user(claims)


async def optional_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> CurrentUser | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1].strip()
        claims = await _verify_jwt(token, settings)
        return _claims_to_user(claims)
    except HTTPException:
        return None


async def require_admin(
    user: Annotated[CurrentUser, Depends(require_user)],
) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )
    return user
