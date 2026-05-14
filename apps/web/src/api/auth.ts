import { apiFetch } from '../lib/fetcher'

export type ClaimResponse = { ok: true; user_curation_id: string }
export type UnlockResponse = { ok: true; unlocked: boolean }

export function claimAnonymousCuration(anonId: string): Promise<ClaimResponse> {
  return apiFetch<ClaimResponse>('/api/auth/claim', {
    method: 'POST',
    body: JSON.stringify({ anon_id: anonId }),
  })
}

export function unlockEntitlement(): Promise<UnlockResponse> {
  return apiFetch<UnlockResponse>('/api/unlock', {
    method: 'POST',
  })
}
