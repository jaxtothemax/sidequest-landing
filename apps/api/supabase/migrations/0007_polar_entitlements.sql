-- Polar.sh payments — per-conference entitlements + anonymous mirror.
--
-- Rationale: payment happens BEFORE signup in the SideQuest flow, so the anon_id
-- carries the entitlement until the user claims it via /api/auth/claim. This
-- mirrors the anonymous_curations → user_curations pattern from 0001.

-- ============================================================================
-- anonymous_entitlements (anon_id is the secret, mirrors anonymous_curations)
-- ============================================================================

create table if not exists anonymous_entitlements (
  anon_id       uuid        not null,
  conference_id text        not null references conferences(id) on delete cascade,
  unlocked      boolean     not null default false,
  unlocked_at   timestamptz,
  provider      text,                              -- 'polar' | 'stub'
  provider_ref  text,                              -- Polar order_id
  expires_at    timestamptz,                       -- null = no expiry (one-time unlock)
  created_at    timestamptz not null default now(),
  claimed_by    uuid,                              -- auth.users(id) once claimed
  claimed_at    timestamptz,
  primary key (anon_id, conference_id)
);

create index if not exists anonymous_entitlements_unclaimed_idx
  on anonymous_entitlements (created_at) where claimed_by is null;

alter table anonymous_entitlements enable row level security;
-- no policies = service-role only access, same trust model as anonymous_curations

-- ============================================================================
-- user_entitlements — extend to per-conference
-- ============================================================================
-- Note: no FK on conference_id here — the canonical FK lives on
-- anonymous_entitlements (the only write path from Polar). Keeping
-- conference_id as plain text on user_entitlements avoids referential
-- problems when claiming entitlements for conferences that may later be
-- deleted, and dodges the "default value doesn't reference a row" pitfall
-- if this table happens to have stub data left from the pre-Polar `/api/unlock`.

-- Drop old singleton policy + PK
drop policy if exists "own user_entitlements" on user_entitlements;
alter table user_entitlements drop constraint if exists user_entitlements_pkey;

-- Add the new columns nullable first, backfill, then enforce NOT NULL.
alter table user_entitlements add column if not exists conference_id  text;
alter table user_entitlements add column if not exists source_anon_id uuid;

-- Backfill any pre-Polar stub rows so we can flip the NOT NULL constraint.
-- These rows are meaningless (the stub always-unlocked) but we keep them to
-- avoid surprising any user whose row already exists.
update user_entitlements set conference_id = '' where conference_id is null;
alter table user_entitlements alter column conference_id set not null;

alter table user_entitlements add primary key (user_id, conference_id);

-- Re-create RLS policy with the same semantics as before.
create policy "own user_entitlements"
  on user_entitlements for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
