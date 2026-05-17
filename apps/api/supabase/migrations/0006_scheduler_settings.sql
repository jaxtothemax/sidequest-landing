-- Global scheduler on/off, controlled from the admin UI.
--
-- Singleton row so we can never get into a state where two settings rows
-- disagree. The scheduler reads this on every tick; flipping it via the
-- admin endpoint takes effect on the next tick (≤ tick_seconds latency).

create table if not exists scheduler_settings (
  id          text primary key default 'singleton' check (id = 'singleton'),
  enabled     boolean not null default false,
  updated_at  timestamptz not null default now(),
  updated_by  uuid
);

-- Seed the singleton so reads never have to handle the empty case.
insert into scheduler_settings (id, enabled) values ('singleton', false)
  on conflict (id) do nothing;

create trigger scheduler_settings_updated_at
  before update on scheduler_settings
  for each row execute function set_updated_at();

alter table scheduler_settings enable row level security;
