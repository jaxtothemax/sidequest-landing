import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { supabase, supabaseConfigured } from '../../lib/supabase'

export default function AuthScreen() {
  const [params] = useSearchParams()
  const next = params.get('next') ?? '/app/chat'
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  const callbackUrl = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`

  const sendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('sending')
    setError(null)
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: callbackUrl },
    })
    if (error) {
      setStatus('error')
      setError(error.message)
      return
    }
    setStatus('sent')
  }

  const signInGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: callbackUrl },
    })
    if (error) {
      setStatus('error')
      setError(error.message)
    }
  }

  if (!supabaseConfigured) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1>Auth disabled</h1>
          <p>
            Set <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> in your{' '}
            <code>.env</code> to enable sign-in.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={sendMagicLink}>
        <h1>Sign in to SideQuest</h1>
        <p>We'll email you a one-time link.</p>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />

        <button type="submit" className="btn-primary" disabled={status === 'sending' || !email}>
          {status === 'sending' ? 'Sending…' : 'Email me a sign-in link'}
        </button>

        <div className="auth-divider">or</div>

        <button type="button" className="btn-google" onClick={signInGoogle}>
          Continue with Google
        </button>

        {status === 'sent' && (
          <div className="auth-status">Check your inbox — link sent to {email}.</div>
        )}
        {status === 'error' && error && <div className="auth-status auth-error">{error}</div>}
      </form>
    </div>
  )
}
