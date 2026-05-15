# Onboarding — sidequest-landing

Welcome. This doc gets you from zero to a running local dev environment in
about 15 minutes. Two apps (`apps/api`, `apps/web`) plus a static marketing
site (`index.html`). The PR-merged code is autodeployed to:

- API → https://api.sidequest.zigakokelj.com
- Web → https://sidequest.zigakokelj.com (TBD per current infra)

If anything below is wrong, fix it in this doc — future-you will thank you.

---

## 1. Prerequisites

Install these once:

| Tool | Version | Install (macOS) |
| --- | --- | --- |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop/ |
| Node | 20+ | `brew install node@20` (or use `mise`/`fnm`) |
| pnpm | 9.x | `corepack enable && corepack prepare pnpm@9.12.0 --activate` |
| Python | 3.12+ | `brew install python@3.12` |
| uv | 0.5+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Supabase CLI | latest | `brew install supabase/tap/supabase` |
| GitHub CLI | latest | `brew install gh && gh auth login` |

Verify:

```bash
docker --version
node -v          # v20.x
pnpm -v          # 9.x
uv --version     # 0.5+
supabase --version
```

---

## 2. Clone

```bash
git clone https://github.com/zkokelj/sidequest-landing.git
cd sidequest-landing
```

Branch naming convention: `<your-name>/<short-description>` (e.g.
`zkokelj/fix-pwa-icons`). PR base is always `main`.

---

## 3. Secrets you'll need

The maintainer (Žiga, info@zkode.si) will share these out-of-band — ask in
DM / your shared password manager:

**For `apps/api/.env`:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY` (server-only — never commit, never put in the web app)
- `OPENROUTER_API_KEY`

**For `apps/web/.env`:**
- `VITE_SUPABASE_URL` (same value as `SUPABASE_URL`)
- `VITE_SUPABASE_ANON_KEY` (the public anon key — different from the service key)

You can also run the API against a **local Supabase** (recommended — see
section 5) and only need the `OPENROUTER_API_KEY` shared. Pick one path.

---

## 4. API setup — `apps/api`

```bash
cd apps/api
cp .env.example .env
# edit .env: fill SUPABASE_* (or leave empty — see section 5),
# OPENROUTER_API_KEY, and CORS_ORIGINS=http://localhost:5173

uv sync                                 # installs deps into .venv/
uv run uvicorn app.main:app --reload --port 8000
```

Smoke test in another terminal:

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"dev"}

./scripts/smoke.sh phase-0              # runs the deployed-phase smoke tests
```

### Run the test suite

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

Tests don't need Supabase — they use the in-memory fallback.

---

## 5. Database — three options

The API needs a Supabase project for auth, curations, and chat history. Pick one:

### Option A — Local Supabase (recommended for daily dev)

Fully offline. Real Postgres + GoTrue + Storage in Docker. Migrations
auto-apply. You mint your own JWTs. Email auth flows through a local
inbox (no SMTP setup needed).

**One-time init.** The repo ships `supabase/migrations/` but not the
CLI config — run `supabase init` once to create it:

```bash
cd apps/api
supabase init                           # creates supabase/config.toml
# (answer "no" to the VS Code / Deno prompts unless you want them)
```

**Start the stack.** First run pulls ~1 GB of Docker images (2-3 min):

```bash
supabase start
```

This boots:

- Postgres on `localhost:54322` (every migration in
  `supabase/migrations/` runs automatically, in order)
- GoTrue + PostgREST + Storage on `localhost:54321`
- **Studio** (web admin UI) on http://127.0.0.1:54323
- **Inbucket** (local email inbox — catches magic links and confirmations)
  on http://127.0.0.1:54324

When it finishes it prints the keys you need. Re-print anytime:

```bash
supabase status
# API URL:          http://127.0.0.1:54321
# DB URL:           postgresql://postgres:postgres@127.0.0.1:54322/postgres
# Studio URL:       http://127.0.0.1:54323
# Inbucket URL:     http://127.0.0.1:54324
# anon key:         eyJ...
# service_role key: eyJ...
```

**Wire the API.** Edit `apps/api/.env`:

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_KEY=<paste service_role key from `supabase status`>
OPENROUTER_API_KEY=<your real key — no local substitute>
CORS_ORIGINS=http://localhost:5173
```

Restart `uvicorn` so it picks up the env. Quick verify:

```bash
curl http://localhost:8000/api/conferences
# JSON from local DB (not the in-memory fallback)
```

**Wire the web app.** Edit `apps/web/.env`:

```env
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=<paste anon key from `supabase status`>
VITE_API_BASE=
```

Restart `pnpm dev` (Vite only reads `.env` on boot).

**Day-to-day commands:**

```bash
supabase status              # re-print URLs + keys
supabase stop                # shut everything down
supabase db reset            # nuke DB + re-apply migrations (clean slate)
supabase migration new <name>  # create a new migration file
supabase db diff             # show schema diff vs migrations
```

**Auth gotchas in local mode:**

- Email signups don't send real email. Confirmation links and magic
  links land in Inbucket at http://127.0.0.1:54324 — open them there.
- Google OAuth won't work without configuring a separate dev OAuth
  client pointing at `http://127.0.0.1:54321/auth/v1/callback`. For
  daily dev, just use email + password (the auth screen supports it).
- To grant yourself admin, run the SQL from section 7 against the
  local DB: `psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f apps/api/scripts/set_admin.sql`
  (after editing the email in that file), or paste the query into
  Studio's SQL editor.

### Option B — Shared dev Supabase (cloud, isolated from prod)

Žiga can provision a separate dev project on Supabase free tier and give
you access. You get a real cloud URL + keys, no Docker overhead, but the
DB is shared with anyone else on the team — careful with destructive
queries.

### Option C — No Supabase at all

Leave `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` empty in `apps/api/.env`.
The API falls back to the in-memory seed (`app/services/seed_data.py`):
catalog routes work, auth/curations/chat **do not**. Useful for UI
tire-kicking only.

---

## 6. Web setup — `apps/web`

```bash
cd apps/web
cp .env.example .env
# edit .env: fill VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
# Leave VITE_API_BASE empty — Vite proxies /api → localhost:8000 in dev.

pnpm install
pnpm dev
```

Open http://localhost:5173. The quiz should load. Walk through it to verify
end-to-end:

1. Pick a conference → days → role → goals → topics → pace → style → people.
2. Hit "Build my schedule" — confirms `POST /api/curate` works.
3. Land on the paywall preview — confirms the LLM round-trip succeeded.

### Run the type checker

```bash
pnpm typecheck
```

No test suite yet on the web side.

---

## 7. Admin access

If you need the `/admin` panel (managing conferences, events, scrape sources):

1. Sign up with your email at http://localhost:5173 (uses Supabase auth).
2. Run this in the Supabase SQL Editor (cloud) or via `psql` (local):

   ```sql
   update auth.users
      set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
                           || '{"role":"admin"}'::jsonb
    where email = 'you@example.com'
   returning id, email, raw_app_meta_data;
   ```

3. Sign out + sign back in (the JWT needs to refresh to pick up the claim).
4. Navigate to http://localhost:5173/admin.

Canonical SQL: `apps/api/scripts/set_admin.sql`.

---

## 8. Editing the marketing landing page

`index.html` at the repo root is the standalone marketing page — no build,
no React. Just open it in a browser, or:

```bash
python -m http.server 8000
# → http://localhost:8000/index.html
```

It is **not** the same codebase as `apps/web`. Tokens are inlined in the
file. Don't confuse it with the PWA app.

---

## 9. Deploy

Every merge to `main` autodeploys both apps to the Hetzner host via Ansible
(see `apps/DEPLOY.md` for the full infra contract). Verify after merge:

```bash
curl https://api.sidequest.zigakokelj.com/health
# → {"status":"ok","version":"<short SHA of HEAD on main>"}
```

If `version` doesn't match the SHA you just merged, autodeploy may be stuck —
ping Žiga.

---

## 10. Common gotchas

- **Supabase migrations are out-of-band.** The API doesn't apply them at
  startup. Use `supabase db push` (cloud) or rely on `supabase start`
  (local) to apply `apps/api/supabase/migrations/*.sql`.
- **Same-origin `/api`.** In dev, Vite proxies `/api/*` to `localhost:8000`.
  In prod, Traefik does the same routing. Don't hardcode API hostnames in
  the web code.
- **PWA service worker.** `pnpm dev` registers the SW in production builds
  only — if a stale SW is causing weird caching, open DevTools → Application
  → Service Workers → Unregister.
- **Theme is OS-driven.** The web app has no theme toggle yet; it follows
  `prefers-color-scheme`. Two browsers may render differently if one has
  Dark Reader / `chrome://flags/#enable-force-dark` set.
- **`VITE_*` are build-time inlined.** Changing them in `.env` requires a
  Vite restart (`pnpm dev` reads on boot).
- **Docker builds for prod take the repo root as context** for `apps/web`
  (because of the shared design-system import) but `apps/api` only.
  Documented in `apps/DEPLOY.md`.

---

## 11. Where to ask

- Quick questions / pairing → DM Žiga (info@zkode.si)
- Deploy issues → check `apps/DEPLOY.md` first, then Ansible repo
- Architecture context → `CLAUDE.md` at the repo root has the product framing
- Per-app deep-dives → `apps/api/README.md` and `apps/web/README.md`

Welcome aboard.
