"""Slice A — list_due() due-window math.

Drives only the in-memory repo. The Supabase impl shares the same `_is_due`
helper, so the math is covered here; the Supabase fetch path is exercised
end-to-end by the scheduler integration test (Slice C).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.scrape_sources_repo import InMemoryScrapeSourcesRepo


def _seed(repo: InMemoryScrapeSourcesRepo, **kwargs) -> dict:
    defaults = dict(conference_id="token2049", url="https://lu.ma/x")
    defaults.update(kwargs)
    return repo.create(**defaults)


def _backdate(repo: InMemoryScrapeSourcesRepo, sid: str, *, when: datetime) -> None:
    """Force-set last_scraped_at to a known value for deterministic tests."""
    repo._rows[sid]["last_scraped_at"] = when  # type: ignore[index]


def test_never_scraped_with_interval_is_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    row = _seed(repo, scrape_interval_minutes=60)
    due = repo.list_due()
    assert [r["id"] for r in due] == [row["id"]]


def test_no_interval_never_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    _seed(repo, scrape_interval_minutes=None)
    assert repo.list_due() == []


def test_disabled_never_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    _seed(repo, scrape_interval_minutes=60, enabled=False)
    assert repo.list_due() == []


def test_fresh_scrape_skipped() -> None:
    repo = InMemoryScrapeSourcesRepo()
    now = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
    row = _seed(repo, scrape_interval_minutes=60)
    _backdate(repo, row["id"], when=now - timedelta(minutes=30))  # half-way
    assert repo.list_due(now=now) == []


def test_exactly_at_boundary_is_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    now = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
    row = _seed(repo, scrape_interval_minutes=60)
    _backdate(repo, row["id"], when=now - timedelta(minutes=60))
    due = repo.list_due(now=now)
    assert [r["id"] for r in due] == [row["id"]]


def test_past_boundary_is_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    now = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
    row = _seed(repo, scrape_interval_minutes=15)
    _backdate(repo, row["id"], when=now - timedelta(hours=2))
    assert len(repo.list_due(now=now)) == 1


def test_mix_returns_only_due() -> None:
    repo = InMemoryScrapeSourcesRepo()
    now = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)

    due_row = _seed(repo, url="https://lu.ma/a", scrape_interval_minutes=15)
    _backdate(repo, due_row["id"], when=now - timedelta(hours=1))

    fresh_row = _seed(repo, url="https://lu.ma/b", scrape_interval_minutes=60)
    _backdate(repo, fresh_row["id"], when=now - timedelta(minutes=10))

    _seed(repo, url="https://lu.ma/c", scrape_interval_minutes=None)
    _seed(repo, url="https://lu.ma/d", scrape_interval_minutes=15, enabled=False)
    _seed(repo, url="https://lu.ma/e", scrape_interval_minutes=15)  # never scraped

    due = repo.list_due(now=now)
    urls = sorted(r["url"] for r in due)
    assert urls == ["https://lu.ma/a", "https://lu.ma/e"]


def test_naive_datetime_in_db_string_is_handled() -> None:
    """Supabase returns last_scraped_at as an ISO string; _is_due must accept that."""
    repo = InMemoryScrapeSourcesRepo()
    now = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
    row = _seed(repo, scrape_interval_minutes=60)
    # Simulate what supabase-py returns: ISO string with trailing Z
    repo._rows[row["id"]]["last_scraped_at"] = "2026-05-16T10:00:00Z"  # type: ignore[index]
    due = repo.list_due(now=now)
    assert len(due) == 1
