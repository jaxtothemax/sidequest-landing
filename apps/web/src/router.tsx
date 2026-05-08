import { lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AuthGate } from './features/auth/AuthGate'

const AuthScreen = lazy(() => import('./features/auth/AuthScreen'))
const AuthCallback = lazy(() => import('./features/auth/AuthCallback'))
const Onboarding = lazy(() => import('./features/onboarding/Onboarding'))
const Paywall = lazy(() => import('./features/onboarding/Paywall'))
const MainApp = lazy(() => import('./features/mainapp/MainApp'))

export function Router() {
  return (
    <Routes>
      <Route path="/" element={<Onboarding />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/paywall" element={<Paywall />} />
      <Route path="/auth" element={<AuthScreen />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route
        path="/app/*"
        element={
          <AuthGate>
            <MainApp />
          </AuthGate>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
