from __future__ import annotations

from app.scraper.base import EventSource
from app.scraper.sources.token2049 import Token2049Source

REGISTRY: dict[str, EventSource] = {
    "token2049": Token2049Source(),
}


def get_source(name: str) -> EventSource:
    if name not in REGISTRY:
        raise KeyError(f"Unknown scraper source: {name!r}. Known: {list(REGISTRY)}")
    return REGISTRY[name]
