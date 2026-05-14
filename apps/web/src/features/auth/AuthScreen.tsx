import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { supabase, supabaseConfigured } from '../../lib/supabase'

type Mode = 'signin' | 'signup' | 'magic'

export default function AuthScreen() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') ?? '/app/chat'
  const initialMode = (params.get('mode') as Mode | null) ?? 'signin'

  const [mode, setMode] = useState<Mode>(
    initialMode === 'signup' || initialMode === 'magic' ? initialMode : 'signin',
  )
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  const callbackUrl = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`

  const switchMode = (m: Mode) => {
    setMode(m)
    setStatus('idle')
    setError(null)
  }

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
    navigate(next, { replace: true })
  }

  const signUpWithPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('sending')
    setError(null)
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      // emailRedirectTo only matters if email confirmation is enabled in
      // Supabase Auth settings. With confirmation disabled (recommended for
      // testing — see CLAUDE.md / setup notes), the user is signed in on the
      // spot and the redirect is never used.
      options: { emailRedirectTo: callbackUrl },
    })
    if (error) {
      setStatus('error')
      setError(error.message)
      return
    }
    // If email confirmation is OFF in Supabase, signUp returns a session and
    // the user is logged in. If it's ON, session is null and the user must
    // click an email link first.
    if (data.session) {
      navigate(next, { replace: true })
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

  const onSubmit =
    mode === 'magic'
      ? sendMagicLink
      : mode === 'signup'
        ? signUpWithPassword
        : signInWithPassword

  const heading = mode === 'signup' ? 'Create your SideQuest account' : 'Sign in to SideQuest'

  const intro =
    mode === 'magic'
      ? "We'll email you a one-time link."
      : mode === 'signup'
        ? 'Pick an email and password — you can add Google later.'
        : 'Sign in with your email and password.'

  const submitLabel = (() => {
    if (status === 'sending') {
      if (mode === 'magic') return 'Sending…'
      if (mode === 'signup') return 'Creating account…'
      return 'Signing in…'
    }
    if (mode === 'magic') return 'Email me a sign-in link'
    if (mode === 'signup') return 'Create account'
    return 'Sign in'
  })()

  const sentMessage =
    mode === 'signup'
      ? `Account created. Confirm via the email we sent to ${email}, then sign in.`
      : `Check your inbox — link sent to ${email}.`

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>{heading}</h1>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === 'signin' ? 'is-active' : ''}`}
            onClick={() => switchMode('signin')}
          >
            Sign in
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'signup' ? 'is-active' : ''}`}
            onClick={() => switchMode('signup')}
          >
            Sign up
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'magic' ? 'is-active' : ''}`}
            onClick={() => switchMode('magic')}
          >
            Magic link
          </button>
        </div>

        <p>{intro}</p>

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

        {mode !== 'magic' && (
          <>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              minLength={mode === 'signup' ? 6 : undefined}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'signup' ? 'At least 6 characters' : '••••••••'}
            />
          </>
        )}

        <button
          type="submit"
          className="btn-primary"
          disabled={status === 'sending' || !email || (mode !== 'magic' && !password)}
        >
          {submitLabel}
        </button>

        <div className="auth-divider">or</div>

        <button type="button" className="btn-google" onClick={signInGoogle}>
          Continue with Google
        </button>

        {status === 'sent' && <div className="auth-status">{sentMessage}</div>}
        {status === 'error' && error && <div className="auth-status auth-error">{error}</div>}
      </form>
    </div>
  )
}
