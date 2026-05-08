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

## Deploy

Deferred — see `../api/README.md` for the SSE-on-Vercel constraint that affects the API.
