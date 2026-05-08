"""CLI runner for scrapers.

Examples:
    uv run python -m app.scraper.run --list
    uv run python -m app.scraper.run --source token2049 --dry-run
    uv run python -m app.scraper.run --source token2049 \
        --conference-id token2049-dubai-2026
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.scraper.registry import REGISTRY, get_source
from app.services.supabase import upsert_events


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="scraper")
    p.add_argument("--list", action="store_true", help="list registered sources and exit")
    p.add_argument("--source", help="source id from the registry, e.g. token2049")
    p.add_argument(
        "--conference-id",
        help="conference id to pass through; defaults to the source id",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print results as JSON instead of writing to Supabase",
    )
    return p.parse_args()


async def amain() -> int:
    args = parse_args()
    if args.list:
        for name in REGISTRY:
            print(name)
        return 0

    if not args.source:
        print("--source is required (or pass --list)", file=sys.stderr)
        return 2

    source = get_source(args.source)
    conference_id = args.conference_id or args.source
    events = await source.fetch_events(conference_id)
    print(f"Fetched {len(events)} events from {source.__class__.__name__}", file=sys.stderr)

    rows = [e.model_dump(mode="json") for e in events]
    if args.dry_run:
        json.dump(rows, sys.stdout, indent=2, default=str)
        print()
        return 0

    upsert_events(rows)
    print(f"Upserted {len(rows)} rows into events", file=sys.stderr)
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
