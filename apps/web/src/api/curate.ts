import { apiFetch } from '../lib/fetcher'
import type { CuratedItem, OnboardingState } from '../types'

export type CurateResponse = { schedule: CuratedItem[]; tokens_used: number }

export function curate(state: OnboardingState, model?: string): Promise<CurateResponse> {
  return apiFetch<CurateResponse>('/api/curate', {
    method: 'POST',
    body: JSON.stringify({ onboarding: state, model }),
  })
}
