# sidequest-api

FastAPI backend for the SideQuest PWA. Proxies LLM calls through OpenRouter and hosts the
event scraper.

## Quick start

```bash
cp .env.example .env  # fill in SUPABASE_* and OPENROUTER_API_KEY
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`.

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | – | liveness |
| GET | `/api/events` | – | public catalog of scraped events |
| POST | `/api/curate` | Bearer JWT | builds a personalised schedule from onboarding state |
| POST | `/api/chat` | Bearer JWT | SSE stream from the assistant |
| POST | `/api/events/pin` | Bearer JWT | pin/unpin an event for the current user |

JWTs are Supabase-issued and verified against the project's JWKS endpoint (ES256).

## Scraper

```bash
# list available sources
uv run python -m app.scraper.run --list

# dry run (no DB writes)
uv run python -m app.scraper.run --source token2049 --dry-run

# real run (writes to Supabase events table via service-role key)
uv run python -m app.scraper.run --source token2049
```

The user's existing scraper code goes into `app/scraper/sources/<id>.py` and must implement the
`EventSource` protocol from `app/scraper/base.py`.

## Tests

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Deploy

**Deferred.** Note: the `/api/chat` SSE endpoint will not work on Vercel (30s function cap +
buffering). Realistic targets: Fly.io, Render, or any host that supports long-lived HTTP.
