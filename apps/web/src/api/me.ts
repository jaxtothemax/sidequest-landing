import { apiFetch } from '../lib/fetcher'
import type { Event } from '../types'

/** Backend ScheduleItem — Event fields + rationale/priority/inSchedule overlay. */
export type ScheduleItem = Event & {
  rationale: string
  priority: 'must' | 'should' | 'maybe'
  inSchedule: true
}

export type ScheduleResponse = {
  conference_id: string | null
  schedule: ScheduleItem[]
}

export function getMySchedule(conferenceId?: string): Promise<ScheduleResponse> {
  const qs = conferenceId ? `?conference_id=${encodeURIComponent(conferenceId)}` : ''
  return apiFetch<ScheduleResponse>(`/api/me/schedule${qs}`)
}
