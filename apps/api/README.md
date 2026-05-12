# sidequest-api

FastAPI backend for SideQuest — personalised conference schedule curation.

Built in phases (see `/Users/zigakokelj/.claude/plans/ok-now-let-s-plan-inherited-scott.md` for the
full design). Each phase ships behind a smoke-test gate before the next one starts.

## Quick start

```bash
cp .env.example .env       # fill SUPABASE_*, OPENROUTER_API_KEY
uv sync
uv run uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
```

## Smoke tests

```bash
./scripts/smoke.sh phase-0     # /health
./scripts/smoke.sh phase-1     # conferences + events
# ...one entry per implemented phase
```

## Tests

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Docker

```bash
docker build -t sidequest-api .
docker run --rm -p 8000:8000 --env-file .env sidequest-api
```

## Implemented so far

- **Phase 0** — skeleton, `/health`, JWT verifier wired (no protected routes yet).

Phases 1–6 land incrementally; see the plan file.

## Admin role

Admin role is encoded as a Supabase user app_metadata claim:

```sql
update auth.users
set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || '{"role":"admin"}'::jsonb
where email = 'you@example.com';
```

The backend reads `app_metadata.role` from the verified JWT — no separate admin table.
