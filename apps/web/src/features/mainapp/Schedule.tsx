import { useMemo, useState } from 'react'
import { Filter, Search } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { EventCard } from '../../components/EventCard'
import { pinEvent } from '../../api/events'
import { useEvents } from '../../hooks/useEvents'
import type { SeedEvent } from '../../data/seedEvents'

export function SchedulePage() {
  const { events: data, isFallback } = useEvents()
  const queryClient = useQueryClient()
  const [events, setEvents] = useState<SeedEvent[]>(data)

  // Reseed local state when the upstream data changes.
  if (events !== data && data.length && events.length === 0) {
    setEvents(data)
  }

  const [view, setView] = useState<'mine' | 'all'>('mine')
  const [day, setDay] = useState<number | 'all'>('all')
  const [tag, setTag] = useState<string>('all')
  const [query, setQuery] = useState('')

  const tags = useMemo(() => Array.from(new Set(events.map((e) => e.tag))), [events])
  const days = useMemo(() => Array.from(new Set(events.map((e) => e.day))).sort(), [events])

  const mut = useMutation({
    mutationFn: ({ id, pinned }: { id: string; pinned: boolean }) => pinEvent(id, pinned),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['events'] }),
  })

  const toggle = (id: string) => {
    setEvents((es) =>
      es.map((e) => (e.id === id ? { ...e, inSchedule: !e.inSchedule } : e)),
    )
    if (!isFallback) {
      const target = events.find((e) => e.id === id)
      mut.mutate({ id, pinned: !(target?.inSchedule ?? false) })
    }
  }

  const filtered = useMemo(
    () =>
      events.filter((e) => {
        if (view === 'mine' && !e.inSchedule) return false
        if (day !== 'all' && e.day !== day) return false
        if (tag !== 'all' && e.tag !== tag) return false
        if (query && !e.title.toLowerCase().includes(query.toLowerCase())) return false
        return true
      }),
    [events, view, day, tag, query],
  )

  const grouped = useMemo(() => {
    const map: Record<number, SeedEvent[]> = {}
    filtered.forEach((e) => {
      map[e.day] = map[e.day] || []
      map[e.day].push(e)
    })
    Object.values(map).forEach((arr) => arr.sort((a, b) => a.start.localeCompare(b.start)))
    return map
  }, [filtered])

  const mineCount = events.filter((e) => e.inSchedule).length

  return (
    <div className="sched">
      <div className="sched__header">
        <div>
          <h1 className="sched__title">Your Schedule</h1>
          <div className="sched__sub">
            {mineCount} events · TOKEN2049 Dubai · 29–30 Apr
          </div>
        </div>
      </div>

      <div className="sched__tabs">
        <button
          className={`sched__tab ${view === 'mine' ? 'is-active' : ''}`}
          onClick={() => setView('mine')}
        >
          My plan
        </button>
        <button
          className={`sched__tab ${view === 'all' ? 'is-active' : ''}`}
          onClick={() => setView('all')}
        >
          All events
        </button>
      </div>

      <div className="sched__filters">
        <div className="sched__search">
          <Search size={16} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search events"
          />
        </div>
        <div className="sched__chips">
          <button
            className={`f-chip ${day === 'all' ? 'is-active' : ''}`}
            onClick={() => setDay('all')}
          >
            All days
          </button>
          {days.map((d) => (
            <button
              key={d}
              className={`f-chip ${day === d ? 'is-active' : ''}`}
              onClick={() => setDay(d)}
            >
              {d === 29 ? 'Wed 29' : d === 30 ? 'Thu 30' : `Day ${d}`}
            </button>
          ))}
          <div className="sched__chips-divider" />
          <button
            className={`f-chip ${tag === 'all' ? 'is-active' : ''}`}
            onClick={() => setTag('all')}
          >
            <Filter size={12} /> All
          </button>
          {tags.map((t) => (
            <button
              key={t}
              className={`f-chip ${tag === t ? 'is-active' : ''}`}
              onClick={() => setTag(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="sched__list">
        {Object.keys(grouped).length === 0 && (
          <div className="sched__empty">No events match these filters.</div>
        )}
        {Object.keys(grouped)
          .map((d) => Number(d))
          .sort((a, b) => a - b)
          .map((d) => (
            <section key={d} className="sched__day">
              <h3 className="sched__day-title">
                {d === 29 ? 'Wednesday, April 29' : d === 30 ? 'Thursday, April 30' : `Day ${d}`}
              </h3>
              {grouped[d].map((e) => (
                <EventCard key={e.id} event={e} onToggle={() => toggle(e.id)} />
              ))}
            </section>
          ))}
      </div>
    </div>
  )
}
