import { useQuery } from '@tanstack/react-query'

import { getMySchedule, type ScheduleItem } from '../api/me'
import { useAuthSession } from '../stores/authStore'

/**
 * Fetches the signed-in user's pin-merged schedule from /api/me/schedule.
 *
 * Returns null `schedule` until the session is available (avoids 401 spam).
 * 404 (user hasn't curated yet) is also normal — surfaced as null schedule.
 */
export function useMySchedule(conferenceId?: string) {
  const { session } = useAuthSession()

  const q = useQuery({
    queryKey: ['me', 'schedule', conferenceId ?? 'active'],
    queryFn: () => getMySchedule(conferenceId),
    enabled: Boolean(session),
    retry: false,
  })

  const schedule: ScheduleItem[] | null = q.data?.schedule ?? null
  const scheduledIds = new Set((schedule ?? []).map((s) => s.id))

  return {
    schedule,
    scheduledIds,
    conferenceId: q.data?.conference_id ?? null,
    isReady: q.isFetched && !q.isError,
    error: q.error,
  }
}
