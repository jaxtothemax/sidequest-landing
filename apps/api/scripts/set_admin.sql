-- Promote a Supabase user to admin.
-- Run in Supabase SQL Editor (or psql). Replace the email.
--
-- The backend reads `app_metadata.role` from the verified JWT (see
-- app/deps.py::require_admin). Users get a fresh JWT next time they
-- sign in / refresh — existing tokens won't carry the new claim until
-- then.
--
-- For local automated tests, use `scripts/mint_test_jwt.py --admin`
-- which calls the Admin API equivalent.

update auth.users
   set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
                        || '{"role":"admin"}'::jsonb
 where email = 'YOU@EXAMPLE.COM'
returning id, email, raw_app_meta_data;
