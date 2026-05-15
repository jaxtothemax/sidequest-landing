from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_admin
from app.models.schemas import (
    AdminConferenceUpsert,
    AdminEventCreate,
    AdminEventOut,
    AdminEventUpdate,
    ConferenceOut,
    LockRequest,
    ScrapeRunResult,
    ScrapeSourceCreate,
    ScrapeSourceOut,
    ScrapeSourceUpdate,
)
from app.scraper.luma_runner import SourceScrapeStats, run_for_source
from app.services.admin_repo import EventsAdminRepo, get_events_admin_repo
from app.services.catalog import CatalogRepo, get_catalog_repo
from app.services.scrape_sources_repo import (
    ScrapeSourcesRepo,
    get_scrape_sources_repo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/conferences", response_model=list[ConferenceOut])
def list_all_conferences(
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> list[ConferenceOut]:
    """List ALL conferences (active + inactive). Public /api/conferences stays active-only."""
    return repo.list_conferences(include_inactive=True)


def _to_out(row: dict) -> AdminEventOut:
    return AdminEventOut.model_validate(row)


@router.get("/events", response_model=list[AdminEventOut])
def list_events(
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
    conference_id: str | None = None,
    locked: bool | None = None,
    is_manual: bool | None = None,
) -> list[AdminEventOut]:
    rows = repo.list_events(
        conference_id=conference_id, locked=locked, is_manual=is_manual
    )
    return [_to_out(r) for r in rows]


@router.post("/events", response_model=AdminEventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    body: AdminEventCreate,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> AdminEventOut:
    fields = body.model_dump()
    # Datetimes need to be serializable for supabase-py — convert to ISO strings.
    fields["starts_at"] = fields["starts_at"].isoformat()
    fields["ends_at"] = fields["ends_at"].isoformat()
    if repo.get_event(body.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"event '{body.id}' already exists",
        )
    row = repo.create_event(fields=fields, updated_by=admin.id)
    return _to_out(row)


@router.patch("/events/{event_id}", response_model=AdminEventOut)
def update_event(
    event_id: str,
    body: AdminEventUpdate,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> AdminEventOut:
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    # Serialize datetimes if present
    for k in ("starts_at", "ends_at"):
        if k in patch and hasattr(patch[k], "isoformat"):
            patch[k] = patch[k].isoformat()
    if not patch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty patch",
        )
    row = repo.update_event(event_id, patch=patch, updated_by=admin.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"event '{event_id}' not found",
        )
    return _to_out(row)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> None:
    if not repo.delete_event(event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"event '{event_id}' not found",
        )


@router.post("/events/{event_id}/lock", response_model=AdminEventOut)
def set_event_lock(
    event_id: str,
    body: LockRequest,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> AdminEventOut:
    row = repo.set_lock(event_id, locked=body.locked, updated_by=admin.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"event '{event_id}' not found",
        )
    return _to_out(row)


@router.post("/conferences", status_code=status.HTTP_200_OK)
def upsert_conference(
    body: AdminConferenceUpsert,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> dict:
    fields = body.model_dump()
    for k in ("start_date", "end_date"):
        if fields.get(k) is not None:
            fields[k] = fields[k].isoformat()
    if fields.get("days") is None:
        fields.pop("days", None)
    return repo.upsert_conference(fields)


# ============================================================================
# Scrape sources
# ============================================================================


def _source_out(row: dict) -> ScrapeSourceOut:
    return ScrapeSourceOut.model_validate(row)


@router.get(
    "/conferences/{conference_id}/sources",
    response_model=list[ScrapeSourceOut],
)
def list_sources(
    conference_id: str,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[ScrapeSourcesRepo, Depends(get_scrape_sources_repo)],
) -> list[ScrapeSourceOut]:
    return [_source_out(r) for r in repo.list_for_conference(conference_id)]


@router.post(
    "/conferences/{conference_id}/sources",
    response_model=ScrapeSourceOut,
    status_code=status.HTTP_201_CREATED,
)
def add_source(
    conference_id: str,
    body: ScrapeSourceCreate,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[ScrapeSourcesRepo, Depends(get_scrape_sources_repo)],
) -> ScrapeSourceOut:
    url = body.url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="url is required",
        )
    row = repo.create(
        conference_id=conference_id,
        url=url,
        source_type=body.source_type,
        enabled=body.enabled,
        scrape_interval_minutes=body.scrape_interval_minutes,
    )
    return _source_out(row)


@router.patch("/sources/{source_id}", response_model=ScrapeSourceOut)
def update_source(
    source_id: str,
    body: ScrapeSourceUpdate,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[ScrapeSourcesRepo, Depends(get_scrape_sources_repo)],
) -> ScrapeSourceOut:
    row = repo.update(
        source_id,
        url=body.url.strip() if body.url is not None else None,
        enabled=body.enabled,
        scrape_interval_minutes=body.scrape_interval_minutes,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"source '{source_id}' not found",
        )
    return _source_out(row)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: str,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    repo: Annotated[ScrapeSourcesRepo, Depends(get_scrape_sources_repo)],
) -> None:
    if not repo.delete(source_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"source '{source_id}' not found",
        )


@router.post(
    "/conferences/{conference_id}/scrape",
    response_model=ScrapeRunResult,
)
def trigger_scrape(
    conference_id: str,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    sources_repo: Annotated[ScrapeSourcesRepo, Depends(get_scrape_sources_repo)],
    events_repo: Annotated[EventsAdminRepo, Depends(get_events_admin_repo)],
) -> ScrapeRunResult:
    """Run every enabled Luma source on this conference and upsert events.

    Per-source failures (network error, bad calendar URL, etc.) are caught
    and recorded against the source's last_scrape_status; one bad source
    doesn't fail the whole run. Per-event failures inside a source are
    counted but not surfaced individually — see server logs.
    """
    sources = [s for s in sources_repo.list_for_conference(conference_id) if s["enabled"]]
    if not sources:
        return ScrapeRunResult(
            ok=True,
            message="No enabled scrape sources for this conference.",
            sources_attempted=0,
            sources_failed=0,
            events_added=0,
            events_updated=0,
        )

    total = SourceScrapeStats()
    failures: list[str] = []

    for source in sources:
        url = source["url"]
        source_id = source["id"]
        try:
            stats = run_for_source(
                conference_id=conference_id,
                source_url=url,
                events_repo=events_repo,
            )
        except Exception as exc:
            logger.exception("admin.trigger_scrape source=%s failed", url)
            failures.append(f"{url}: {exc}")
            sources_repo.record_scrape(
                source_id,
                status="error",
                error=str(exc)[:500],
            )
            continue

        sources_repo.record_scrape(
            source_id,
            status="ok",
            events_added=stats.events_added,
            events_updated=stats.events_updated,
        )
        total.merge(stats)

    failed = len(failures)
    if failed == 0:
        message = (
            f"Scraped {len(sources)} source(s): "
            f"added {total.events_added}, updated {total.events_updated}, "
            f"skipped (locked) {total.events_skipped_locked}, "
            f"failed events {total.events_failed}."
        )
    else:
        message = (
            f"Scraped {len(sources)} source(s); {failed} failed. "
            f"Added {total.events_added}, updated {total.events_updated}. "
            f"First failure: {failures[0]}"
        )

    return ScrapeRunResult(
        ok=failed == 0,
        message=message,
        sources_attempted=len(sources),
        sources_failed=failed,
        events_added=total.events_added,
        events_updated=total.events_updated,
    )
