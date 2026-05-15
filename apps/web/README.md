# sidequest-web

PWA frontend for SideQuest. React 18 + Vite 6 + TypeScript + vite-plugin-pwa.

## Quick start

```bash
cp .env.example .env  # fill VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
pnpm install
pnpm dev               # http://localhost:5173 — /api proxied to localhost:8000
```

The companion API lives in `../api` and must be running for `/api/*` calls to succeed.

## Layout

```
src/
  main.tsx, App.tsx, router.tsx
  lib/        supabase client, queryClient, fetcher (injects Supabase JWT)
  api/        typed wrappers around backend endpoints
  stores/     zustand: onboarding, auth, schedule
  hooks/      useUser, useEvents, useChatStream
  features/
    onboarding/  10-step quiz + paywall (ported from quiz-app)
    mainapp/     chat / schedule / profile tabs
    auth/        magic-link + Google OAuth
  components/   shared UI (EventCard, Slider, Header, Button)
  data/         CONFERENCES, SUGGESTIONS, GOALS_BY_ROLE, TOPICS, SEED_EVENTS (offline fallback)
  styles/       imports design-system tokens.css + shared.css + per-feature CSS
  pwa/          SW registration, NewVersionPrompt, OfflineBanner
  types/        Event, OnboardingState, ChatMessage
```

## Design system

Imports the canonical tokens from the repo-level design system:

```css
@import "../../../../design-system/styles/tokens.css";
@import "../../../../design-system/styles/shared.css";
```

No Tailwind. Component CSS lives alongside features.

## PWA

- Auto-update SW with a "new version" prompt — keeps the cached schedule across SW swaps.
- `GET /api/events` is `NetworkFirst` cached for 1 hour.
- `POST /api/curate` and the SSE `/api/chat` endpoint are never cached.
- Manifest icons live in `public/`. Generate them from `../../assets/symbol.svg`.

## Deploy (Hetzner / Ansible / Traefik)

The container is built from the **repo root** (not `apps/web`) because the app
imports tokens from `../../../design-system/`. Configure the Ansible role with:

```yaml
apps:
  - name: sidequest-web
    # build_subdir omitted — context is the repo root
    dockerfile: apps/web/Dockerfile
    build_args:
      VITE_SUPABASE_URL: "{{ vault_supabase_url }}"
      VITE_SUPABASE_ANON_KEY: "{{ vault_supabase_anon_key }}"
      VITE_API_BASE: "{{ api_base_url }}"  # e.g. https://api.sidequest.example
```

**Runtime contract**

- Static SPA served by nginx (alpine).
- Binds `0.0.0.0:${PORT}` (defaults to `8080`). Traefik forwards HTTPS to this port.
- Health endpoint: `GET /healthz` (returns `ok`).
- SPA fallback: all non-asset paths serve `index.html` (React Router).
- Logs to stdout/stderr.

**Build-time vars** (passed via `build.args` — Vite inlines these into the bundle)

| Var | Purpose |
| --- | --- |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon (public) key |
| `VITE_API_BASE` | API origin (empty = same-origin reverse-proxy) |

**Runtime vars**

| Var | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8080` | HTTP listen port |

**Local build test**

```bash
# from repo root
docker build -f apps/web/Dockerfile \
  --build-arg VITE_SUPABASE_URL=https://demo.supabase.co \
  --build-arg VITE_SUPABASE_ANON_KEY=anon-demo \
  -t sidequest-web:test .
docker run --rm -e PORT=8080 -p 8080:8080 sidequest-web:test
curl http://localhost:8080/healthz
```
