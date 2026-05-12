-- service_role grants.
--
-- When the project's "Automatically expose new tables" Data API setting is OFF
-- (recommended for a backend-mediated architecture like ours), no role gets
-- auto-grants on new tables — including service_role. The backend uses
-- service_role and needs explicit access.
--
-- Idempotent: safe to re-run.
--
-- We deliberately do NOT grant anon/authenticated. The frontend never reads
-- public tables directly; it routes through apps/api, which authenticates as
-- service_role. Auth flows (signup/login) use Supabase Auth directly with the
-- publishable key, which doesn't need table grants.

grant usage on schema public to service_role;

grant all on all tables    in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant all on all functions in schema public to service_role;

-- Default privileges for tables added by later migrations.
alter default privileges in schema public grant all on tables    to service_role;
alter default privileges in schema public grant all on sequences to service_role;
alter default privileges in schema public grant all on functions to service_role;
