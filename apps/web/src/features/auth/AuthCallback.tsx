import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { supabase } from '../../lib/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/app/chat'

  useEffect(() => {
    // supabase-js v2 handles the URL hash via detectSessionInUrl, but double-check.
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) navigate(next, { replace: true })
      else navigate('/auth', { replace: true })
    })
  }, [navigate, next])

  return <div className="boot-spinner" />
}
