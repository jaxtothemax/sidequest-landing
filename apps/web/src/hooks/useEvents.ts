import { useQuery } from '@tanstack/react-query'

import { getEvents } from '../api/events'
import { SEED_EVENTS, type SeedEvent } from '../data/seedEvents'
import { useOnboarding } from '../stores/onboardingStore'

/**
 * Returns the live events for a conference. Falls back to the offline
 * fixture if the API is unreachable.
 *
 * If no conferenceId is passed, uses the active conference from the
 * onboarding store (defaults to 'token2049').
 */
export function useEvents(conferenceIdArg?: string) {
  const activeConferenceId = useOnboarding((s) => s.state.conferenceId)
  const conferenceId = conferenceIdArg ?? activeConferenceId ?? 'token2049'

  const q = useQuery({
    queryKey: ['events', conferenceId],
    queryFn: () => getEvents(conferenceId),
  })

  // Map the API Event to the legacy SeedEvent shape used by EventCard etc.
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

  return { events: live ?? SEED_EVENTS, isFallback: !live, conferenceId, ...q }
}
