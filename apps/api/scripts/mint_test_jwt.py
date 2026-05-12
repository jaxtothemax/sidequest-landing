"""
Mint a Supabase JWT for a test user.

Reads SUPABASE_URL + SUPABASE_SERVICE_KEY from the environment (or apps/api/.env
if loaded by the caller). Ensures the user exists (idempotent), optionally
promotes them to admin via app_metadata.role, signs them in, and prints the
access token to stdout.

Usage:
    uv run python scripts/mint_test_jwt.py                       # default user
    uv run python scripts/mint_test_jwt.py --email you@x.com
    uv run python scripts/mint_test_jwt.py --admin
    uv run python scripts/mint_test_jwt.py --user-id-only        # print uuid, not jwt
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_EMAIL = "test+sq@sidequest.local"
DEFAULT_PASSWORD = "sq-test-pw-9X3kLm2Q"


def _admin_headers(key: str) -> dict[str, str]:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def ensure_user(url: str, key: str, email: str, password: str) -> str:
    """Create the user if missing; return user id."""
    base = url.rstrip("/")

    # Try create. If it already exists, list and find.
    r = httpx.post(
        f"{base}/auth/v1/admin/users",
        headers=_admin_headers(key),
        json={"email": email, "password": password, "email_confirm": True},
        timeout=20.0,
    )
    if r.status_code in (200, 201):
        return r.json()["id"]
    # 422 / 409 / 400 on duplicate — look the user up
    if r.status_code in (400, 409, 422):
        lookup = httpx.get(
            f"{base}/auth/v1/admin/users",
            headers=_admin_headers(key),
            params={"email": email},
            timeout=20.0,
        )
        lookup.raise_for_status()
        users = lookup.json().get("users", [])
        for u in users:
            if u.get("email", "").lower() == email.lower():
                return u["id"]
        raise SystemExit(f"user exists but lookup failed: {lookup.text}")
    r.raise_for_status()
    raise SystemExit(f"unexpected response: {r.status_code} {r.text}")


def set_admin(url: str, key: str, user_id: str, *, admin: bool) -> None:
    role = "admin" if admin else None
    httpx.put(
        f"{url.rstrip('/')}/auth/v1/admin/users/{user_id}",
        headers=_admin_headers(key),
        json={"app_metadata": {"role": role}},
        timeout=20.0,
    ).raise_for_status()


def sign_in(url: str, key: str, email: str, password: str) -> str:
    base = url.rstrip("/")
    r = httpx.post(
        f"{base}/auth/v1/token",
        params={"grant_type": "password"},
        headers={
            "apikey": key,
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password},
        timeout=20.0,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--email", default=DEFAULT_EMAIL)
    p.add_argument("--password", default=DEFAULT_PASSWORD)
    p.add_argument("--admin", action="store_true", help="promote to app_metadata.role=admin")
    p.add_argument("--user-id-only", action="store_true", help="print user id instead of JWT")
    args = p.parse_args()

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in env", file=sys.stderr)
        return 2

    user_id = ensure_user(url, key, args.email, args.password)
    set_admin(url, key, user_id, admin=args.admin)

    if args.user_id_only:
        print(user_id)
        return 0

    token = sign_in(url, key, args.email, args.password)
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
