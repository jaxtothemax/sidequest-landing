import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { supabaseConfigured } from '../../lib/supabase'
import { useAuthSession } from '../../stores/authStore'

export function AuthGate({ children }: { children: ReactNode }) {
  const { session, loading } = useAuthSession()
  const location = useLocation()

  if (!supabaseConfigured) {
    // Dev mode without Supabase env vars — let the user through so the UI is testable.
    return <>{children}</>
  }
  if (loading) return <div className="boot-spinner" />
  if (!session) {
    const redirectTo = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/auth?next=${redirectTo}`} replace />
  }
  return <>{children}</>
}
