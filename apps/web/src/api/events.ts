import { apiFetch } from '../lib/fetcher'
import type { Event } from '../types'

/** Conference detail returned by the backend. We keep just the fields the UI needs. */
export type ConferenceSummary = {
  id: string
  name: string
  city: string | null
}

export type EventsResponse = {
  events: Event[]
  conference: ConferenceSummary | null
}

type ApiConference = {
  id: string
  name: string
  city: string | null
  venue: string | null
  start_date: string | null
  end_date: string | null
  timezone: string | null
  meta: Record<string, unknown>
  days: { num: number; dow: string; date: string | null; enabled: boolean }[]
}

export async function getEvents(conferenceId: string): Promise<EventsResponse> {
  const [conf, events] = await Promise.all([
    apiFetch<ApiConference>(`/api/conferences/${encodeURIComponent(conferenceId)}`),
    apiFetch<Event[]>(`/api/conferences/${encodeURIComponent(conferenceId)}/events`),
  ])
  return {
    events,
    conference: {
      id: conf.id,
      name: conf.name,
      city: conf.city,
    },
  }
}

export function pinEvent(eventId: string, pinned: boolean) {
  return apiFetch<{ ok: true; event_id: string; pinned: boolean }>(`/api/events/pin`, {
    method: 'POST',
    body: JSON.stringify({ event_id: eventId, pinned }),
  })
}

export function getMyEvents() {
  return apiFetch<Event[]>(`/api/me/events`)
}
