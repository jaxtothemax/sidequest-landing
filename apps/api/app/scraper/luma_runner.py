"""Drives a single Luma `scrape_sources` entry end-to-end.

The admin trigger endpoint iterates enabled sources and calls
:func:`run_for_source` once per source. Per-event errors are absorbed so
one bad event doesn't kill the whole run; the scraper itself raising
(network failure, bad slug, calendar 404) propagates and is recorded as
the source's last_scrape_status = "error" by the caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.scraper.sources.luma import LumaScraper, normalize_event
from app.services.admin_repo import EventsAdminRepo

logger = logging.getLogger(__name__)


@dataclass
class SourceScrapeStats:
    events_added: int = 0
    events_updated: int = 0
    events_skipped_locked: int = 0
    events_failed: int = 0

    def merge(self, other: SourceScrapeStats) -> None:
        self.events_added += other.events_added
        self.events_updated += other.events_updated
        self.events_skipped_locked += other.events_skipped_locked
        self.events_failed += other.events_failed


def run_for_source(
    *,
    conference_id: str,
    source_url: str,
    events_repo: EventsAdminRepo,
    scraper: LumaScraper | None = None,
    fetch_details: bool = False,
    max_pages: int | None = None,
) -> SourceScrapeStats:
    """Scrape one Luma source and upsert events into `events_repo`.

    Args:
        conference_id: SideQuest conference to attach events to.
        source_url: Full Luma URL (or bare slug). Stored as `events.source`.
        events_repo: Repo to upsert into. Tests inject the in-memory backend.
        scraper: Optional pre-built scraper (used by tests with MockTransport).
            When None, a fresh LumaScraper is built and disposed.
        fetch_details: When True, also call `/event/get` for each entry to
            populate description/capacity/attendees. Costs N extra HTTP
            requests, so default off — admin can opt in for slow but rich
            re-scrapes.
        max_pages: Cap on calendar pagination (None = walk to end).

    Returns:
        Per-source stats. Caller is responsible for recording these via
        `ScrapeSourcesRepo.record_scrape`.

    Raises:
        Anything raised by the scraper itself (httpx.HTTPError, ValueError
        from missing calendar id, etc.). Per-event failures are caught
        internally and counted in `events_failed`.
    """
    owns_scraper = scraper is None
    s = scraper or LumaScraper()
    try:
        entries = s.scrape_calendar(source_url, max_pages=max_pages)
        details_map = s.fetch_all_details(entries) if fetch_details else {}
    finally:
        if owns_scraper:
            s.close()

    stats = SourceScrapeStats()
    for entry in entries:
        try:
            api_id = (entry.get("event") or {}).get("api_id")
            details = details_map.get(api_id) if api_id else None
            row = normalize_event(
                entry,
                conference_id=conference_id,
                source=source_url,
                details=details,
            )
            if row is None:
                stats.events_failed += 1
                continue

            existed = events_repo.get_event(row["id"]) is not None
            upserted = events_repo.scraper_upsert(row)
            if not upserted:
                # locked=true — scraper contract requires skip
                stats.events_skipped_locked += 1
            elif existed:
                stats.events_updated += 1
            else:
                stats.events_added += 1
        except Exception:
            logger.exception("luma_runner.event_failed source_url=%s", source_url)
            stats.events_failed += 1

    logger.info(
        "luma_runner.done source_url=%s added=%d updated=%d skipped_locked=%d failed=%d",
        source_url,
        stats.events_added,
        stats.events_updated,
        stats.events_skipped_locked,
        stats.events_failed,
    )
    return stats
