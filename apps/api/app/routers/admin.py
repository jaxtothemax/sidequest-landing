from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import CurrentUser, require_admin
from app.models.schemas import (
    AdminConferenceUpsert,
    AdminEventCreate,
    AdminEventOut,
    AdminEventUpdate,
    LockRequest,
)
from app.services.admin_repo import EventsAdminRepo, get_events_admin_repo

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
    return repo.upsert_conference(fields)
