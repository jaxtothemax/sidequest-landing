-- SideQuest backend — initial schema.
-- Covers all tables for Phases 1–6. Empty tables are harmless for phases not yet wired.

-- ============================================================================
-- Conferences + events catalog (public-read)
-- ============================================================================

create table if not exists conferences (
  id          text primary key,
  name        text not null,
  city        text,
  venue       text,
  start_date  date,
  end_date    date,
  timezone    text default 'UTC',
  meta        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

create table if not exists conference_days (
  conference_id text not null references conferences(id) on delete cascade,
  day_num       int  not null,
  dow           text not null,
  date          date,
  enabled       boolean not null default true,
  primary key (conference_id, day_num)
);

create table if not exists events (
  id            text primary key,
  conference_id text not null references conferences(id) on delete cascade,
  title         text not null,
  description   text,
  starts_at     timestamptz not null,
  ends_at       timestamptz not null,
  venue         text,
  tags          text[] not null default '{}',
  url           text,
  capacity      int,
  attendees     int,
  source        text,                                  -- 'seed' | 'manual' | scraper id
  raw           jsonb,
  is_manual     boolean not null default false,        -- created by admin, not scraper
  locked        boolean not null default false,        -- scraper must skip rows where true
  updated_by    uuid,                                  -- references auth.users(id); admin who last edited
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists events_conference_starts_at_idx
  on events (conference_id, starts_at);
create index if not exists events_tags_gin
  on events using gin (tags);
-- partial index for the scraper hot path: only candidates the scraper may overwrite
create index if not exists events_unlocked_idx
  on events (conference_id) where locked = false;

create table if not exists conference_suggestions (
  id            text primary key,
  conference_id text not null references conferences(id) on delete cascade,
  kind          text not null check (kind in ('people','companies','speakers')),
  name          text not null,
  role          text,
  meta          jsonb not null default '{}'::jsonb
);

create index if not exists conference_suggestions_conf_kind_idx
  on conference_suggestions (conference_id, kind);

-- ============================================================================
-- Anonymous curations (anon_id is the secret)
-- ============================================================================

create table if not exists anonymous_curations (
  anon_id        uuid primary key,
  conference_id  text references conferences(id) on delete set null,
  onboarding     jsonb not null,
  schedule       jsonb not null,
  tokens_used    int,
  model          text,
  created_at     timestamptz not null default now(),
  claimed_by     uuid,                                 -- auth.users(id) once claimed
  claimed_at     timestamptz
);

create index if not exists anonymous_curations_unclaimed_idx
  on anonymous_curations (created_at) where claimed_by is null;

-- ============================================================================
-- User-scoped tables (RLS to auth.uid())
-- ============================================================================

create table if not exists user_curations (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null,                       -- references auth.users(id)
  conference_id   text references conferences(id) on delete set null,
  onboarding      jsonb not null,
  schedule        jsonb not null,
  is_active       boolean not null default true,
  source_anon_id  uuid,
  tokens_used     int,
  model           text,
  created_at      timestamptz not null default now()
);

create index if not exists user_curations_active_idx
  on user_curations (user_id, conference_id, created_at desc);

create table if not exists user_event_pins (
  user_id    uuid not null,
  event_id   text not null references events(id) on delete cascade,
  pinned     boolean not null,                         -- false = explicit hide
  pinned_at  timestamptz not null default now(),
  primary key (user_id, event_id)
);

create table if not exists user_entitlements (
  user_id      uuid primary key,
  unlocked     boolean not null default false,
  unlocked_at  timestamptz,
  provider     text,
  provider_ref text,
  expires_at   timestamptz,
  created_at   timestamptz not null default now()
);

create table if not exists chat_messages (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null,
  conference_id text references conferences(id) on delete set null,
  role          text not null check (role in ('user','assistant','system')),
  content       text not null,
  created_at    timestamptz not null default now()
);

create index if not exists chat_messages_user_time_idx
  on chat_messages (user_id, created_at);

-- ============================================================================
-- RLS — backend uses service-role key which bypasses RLS. These policies
-- protect against accidental client-side reads via the anon key.
-- ============================================================================

alter table conferences            enable row level security;
alter table conference_days        enable row level security;
alter table events                 enable row level security;
alter table conference_suggestions enable row level security;
alter table anonymous_curations    enable row level security;
alter table user_curations         enable row level security;
alter table user_event_pins        enable row level security;
alter table user_entitlements      enable row level security;
alter table chat_messages          enable row level security;

-- Public-read catalog
create policy "public read conferences"            on conferences            for select using (true);
create policy "public read conference_days"        on conference_days        for select using (true);
create policy "public read events"                 on events                 for select using (true);
create policy "public read conference_suggestions" on conference_suggestions for select using (true);

-- Anonymous curations: no client access — only service role writes/reads
-- (no policy = no access except service role)

-- User-scoped
create policy "own user_curations"    on user_curations    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own user_event_pins"   on user_event_pins   for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own user_entitlements" on user_entitlements for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own chat_messages"     on chat_messages     for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ============================================================================
-- Helpers
-- ============================================================================

create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger events_set_updated_at
  before update on events
  for each row execute function set_updated_at();
