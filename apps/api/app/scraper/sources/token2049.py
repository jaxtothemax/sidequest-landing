"""TOKEN2049 scraper — STUB.

Replace the body of `fetch_events` with the real scraper logic (paste it from the existing
implementation). The shape that needs to come out is `list[EventDTO]`.

Until then this stub returns a tiny canned set so the rest of the pipeline is testable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.scraper.base import EventDTO, EventSource


class Token2049Source(EventSource):
    id = "token2049"

    async def fetch_events(self, conference_id: str) -> list[EventDTO]:
        # TODO: paste real scraper here. Must return EventDTO instances with stable ids.
        return [
            EventDTO(
                id=f"{conference_id}:stable-summit-iv",
                conference_id=conference_id,
                title="Stable Summit IV",
                description="Founders & investors gathering on stablecoin infra.",
                start=datetime(2026, 4, 29, 9, 0, tzinfo=timezone.utc),
                end=datetime(2026, 4, 29, 11, 0, tzinfo=timezone.utc),
                venue="Madinat Jumeirah",
                tags=["Founders", "Stablecoins"],
                url="https://example.com/stable-summit",
                source=self.id,
            ),
            EventDTO(
                id=f"{conference_id}:investor-coffee-seed",
                conference_id=conference_id,
                title="Investor Coffee — Seed Stage",
                description="Speed-dating round with seed VCs.",
                start=datetime(2026, 4, 29, 11, 30, tzinfo=timezone.utc),
                end=datetime(2026, 4, 29, 12, 30, tzinfo=timezone.utc),
                venue="Madinat Jumeirah · Beach Lawn",
                tags=["Investors"],
                source=self.id,
            ),
        ]
