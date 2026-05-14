import { useMemo } from 'react'
import { CheckCircle2, Download, Sparkles, UserPlus, Wrench } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { EventCard } from '../../components/EventCard'
import type { SeedEvent } from '../../data/seedEvents'
import { useEvents } from '../../hooks/useEvents'
import { useOnboarding } from '../../stores/onboardingStore'

export default function PaywallThanks() {
  const navigate = useNavigate()
  const { events } = useEvents()
  const curatedSchedule = useOnboarding((s) => s.curatedSchedule)

  // Show the user's actual curated schedule, fully unblurred. Falls back to
  // a small preview from the catalog if there's no curation in the store yet.
  const scheduled: SeedEvent[] = useMemo(() => {
    const sortByStart = (a: SeedEvent, b: SeedEvent) =>
      a.day - b.day || a.start.localeCompare(b.start)
    const ids = new Set((curatedSchedule ?? []).map((c) => c.event_id))
    if (ids.size) {
      return events.filter((e) => ids.has(e.id)).sort(sortByStart)
    }
    return events.slice().sort(sortByStart)
  }, [events, curatedSchedule])

  const grouped = useMemo(() => {
    const map = new Map<number, SeedEvent[]>()
    for (const e of scheduled) {
      const arr = map.get(e.day) ?? []
      arr.push(e)
      map.set(e.day, arr)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a - b)
  }, [scheduled])

  const dayLabel = (firstStart: string, day: number) => {
    const d = new Date(firstStart)
    if (Number.isNaN(d.getTime())) return `Day ${day}`
    return d.toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    })
  }

  const onCreateAccount = () =>
    navigate('/auth?next=' + encodeURIComponent('/app/schedule'))

  const onDownload = () => {
    // Placeholder. Wire to real export (PDF / .ics) when payment is real.
    alert(
      'TODO: Download is not implemented yet. Once payment is live, this will export your schedule as PDF and .ics calendar.',
    )
  }

  return (
    <div className="sq-app">
      <div className="sq-frame">
        <div className="thanks">
          <header className="thanks__header">
            <div className="thanks__check">
              <CheckCircle2 size={28} />
            </div>
            <h1 className="thanks__title">Thank you for your purchase</h1>
            <p className="thanks__sub">
              You can see your full curated schedule below and download it. Create an
              account to save it across devices and unlock the AI agent.
            </p>
          </header>

          <div className="thanks__todo">
            <div className="thanks__todo-icon">
              <Wrench size={16} />
            </div>
            <div>
              <strong>TODO — payment not implemented yet.</strong>{' '}
              This page is a placeholder. Wire up Stripe / Apple Pay so the "Buy"
              button actually charges before letting users land here. The
              <code> /api/unlock</code> backend endpoint is also a stub today.
            </div>
          </div>

          <div className="thanks__actions">
            <button
              type="button"
              className="thanks__cta"
              onClick={onCreateAccount}
            >
              <UserPlus size={16} />
              Create your account
            </button>
            <button
              type="button"
              className="thanks__cta thanks__cta--secondary"
              onClick={onDownload}
            >
              <Download size={16} />
              Download schedule
            </button>
          </div>

          <section className="thanks__schedule">
            <div className="thanks__schedule-head">
              <Sparkles size={14} />
              <span>Your curated schedule</span>
            </div>
            {grouped.length === 0 && (
              <div className="thanks__empty">
                No schedule yet — go back and finish the quiz to generate one.
              </div>
            )}
            {grouped.map(([day, items]) => (
              <div key={day} className="thanks__day-group">
                <div className="thanks__day-label">
                  {dayLabel(items[0].start, day)} · {items.length} event
                  {items.length === 1 ? '' : 's'}
                </div>
                <div className="thanks__events">
                  {items.map((e) => (
                    <EventCard key={e.id} event={e} />
                  ))}
                </div>
              </div>
            ))}
          </section>
        </div>
      </div>
    </div>
  )
}
