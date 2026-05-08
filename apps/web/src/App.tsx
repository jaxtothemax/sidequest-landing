import { Suspense } from 'react'

import { Router } from './router'
import { NewVersionPrompt } from './pwa/NewVersionPrompt'
import { OfflineBanner } from './pwa/OfflineBanner'

export function App() {
  return (
    <>
      <Suspense fallback={<div className="boot-spinner" />}>
        <Router />
      </Suspense>
      <NewVersionPrompt />
      <OfflineBanner />
    </>
  )
}
