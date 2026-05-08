import { apiFetch } from '../lib/fetcher'
import type { Event } from '../types'

export type EventsResponse = {
  events: Event[]
  conference: { id: string; name: string; city: string } | null
}

export function getEvents(conferenceId?: string): Promise<EventsResponse> {
  const qs = conferenceId ? `?conference_id=${encodeURIComponent(conferenceId)}` : ''
  return apiFetch<EventsResponse>(`/api/events${qs}`)
}

export function pinEvent(eventId: string, pinned: boolean) {
  return apiFetch<{ ok: true }>(`/api/events/pin`, {
    method: 'POST',
    body: JSON.stringify({ event_id: eventId, pinned }),
  })
}

export function getMyEvents() {
  return apiFetch<Event[]>(`/api/me/events`)
}
