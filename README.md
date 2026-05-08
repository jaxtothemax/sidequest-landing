# SideQuest

Personalised conference-schedule curation. Static marketing site + a new PWA + FastAPI backend.

## Repo layout

```
.
├── index.html              — marketing landing page (static, self-contained)
├── design-system/          — canonical CSS tokens + design-system docs (ds.html)
├── assets/                 — brand logos and screen mockups
├── quiz-app/               — original React/Vite mock of the onboarding quiz (kept as reference)
└── apps/
    ├── web/                — NEW PWA frontend (React + Vite + vite-plugin-pwa, Supabase-backed)
    └── api/                — NEW Python FastAPI backend (uv-managed, OpenRouter LLM proxy + scraper host)
```

The new app lives entirely under `apps/`. The marketing site (`index.html`), the design system, and
the original `quiz-app/` are untouched.

## Quick start

```bash
# Backend
cd apps/api
cp .env.example .env             # fill SUPABASE_* + OPENROUTER_API_KEY
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web
cp .env.example .env             # fill VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
pnpm install
pnpm dev                         # http://localhost:5173 — /api proxied to :8000
```

Health check the backend: `curl http://localhost:8000/health`.

## Apps

- **`apps/web`** — React 18 + Vite 6 + TypeScript PWA. Reuses design tokens from
  `design-system/styles/`. Auth via Supabase (magic link + Google OAuth). Talks to the API for
  curation and the assistant chat (SSE streamed). See `apps/web/README.md`.

- **`apps/api`** — FastAPI proxying OpenRouter, hosting the event scraper, and verifying
  Supabase JWTs against the project JWKS. Endpoints: `/api/curate`, `/api/chat` (SSE),
  `/api/events`, `/api/events/pin`. See `apps/api/README.md`.

## Marketing site

Open `index.html` in a browser, or `python -m http.server 8000` from the repo root and visit
`/index.html`. See `CLAUDE.md` for product context.

## Deploy

**Deferred.** Note: the `/api/chat` SSE endpoint will not work on Vercel (30s function cap +
buffering). Realistic targets when we ship:

- Web → Vercel (existing `sidequest-landing` project)
- API → Fly.io or Render

## TODO

- Paste the existing scraper code into `apps/api/app/scraper/sources/` (wrap in `EventSource`).
- Generate proper PWA icons (`icon-192.png`, `icon-512.png`, `icon-512-maskable.png`,
  `apple-touch-icon.png`) from `assets/symbol.svg` into `apps/web/public/`.
- Apply `apps/api/supabase/migrations/0001_init.sql` to the Supabase project + enable Google OAuth
  in the Supabase dashboard.
- Pick a deploy target for the API.
