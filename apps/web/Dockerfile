# syntax=docker/dockerfile:1.7
#
# Build context MUST be the repo root, not apps/web — the web app imports
# tokens.css from ../../../design-system. The Ansible role should be configured
# with NO build_subdir (or build_subdir: ".") and dockerfile: apps/web/Dockerfile.

# -------- Build stage --------
FROM node:20-alpine AS builder

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN corepack enable && corepack prepare pnpm@9.12.0 --activate

WORKDIR /repo

# Install deps first (cached layer until lockfile changes)
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./apps/web/
WORKDIR /repo/apps/web
RUN pnpm install --frozen-lockfile

# Pull in source — both the web app and the shared design-system tokens
WORKDIR /repo
COPY apps/web/tsconfig.json apps/web/vite.config.ts apps/web/index.html ./apps/web/
COPY apps/web/public ./apps/web/public
COPY apps/web/src ./apps/web/src
COPY design-system ./design-system

# VITE_* vars are inlined at build time. The Ansible role must pass these as
# build args (docker-compose: `build.args`). Empty defaults let local builds
# succeed without secrets; production deployments MUST supply real values.
ARG VITE_SUPABASE_URL=""
ARG VITE_SUPABASE_ANON_KEY=""
ARG VITE_API_BASE=""
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY \
    VITE_API_BASE=$VITE_API_BASE

WORKDIR /repo/apps/web
RUN pnpm build


# -------- Runtime stage --------
FROM nginx:1.27-alpine AS runtime

ENV PORT=8080

RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf
COPY --from=builder /repo/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080

# nginx:alpine has a built-in entrypoint that runs `envsubst` on every file in
# /etc/nginx/templates/ — so ${PORT} in the template becomes the real port in
# /etc/nginx/conf.d/default.conf at container start.
CMD ["nginx", "-g", "daemon off;"]
