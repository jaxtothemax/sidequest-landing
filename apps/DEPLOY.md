# Deploy Handoff — sidequest-landing → Hetzner / Ansible / Traefik

This document is the handoff to whoever (human or agent) configures the Ansible
role that deploys this repo. Both apps under `apps/` follow the Hetzner /
Docker-Compose / Traefik contract (see the repo's deployable-repository spec).

Repo: `https://github.com/zkokelj/sidequest-landing`
Branch: controlled in infra config (`apps[].branch`), not here.

---

## Prompt for the Ansible agent

You are configuring the Ansible deploy role for `zkokelj/sidequest-landing`.
The repo contains **two deployable apps** under `apps/`, each with its own
Dockerfile and runtime contract. Read this document in full, then add two
entries to the `apps:` list in your infra config — one per app described below.

For each app, you must:

1. Set `repo`, `branch`, `dockerfile`, and (only where noted) `build_subdir`.
2. Provision env vars via the generated `.env` file (runtime).
3. Provision `build_args` where the app needs build-time secrets (web only).
4. Configure Traefik to forward HTTPS to the documented internal port.
5. Wire a health check to the documented endpoint.
6. Provision external resources (Supabase, OpenRouter) **out-of-band** — neither
   app boots its own database. Schema migrations are applied by hand against
   Supabase before first deploy (see `apps/api/README.md`).

After deploy, verify each app responds 200 on its health endpoint via the
public Traefik hostname before marking the rollout green.

---

## App 1 — `sidequest-api` (FastAPI backend)

**Path in repo:** `apps/api/`
**Dockerfile:** `apps/api/Dockerfile`
**Build context:** `apps/api/` — set `build_subdir: apps/api`
**Internal port:** `${PORT}`, defaults to `8000`
**Health endpoint:** `GET /health` → `{"status":"ok"}`
**Run mode:** non-root user `app` (uid 1000), `PYTHONUNBUFFERED=1`, logs to stdout/stderr.
**Migrations:** none at container start — applied out-of-band against Supabase.

### Required runtime env vars

| Var | Source | Notes |
| --- | --- | --- |
| `SUPABASE_URL` | Vault | e.g. `https://abcd.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Vault | service-role key, **server-side only** |
| `OPENROUTER_API_KEY` | Vault | `sk-or-v1-...` |
| `CORS_ORIGINS` | Computed | comma-separated; must include the web app's public origin |

### Optional runtime env vars

| Var | Default | Notes |
| --- | --- | --- |
| `PORT` | `8000` | listen port |
| `SUPABASE_JWT_JWKS_URL` | derived from `SUPABASE_URL` | override only if Supabase JWKS path changes |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | |
| `OPENROUTER_MODEL_DEFAULT` | `anthropic/claude-sonnet-4-5` | |
| `OPENROUTER_MODEL_CHEAP` | `anthropic/claude-haiku-4-5` | |

### Traefik hint

The API streams SSE on `POST /api/chat`. The Dockerfile already sets
`X-Accel-Buffering: no` at the app layer, but make sure Traefik does **not**
buffer responses for this service.

---

## App 2 — `sidequest-web` (React SPA, served by nginx)

**Path in repo:** `apps/web/`
**Dockerfile:** `apps/web/Dockerfile`
**Build context:** **repo root** — do **NOT** set `build_subdir`, or set it to `"."`.
**Internal port:** `${PORT}`, defaults to `8080`
**Health endpoint:** `GET /healthz` → `ok` (plain text, 200)
**Run mode:** nginx:1.27-alpine, SPA fallback to `/index.html`, logs to stdout/stderr.

### Why the build context is the repo root

The app imports tokens from `../../../design-system/styles/tokens.css`. If you
set `build_subdir: apps/web`, the build fails because `design-system/` is not
in the context. The Dockerfile `COPY`s both `apps/web/` and `design-system/`
from the repo root.

### Build-time args (CRITICAL — see below)

Vite inlines `VITE_*` variables into the JS bundle at build time. They **must**
be passed as Docker `build.args`, not just runtime env vars. If you only set
runtime env, the deployed bundle will contain empty strings and the app will
fail to connect to Supabase.

| Build arg | Source | Notes |
| --- | --- | --- |
| `VITE_SUPABASE_URL` | Vault | same value as the API's `SUPABASE_URL` |
| `VITE_SUPABASE_ANON_KEY` | Vault | anon (public) key, **not** the service key |
| `VITE_API_BASE` | Computed | public origin of `sidequest-api`, e.g. `https://api.sidequest.example`. Empty string = same-origin (only valid if Traefik reverse-proxies `/api` on the same hostname). |

### Runtime env vars

| Var | Default | Notes |
| --- | --- | --- |
| `PORT` | `8080` | nginx listen port; rendered into the config by the nginx:alpine entrypoint via `envsubst` |

### Sample infra entry (adapt to your role's schema)

```yaml
apps:
  - name: sidequest-api
    repo: https://github.com/zkokelj/sidequest-landing
    branch: main
    build_subdir: apps/api
    dockerfile: apps/api/Dockerfile
    internal_port: 8000
    health_path: /health
    env:
      SUPABASE_URL: "{{ vault_supabase_url }}"
      SUPABASE_SERVICE_KEY: "{{ vault_supabase_service_key }}"
      OPENROUTER_API_KEY: "{{ vault_openrouter_api_key }}"
      CORS_ORIGINS: "https://app.sidequest.example"
    traefik:
      host: api.sidequest.example
      buffering: false   # required for SSE on /api/chat

  - name: sidequest-web
    repo: https://github.com/zkokelj/sidequest-landing
    branch: main
    # build_subdir intentionally omitted — context must be the repo root
    dockerfile: apps/web/Dockerfile
    internal_port: 8080
    health_path: /healthz
    build_args:
      VITE_SUPABASE_URL: "{{ vault_supabase_url }}"
      VITE_SUPABASE_ANON_KEY: "{{ vault_supabase_anon_key }}"
      VITE_API_BASE: "https://api.sidequest.example"
    env: {}
    traefik:
      host: app.sidequest.example
```

---

## Verification checklist (run after first deploy)

```bash
# API
curl -fsS https://api.sidequest.example/health
# → {"status":"ok"}

# Web
curl -fsS https://app.sidequest.example/healthz
# → ok

# Web → API connectivity (no auth required)
curl -fsS https://app.sidequest.example/api/conferences   # if /api is same-origin
# OR
curl -fsS https://api.sidequest.example/api/conferences
# → JSON array of conferences

# Web bundle picked up VITE_SUPABASE_URL at build time
curl -sS https://app.sidequest.example/ \
  | grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' \
  | head -1 \
  | xargs -I{} curl -sS "https://app.sidequest.example/{}" \
  | grep -oE 'https://[a-z0-9-]+\.supabase\.co' \
  | head -1
# → should print your supabase project URL, NOT empty
```

If the last command prints nothing, the `VITE_*` build args were not passed —
fix the infra config and rebuild.

---

## Things that are NOT this repo's concern

- TLS cert issuance (Traefik / Let's Encrypt at the edge).
- Backups of Supabase data.
- Rotation of the OpenRouter / Supabase keys.
- DNS for `api.*` and `app.*` hostnames.
- Generating the deployed `docker-compose.yml` — that lives in the Ansible role.
