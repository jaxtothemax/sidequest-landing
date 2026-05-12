import { getAnonId } from '../lib/anonId'
import { apiFetch } from '../lib/fetcher'
import type { CuratedItem, OnboardingState } from '../types'

export type CurateResponse = {
  curate_id: string
  schedule: CuratedItem[]
  tokens_used: number
}

export function curate(state: OnboardingState, model?: string): Promise<CurateResponse> {
  return apiFetch<CurateResponse>('/api/curate', {
    method: 'POST',
    body: JSON.stringify({
      anon_id: getAnonId(),
      onboarding: state,
      model,
    }),
  })
}
