import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { supabase, supabaseConfigured } from '../../lib/supabase'

type Mode = 'magic' | 'password'

export default function AuthScreen() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') ?? '/app/chat'

  const [mode, setMode] = useState<Mode>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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

  const signInWithPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('sending')
    setError(null)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      setStatus('error')
      setError(error.message)
      return
    }
    // Session is set; AuthGate / AdminGate will route us based on `next`.
    navigate(next, { replace: true })
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
      <form
        className="auth-card"
        onSubmit={mode === 'magic' ? sendMagicLink : signInWithPassword}
      >
        <h1>Sign in to SideQuest</h1>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === 'password' ? 'is-active' : ''}`}
            onClick={() => {
              setMode('password')
              setStatus('idle')
              setError(null)
            }}
          >
            Password
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'magic' ? 'is-active' : ''}`}
            onClick={() => {
              setMode('magic')
              setStatus('idle')
              setError(null)
            }}
          >
            Magic link
          </button>
        </div>

        <p>
          {mode === 'magic'
            ? "We'll email you a one-time link."
            : 'Sign in with your email and password.'}
        </p>

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

        {mode === 'password' && (
          <>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </>
        )}

        <button
          type="submit"
          className="btn-primary"
          disabled={status === 'sending' || !email || (mode === 'password' && !password)}
        >
          {status === 'sending'
            ? mode === 'magic'
              ? 'Sending…'
              : 'Signing in…'
            : mode === 'magic'
              ? 'Email me a sign-in link'
              : 'Sign in'}
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
