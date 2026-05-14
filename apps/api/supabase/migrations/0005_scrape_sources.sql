-- Per-conference scrape sources (Luma URLs to start; extensible to other
-- sources later via source_type).
--
-- The scraper itself is not implemented yet — Slice 3. The /scrape endpoint
-- is currently a stub that records last_scraped_at + a "not implemented"
-- message so the UX can be exercised end-to-end.

create table if not exists conference_scrape_sources (
  id                uuid primary key default gen_random_uuid(),
  conference_id     text not null references conferences(id) on delete cascade,
  source_type       text not null default 'luma' check (source_type in ('luma')),
  url               text not null,
  enabled           boolean not null default true,
  last_scraped_at   timestamptz,
  last_status       text,                              -- 'ok' | 'error' | 'pending' | null
  last_error        text,
  events_added      int not null default 0,
  events_updated    int not null default 0,
  scrape_interval_minutes int,                         -- null = manual-only (default)
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (conference_id, url)
);

create index if not exists conference_scrape_sources_conf_idx
  on conference_scrape_sources (conference_id);

create index if not exists conference_scrape_sources_due_idx
  on conference_scrape_sources (last_scraped_at) where enabled = true and scrape_interval_minutes is not null;

create trigger conference_scrape_sources_updated_at
  before update on conference_scrape_sources
  for each row execute function set_updated_at();

-- RLS: backend uses service_role (bypasses), so we just enable RLS without
-- adding any client-facing policies. The admin UI hits the API; the API
-- holds the service-role key.
alter table conference_scrape_sources enable row level security;
