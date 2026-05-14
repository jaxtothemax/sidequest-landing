import { useQuery } from '@tanstack/react-query'

import { listConferences, type ConferenceFromApi } from '../api/admin'
import { CONFERENCES, type Conference } from '../data/conferences'

/**
 * Returns the active conference list for the public picker.
 *
 * Hits GET /api/conferences (active-only on the server). Falls back to the
 * static CONFERENCES list if the API is unreachable or empty so onboarding
 * never deadends. The API shape is mapped into the legacy `Conference` shape
 * the picker expects.
 */
export function useConferences() {
  const q = useQuery({
    queryKey: ['public', 'conferences'],
    queryFn: listConferences,
    retry: 1,
    staleTime: 60_000,
  })

  const live = (q.data ?? []).map(toLegacyShape)
  const conferences: Conference[] = live.length ? live : CONFERENCES
  return { conferences, isFallback: live.length === 0, ...q }
}

function toLegacyShape(c: ConferenceFromApi): Conference {
  const meta = c.meta ?? {}
  return {
    id: c.id,
    name: c.name,
    meta: (meta.meta_short as string | undefined) ?? '',
    gradient:
      (meta.gradient as string | undefined) ??
      'linear-gradient(135deg, #6088F7, #1E4EB0)',
    days: c.days.map((d) => ({ dow: d.dow, num: d.num, enabled: d.enabled })),
    month: (meta.month as string | undefined) ?? '',
  }
}
