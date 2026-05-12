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
- **Phase 1** — `GET /api/conferences[/{id}[/events]]`, schema migrations `0001_init.sql` + `0002_seed_token2049.sql`, in-memory fallback for local dev when Supabase isn't configured.

Phases 2–6 land incrementally; see the plan file.

## Data backend

The catalog routes work in two modes — driven by env vars:

- **With Supabase** (`SUPABASE_URL` + `SUPABASE_SERVICE_KEY` set): reads via the service-role client. Apply `supabase/migrations/` first (`supabase db push` or `psql -f`).
- **Without Supabase** (env empty): falls back to the in-memory copy of the seed in `app/services/seed_data.py`. This lets the API + tests run with zero setup. The two are kept in sync by hand — update both when you change the seed.

## Admin role

Admin role is encoded as a Supabase user app_metadata claim:

```sql
update auth.users
set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || '{"role":"admin"}'::jsonb
where email = 'you@example.com';
```

The backend reads `app_metadata.role` from the verified JWT — no separate admin table.
