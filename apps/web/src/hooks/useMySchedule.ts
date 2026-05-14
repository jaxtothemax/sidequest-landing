import { useQuery } from '@tanstack/react-query'

import { getMySchedule, type ScheduleItem } from '../api/me'
import { useAuthSession } from '../stores/authStore'

/**
 * Fetches the signed-in user's pin-merged schedule from /api/me/schedule.
 *
 * Returns null `schedule` until the session is available (avoids 401 spam).
 * 404 (user hasn't curated yet) is normal — surfaced as an empty schedule
 * with isReady=true so the UI can still apply pin overrides on top of the
 * catalog instead of staying stuck in the catalog-fallback path forever.
 */
export function useMySchedule(conferenceId?: string) {
  const { session } = useAuthSession()

  const q = useQuery({
    queryKey: ['me', 'schedule', conferenceId ?? 'active'],
    queryFn: () => getMySchedule(conferenceId),
    enabled: Boolean(session),
    retry: false,
  })

  const is404 = /\b404\b/.test((q.error as Error | undefined)?.message ?? '')

  const schedule: ScheduleItem[] | null = q.data?.schedule ?? null
  const scheduledIds = new Set((schedule ?? []).map((s) => s.id))

  return {
    schedule,
    scheduledIds,
    conferenceId: q.data?.conference_id ?? null,
    // Treat 404 (no curation) as ready-with-empty so pin overrides apply.
    isReady: q.isFetched && (!q.isError || is404),
    error: q.error,
  }
}
