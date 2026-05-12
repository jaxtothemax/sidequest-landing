import { apiFetch } from '../lib/fetcher'

export type AdminEvent = {
  id: string
  conference_id: string
  title: string
  description: string | null
  starts_at: string
  ends_at: string
  venue: string | null
  tags: string[]
  url: string | null
  capacity: number | null
  attendees: number | null
  is_manual: boolean
  locked: boolean
  updated_by: string | null
  updated_at: string | null
  created_at: string | null
}

export type AdminEventCreate = {
  id: string
  conference_id: string
  title: string
  description?: string | null
  starts_at: string
  ends_at: string
  venue?: string | null
  tags?: string[]
  url?: string | null
  capacity?: number | null
  attendees?: number | null
}

export type AdminEventUpdate = Partial<Omit<AdminEventCreate, 'id'>>

export type AdminConferenceDay = {
  day_num: number
  dow: string
  date?: string | null
  enabled: boolean
}

export type AdminConferenceUpsert = {
  id: string
  name: string
  city?: string | null
  venue?: string | null
  start_date?: string | null
  end_date?: string | null
  timezone?: string | null
  meta?: Record<string, unknown>
  days?: AdminConferenceDay[]
}

export type ConferenceFromApi = {
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

export function listConferences(): Promise<ConferenceFromApi[]> {
  return apiFetch<ConferenceFromApi[]>('/api/conferences')
}

export function getConference(id: string): Promise<ConferenceFromApi> {
  return apiFetch<ConferenceFromApi>(`/api/conferences/${encodeURIComponent(id)}`)
}

// ---------- events ----------

export function listAdminEvents(params: {
  conference_id?: string
  locked?: boolean
  is_manual?: boolean
}): Promise<AdminEvent[]> {
  const qs = new URLSearchParams()
  if (params.conference_id) qs.set('conference_id', params.conference_id)
  if (params.locked !== undefined) qs.set('locked', String(params.locked))
  if (params.is_manual !== undefined) qs.set('is_manual', String(params.is_manual))
  const suffix = qs.toString() ? `?${qs}` : ''
  return apiFetch<AdminEvent[]>(`/api/admin/events${suffix}`)
}

export function createAdminEvent(body: AdminEventCreate): Promise<AdminEvent> {
  return apiFetch<AdminEvent>('/api/admin/events', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function updateAdminEvent(id: string, patch: AdminEventUpdate): Promise<AdminEvent> {
  return apiFetch<AdminEvent>(`/api/admin/events/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

export function deleteAdminEvent(id: string): Promise<void> {
  return apiFetch<void>(`/api/admin/events/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
}

export function setAdminEventLock(id: string, locked: boolean): Promise<AdminEvent> {
  return apiFetch<AdminEvent>(`/api/admin/events/${encodeURIComponent(id)}/lock`, {
    method: 'POST',
    body: JSON.stringify({ locked }),
  })
}

// ---------- conferences ----------

export function upsertAdminConference(body: AdminConferenceUpsert) {
  return apiFetch<Record<string, unknown>>('/api/admin/conferences', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
