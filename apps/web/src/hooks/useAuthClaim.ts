import { useEffect, useRef } from 'react'

import { claimAnonymousCuration, unlockEntitlement } from '../api/auth'
import { clearAnonId, peekAnonId } from '../lib/anonId'
import { useAuthSession } from '../stores/authStore'

/**
 * Once per session, if we have an anonymous_curation id from the pre-signup
 * onboarding flow, link it to the now-signed-in user and flip the unlock
 * entitlement.
 *
 * Safe to mount in multiple places — the anon id is cleared on success, so
 * subsequent runs no-op. 404 (no anon row) and 409 (already claimed) are
 * silent — both are expected for users who signed up without curating, or
 * who re-land on an authed page after a prior claim.
 *
 * Errors otherwise are logged but never surfaced to the UI.
 */
export function useAuthClaim() {
  const { session } = useAuthSession()
  const ran = useRef(false)

  useEffect(() => {
    if (!session || ran.current) return
    const anonId = peekAnonId()
    if (!anonId) return
    ran.current = true
    ;(async () => {
      try {
        await claimAnonymousCuration(anonId)
      } catch (e) {
        const msg = (e as Error).message || ''
        if (!/404|409/.test(msg)) {
          // eslint-disable-next-line no-console
          console.warn('claim failed:', e)
        }
      }
      try {
        await unlockEntitlement()
      } catch (e) {
        // eslint-disable-next-line no-console
        console.warn('unlock failed:', e)
      }
      clearAnonId()
    })()
  }, [session])
}
