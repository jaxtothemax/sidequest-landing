import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const anon = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

if (!url || !anon) {
  // Don't crash the bundle — surface a clear error at the auth boundary instead.
  console.warn('[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY missing — auth disabled')
}

export const supabase: SupabaseClient = createClient(url ?? 'http://localhost:0', anon ?? 'noop', {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
})

export const supabaseConfigured = Boolean(url && anon)
