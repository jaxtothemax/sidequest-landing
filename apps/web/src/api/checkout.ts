import { getAnonId } from '../lib/anonId'
import { apiFetch } from '../lib/fetcher'

export type CheckoutResponse = { checkout_url: string }

export function createCheckout(conferenceId: string): Promise<CheckoutResponse> {
  return apiFetch<CheckoutResponse>('/api/checkout', {
    method: 'POST',
    body: JSON.stringify({
      anon_id: getAnonId(),
      conference_id: conferenceId,
    }),
  })
}
