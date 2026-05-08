-- 0001_init.sql — initial schema for SideQuest
-- Run via: supabase db push  (or paste into the SQL editor)

-- ─── profiles ─────────────────────────────────────────────────────────
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    title text,
    avatar_url text,
    twitter text,
    linkedin text,
    website text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles: read own" on public.profiles
    for select to authenticated using (id = auth.uid());

create policy "profiles: insert own" on public.profiles
    for insert to authenticated with check (id = auth.uid());

create policy "profiles: update own" on public.profiles
    for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ─── onboarding_state ─────────────────────────────────────────────────
create table if not exists public.onboarding_state (
    user_id uuid primary key references auth.users(id) on delete cascade,
    state jsonb not null,
    completed_at timestamptz,
    updated_at timestamptz not null default now()
);

alter table public.onboarding_state enable row level security;

create policy "onboarding: read own" on public.onboarding_state
    for select to authenticated using (user_id = auth.uid());

create policy "onboarding: write own" on public.onboarding_state
    for insert to authenticated with check (user_id = auth.uid());

create policy "onboarding: update own" on public.onboarding_state
    for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- ─── events (public catalog, scraper-written) ─────────────────────────
create table if not exists public.events (
    id text primary key,
    conference_id text not null,
    title text not null,
    description text default '',
    start timestamptz not null,
    "end" timestamptz not null,
    venue text default '',
    tags text[] not null default '{}',
    url text,
    capacity integer,
    attendees integer,
    source text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists events_conference_idx on public.events (conference_id);
create index if not exists events_start_idx on public.events (start);

alter table public.events enable row level security;

-- Anyone (including anon) can read the public catalog.
create policy "events: public read" on public.events
    for select to anon, authenticated using (true);
-- No insert/update/delete policies → defaults to deny. Scraper writes via service-role key,
-- which bypasses RLS by design.

-- ─── user_events (per-user pins) ──────────────────────────────────────
create table if not exists public.user_events (
    user_id uuid not null references auth.users(id) on delete cascade,
    event_id text not null references public.events(id) on delete cascade,
    pinned boolean not null default true,
    priority text check (priority in ('must','should','maybe')),
    rationale text,
    pinned_at timestamptz not null default now(),
    primary key (user_id, event_id)
);

create index if not exists user_events_user_idx on public.user_events (user_id);

alter table public.user_events enable row level security;

-- IMPORTANT: every policy filters by user_id — including SELECT — so a missing SELECT policy
-- doesn't leak other users' schedules.
create policy "user_events: read own" on public.user_events
    for select to authenticated using (user_id = auth.uid());

create policy "user_events: insert own" on public.user_events
    for insert to authenticated with check (user_id = auth.uid());

create policy "user_events: update own" on public.user_events
    for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "user_events: delete own" on public.user_events
    for delete to authenticated using (user_id = auth.uid());

-- Realtime: enable replication so devices see pin updates live.
alter publication supabase_realtime add table public.user_events;

-- ─── chat_messages ────────────────────────────────────────────────────
create table if not exists public.chat_messages (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('user','assistant','system')),
    content text not null,
    created_at timestamptz not null default now()
);

create index if not exists chat_messages_user_created_idx
    on public.chat_messages (user_id, created_at desc);

alter table public.chat_messages enable row level security;

create policy "chat: read own" on public.chat_messages
    for select to authenticated using (user_id = auth.uid());

create policy "chat: insert own" on public.chat_messages
    for insert to authenticated with check (user_id = auth.uid());

create policy "chat: delete own" on public.chat_messages
    for delete to authenticated using (user_id = auth.uid());

-- ─── updated_at trigger helpers ───────────────────────────────────────
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles
    for each row execute function public.set_updated_at();

drop trigger if exists onboarding_set_updated_at on public.onboarding_state;
create trigger onboarding_set_updated_at before update on public.onboarding_state
    for each row execute function public.set_updated_at();

drop trigger if exists events_set_updated_at on public.events;
create trigger events_set_updated_at before update on public.events
    for each row execute function public.set_updated_at();
