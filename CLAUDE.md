# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static marketing site for **SideQuest**. No build system, no package manager — just HTML/CSS/JS served as-is. Linked to the `sidequest-landing` Vercel project (`.vercel/project.json`).

### Product positioning (post-pivot, 2026-05)

SideQuest is a **personalised conference schedule curation tool**, not an event-discovery / check-in app. The funnel is a 10-question, ~90-second quiz designed in Figma file `qbfOQAATpuWlwe4o6hz4et`, node `4592:757` ("Pivot Design"). Flow: Pick conference → Attendance → Days → Role → Goals → Topics → Pace → Networking style → People to meet → Review → Curated schedule ("Your TOKEN2049 is ready. 21 events across 2 days. 6 people on watch."). The landing page's primary CTA "Take Quiz" routes to `/quiz.html` — currently a stub; the real quiz will live there later. **Pricing (free vs. paywall) is undecided — keep all pricing language off the landing page.** The hero phone mockups are gradient placeholders awaiting real screenshots.

## Working with the site

- **Preview locally**: open `index.html` directly, or run a static server from the repo root (e.g. `python -m http.server 8000`) and visit `/index.html`, `/ds.html`, or `/design-system/ds.html`. There is no `npm`/`yarn` step.
- **Deploy**: `vercel deploy` (preview) or `vercel deploy --prod`. The project is already linked.
- No tests, no linter, no formatter configured.

## Layout

- `index.html` — landing page. **Self-contained**: all CSS tokens, component styles, and JS are inlined in this single file (~850 lines). It does **not** import anything from `design-system/styles/`.
- `design-system/ds.html` — the canonical design-system docs page. Imports `design-system/styles/tokens.css` and `design-system/styles/shared.css`.
- `ds.html` (repo root) — a near-duplicate of `design-system/ds.html` that links to the same external stylesheets via relative path. Treat the `design-system/ds.html` copy as the source of truth; keep them in sync if you edit either.
- `design-system/styles/tokens.css` — all design tokens (brand palette, ink/red/blue ramps, semantic light/dark variables, type scale, spacing on a 4pt grid, radius, elevation, motion, z-index).
- `design-system/styles/shared.css` — shared "doc chrome" (header, nav, layout) used by the design-system pages.
- `assets/` — brand logos (`logo-h/v-bright/dark*.svg`, `symbol.svg`) and phone-screen mockups (`screen-*.png`) embedded in the landing page.

## Architecture notes for editors

- **Two parallel token systems exist.** `index.html` defines its own CSS custom properties inline (`--bg`, `--text`, `--blue`, `--red`, `--orb-*`, `--feat-*-bg`, etc.) under `[data-theme="dark"]` and `[data-theme="light"]` blocks. `design-system/styles/tokens.css` defines a richer, separately-namespaced system (`--sq-red-500`, `--bg-canvas`, `--fg-default`, `--space-*`, etc.). The two are not unified — colors overlap but variable names do not. Edits to one **do not** propagate to the other; update both deliberately if changing brand values.
- **Theme switching**: the `<html data-theme="...">` attribute drives all theming. The toggle button in the header reads/writes `localStorage["sq-theme"]` (`index.html`) or `localStorage["ds-theme"]` (design-system pages). When `data-theme` is absent, a `prefers-color-scheme: dark` media query in `tokens.css` applies dark values.
- **Fonts**: Cabinet Grotesk (display) and Satoshi (body) load from Fontshare; JetBrains Mono loads from Google Fonts (used in `shared.css`). All three are CDN-loaded — no local font files.
- **Hero video ping-pong loop** (`index.html` ~line 811): plays a hero video forward via native playback, then drives `currentTime` backward via `requestAnimationFrame` for a seamless reverse, then loops. Touch this carefully — small numerical changes to `dt` clamping or end-thresholds cause stutter or jumps.
- Landing-page sections are anchored by id: `#features`, `#how`, `#events`, `#cta` (referenced by the in-page nav).

## Design tokens at a glance

Brand: `--sq-red #E62C5A`, `--sq-blue #3B82F6`, `--sq-blue-deep #4B60B8`, `--sq-red-soft #FF8C8E`, `--sq-blue-soft #BBC7FF`. Spacing follows a 4pt grid (`--space-2` = 4px through `--space-16` = 128px). Radii from `--radius-xs` (4px) to `--radius-3xl` (24px) plus `--radius-pill`. See `design-system/ds.html` rendered for the full visual reference.
