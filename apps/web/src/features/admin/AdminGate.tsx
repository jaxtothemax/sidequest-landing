import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { supabaseConfigured } from '../../lib/supabase'
import { useAuthSession } from '../../stores/authStore'

/**
 * Guards /admin routes. Requires a Supabase session AND app_metadata.role === 'admin'.
 * Server-side enforcement is still on the FastAPI endpoints — this just stops
 * a non-admin from staring at an empty page that 403s on every request.
 *
 * Promote a user via apps/api/scripts/set_admin.sql or
 * `scripts/mint_test_jwt.py --admin --email you@example.com`.
 */
export function AdminGate({ children }: { children: ReactNode }) {
  const { session, loading } = useAuthSession()
  const location = useLocation()

  if (!supabaseConfigured) return <>{children}</>
  if (loading) return <div className="boot-spinner" />

  if (!session) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/auth?next=${next}`} replace />
  }

  const role = (session.user?.app_metadata as Record<string, unknown> | undefined)?.role
  if (role !== 'admin') {
    return (
      <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
        <h2>Admin access required</h2>
        <p style={{ marginTop: '1rem', opacity: 0.7 }}>
          You're signed in as <code>{session.user?.email}</code>, but this account doesn't have the
          admin role.
        </p>
        <p style={{ marginTop: '1rem', opacity: 0.6, fontSize: 14 }}>
          Promote a user via <code>apps/api/scripts/set_admin.sql</code>.
        </p>
      </div>
    )
  }

  return <>{children}</>
}
