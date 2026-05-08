import { useQuery } from '@tanstack/react-query'

import { getEvents } from '../api/events'
import { SEED_EVENTS, type SeedEvent } from '../data/seedEvents'

/**
 * Returns the live events from /api/events, keyed by conference. Falls back to the offline
 * fixture if the API is unreachable or hasn't been populated yet.
 */
export function useEvents(conferenceId?: string) {
  const q = useQuery({
    queryKey: ['events', conferenceId ?? 'all'],
    queryFn: () => getEvents(conferenceId),
  })

  // Map the API EventDTO to the legacy SeedEvent shape used by the UI components.
  const live: SeedEvent[] | null = q.data?.events.length
    ? q.data.events.map((e) => ({
        id: e.id,
        title: e.title,
        day: new Date(e.start).getUTCDate(),
        start: new Date(e.start).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        end: new Date(e.end).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        venue: e.venue ?? '',
        tag: e.tags[0] ?? 'Event',
        attendees: e.attendees ?? 0,
        match: e.match ?? 80,
        inSchedule: e.inSchedule ?? false,
        desc: e.description ?? '',
      }))
    : null

  return { events: live ?? SEED_EVENTS, isFallback: !live, ...q }
}
