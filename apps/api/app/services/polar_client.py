"""
Thin wrapper around the Polar SDK.

Two concerns:
  - constructing the SDK against the right server (sandbox vs production)
  - exposing the one call we make from the request path: `create_checkout`.

Webhook signature verification lives in the webhooks router (Phase 3) using
the same `standardwebhooks` package the Polar SDK depends on, so it doesn't
need a client instance.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import Settings, get_settings


class PolarConfigError(RuntimeError):
    """Raised when Polar env vars are missing at request time."""


class PolarClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.polar_access_token:
            raise PolarConfigError("POLAR_ACCESS_TOKEN is not set")
        self._settings = settings

    def _sdk(self) -> Any:
        # Import lazily so test environments without the SDK installed
        # (and without Polar config) don't pay the import cost at boot.
        from polar_sdk import Polar

        return Polar(
            server=self._settings.polar_server,
            access_token=self._settings.polar_access_token,
        )

    def create_checkout(
        self,
        *,
        product_id: str,
        success_url: str,
        metadata: dict[str, str],
    ) -> str:
        """Create a Polar hosted checkout. Returns the URL to redirect the user to.

        `metadata` round-trips on the eventual webhook payload — this is how
        the anonymous payer is identified (anon_id + conference_id).
        """
        with self._sdk() as polar:
            res = polar.checkouts.create(
                request={
                    "products": [product_id],
                    "success_url": success_url,
                    "metadata": metadata,
                }
            )
            return res.url

    def product_id_for_conference(self, conference_id: str) -> str:
        product_id = self._settings.polar_product_id_map.get(conference_id)
        if not product_id:
            raise PolarConfigError(
                f"No Polar product configured for conference '{conference_id}' "
                f"(set POLAR_PRODUCT_IDS)"
            )
        return product_id


@lru_cache
def _build_client() -> PolarClient:
    return PolarClient(get_settings())


def get_polar_client() -> PolarClient:
    """FastAPI dependency. Converts misconfig into a 503 so the response
    actually carries CORS headers — an unhandled exception leaks through
    Starlette as a bare 500 and the browser surfaces it as a CORS error."""
    try:
        return _build_client()
    except PolarConfigError as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
