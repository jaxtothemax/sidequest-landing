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

## Deploy (Hetzner / Ansible / Traefik)

The container is built from this directory by the Ansible role (`build_subdir: apps/api`)
and routed through Traefik. The deployment system generates the `.env` file and the
compose file — only the `Dockerfile` and source live here.

**Runtime contract**

- Binds `0.0.0.0:${PORT}` (defaults to `8000`). Traefik forwards HTTPS to this port.
- Starts unattended via `uvicorn app.main:app`. No interactive setup.
- Logs to stdout/stderr (`PYTHONUNBUFFERED=1`).
- Health endpoint: `GET /health` (returns `{"status": "ok", "version": "<git-sha>"}`).
- Runs as non-root user `app` (uid 1000).

**Required env vars**

| Var | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service-role key (server-side only) |
| `OPENROUTER_API_KEY` | OpenRouter API key for chat + curation |
| `CORS_ORIGINS` | Comma-separated allowed origins for the web app |

**Optional**

| Var | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8000` | HTTP listen port |
| `SUPABASE_JWT_JWKS_URL` | `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` | JWT verification |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `OPENROUTER_MODEL_DEFAULT` | `anthropic/claude-sonnet-4-5` | Default chat/curation model |
| `OPENROUTER_MODEL_CHEAP` | `anthropic/claude-haiku-4-5` | Cheap fallback model |

**Migrations**

Schema is applied out-of-band against Supabase:

```bash
supabase db push                          # via Supabase CLI
# or
psql "$DATABASE_URL" -f supabase/migrations/0001_init.sql
psql "$DATABASE_URL" -f supabase/migrations/0002_seed_token2049.sql
```

There is no entrypoint migration step — the container starts immediately and serves
requests against the existing schema.

## Implemented so far

- **Phase 0** — skeleton, `/health`, JWT verifier wired (no protected routes yet).
- **Phase 1** — `GET /api/conferences[/{id}[/events]]`, schema migrations `0001_init.sql` + `0002_seed_token2049.sql`, in-memory fallback for local dev when Supabase isn't configured.
- **Phase 2** — `POST /api/curate` (no auth). Pre-filters events to attended days, sends candidates + onboarding to OpenRouter (default `anthropic/claude-sonnet-4-5`), parses JSON (handles Claude's markdown-fenced output), validates against the candidate set, persists to `anonymous_curations`.
- **Phase 3** — `POST /api/auth/claim`, `POST /api/unlock` (stub), `GET /api/me/schedule`. Real Supabase Auth JWT verification via JWKS. The claim flow copies an `anonymous_curations` row into `user_curations` for the signed-in user; unlock flips `user_entitlements.unlocked=true`; me/schedule returns the active curation enriched with full event details, sorted by start time. `scripts/mint_test_jwt.py` provisions test users via the Supabase Admin API for local smoke runs.
- **Phase 4** — `POST /api/events/pin`, `GET /api/me/events`. `services/schedule_merge.py` owns the merge logic (pure function): `pinned=true` events not in the curation are appended with `priority='must'`; `pinned=false` events are filtered out of the curation. `/api/me/schedule` now applies this overlay automatically.
- **Phase 5** — Admin layer behind `require_admin` (reads `app_metadata.role == "admin"` from the verified JWT). `/api/admin/events` (GET/POST/PATCH/DELETE), `/api/admin/events/{id}/lock`, `/api/admin/conferences`. Patching an event auto-locks it (sets `locked=true`); admin can toggle lock explicitly. `services/admin_repo.py::scraper_upsert()` is the helper future scrapers must call — it no-ops on `locked=true` rows, enforcing the contract documented in `0001_init.sql`. Promote users via `scripts/set_admin.sql` (manual) or `scripts/mint_test_jwt.py --admin` (automated).
- **Phase 6** — `POST /api/chat` via `sse-starlette`. The system prompt is assembled from the user's onboarding answers, active pin-merged schedule, and conference metadata (so the assistant grounds answers in specific events). OpenRouter chat-completions streamed in; emitted as `{type:'delta', content}` frames terminated by `{type:'done'}` and an OpenAI-style `[DONE]` line. User/assistant turns are persisted to `chat_messages` post-stream (best-effort). `X-Accel-Buffering: no` header for nginx compatibility.

**All six phases complete.**

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
