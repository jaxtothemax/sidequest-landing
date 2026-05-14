-- Add is_active flag to conferences.
--
-- Active conferences are visible to end users in the public picker.
-- Inactive conferences are admin-only (drafts, archived, etc.) — still
-- editable via /api/admin/conferences but excluded from the public list.
--
-- Default true so existing rows remain visible after the migration.

alter table conferences
  add column if not exists is_active boolean not null default true;

-- Public-read policy already in place from 0001_init.sql; no change needed.

-- Index used by the public catalog endpoint to skip inactive rows quickly.
create index if not exists conferences_active_idx
  on conferences (is_active) where is_active = true;
