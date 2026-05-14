import { useMemo, useRef, useState } from 'react'
import { Check, Loader2, MapPin, Pause, Play, Sparkles, X } from 'lucide-react'

import { useEvents } from '../../hooks/useEvents'
import { useMySchedule } from '../../hooks/useMySchedule'
import type { SeedEvent } from '../../data/seedEvents'

type ApplyStatus = 'idle' | 'queued' | 'applying' | 'applied' | 'failed' | 'skipped'

type Row = SeedEvent & { status: ApplyStatus; note?: string }

// Mock: deterministic-ish failure on a couple events so the UX of partial
// success is visible. Replace with real backend integration later.
function simulateApplyOutcome(ev: SeedEvent): { ok: boolean; note?: string } {
  if (ev.tag === 'Investors' && ev.attendees < 100) {
    return { ok: false, note: 'Invite-only — agent waitlisted you' }
  }
  if (ev.tag === 'Press') {
    return { ok: false, note: 'Press credentials required' }
  }
  return { ok: true, note: 'Confirmation will land in your inbox' }
}

export function ApplyPage() {
  const { events: catalogEvents } = useEvents()
  const { scheduledIds, isReady } = useMySchedule()

  const scheduled: SeedEvent[] = useMemo(() => {
    return catalogEvents.filter((e) =>
      isReady ? scheduledIds.has(e.id) : e.inSchedule,
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogEvents, isReady, Array.from(scheduledIds).sort().join(',')])

  const [rows, setRows] = useState<Record<string, Row>>({})
  const [running, setRunning] = useState(false)
  const cancelRef = useRef(false)

  // Derived view: merge current event list with status map.
  const view: Row[] = scheduled.map((e) => ({
    ...e,
    status: rows[e.id]?.status ?? 'idle',
    note: rows[e.id]?.note,
  }))

  const counts = view.reduce(
    (acc, r) => {
      acc[r.status] = (acc[r.status] ?? 0) + 1
      return acc
    },
    {} as Record<ApplyStatus, number>,
  )
  const applied = counts.applied ?? 0
  const failed = counts.failed ?? 0
  const total = view.length

  const start = async () => {
    if (running || total === 0) return
    cancelRef.current = false
    setRunning(true)
    setRows(() =>
      Object.fromEntries(scheduled.map((e) => [e.id, { ...e, status: 'queued' as const }])),
    )

    for (const ev of scheduled) {
      if (cancelRef.current) break
      setRows((prev) => ({
        ...prev,
        [ev.id]: { ...ev, status: 'applying', note: undefined },
      }))
      // Per-event delay simulates agent doing the work.
      await new Promise((r) => setTimeout(r, 700 + Math.random() * 700))
      if (cancelRef.current) break
      const outcome = simulateApplyOutcome(ev)
      setRows((prev) => ({
        ...prev,
        [ev.id]: {
          ...ev,
          status: outcome.ok ? 'applied' : 'failed',
          note: outcome.note,
        },
      }))
    }

    if (cancelRef.current) {
      setRows((prev) => {
        const next = { ...prev }
        for (const ev of scheduled) {
          if (next[ev.id]?.status === 'queued' || next[ev.id]?.status === 'applying') {
            next[ev.id] = { ...ev, status: 'skipped', note: 'Cancelled' }
          }
        }
        return next
      })
    }

    setRunning(false)
  }

  const stop = () => {
    cancelRef.current = true
  }

  const reset = () => {
    if (running) return
    setRows({})
  }

  return (
    <div className="apl">
      <div className="apl__header">
        <div className="apl__title-wrap">
          <h1 className="apl__title">
            <Sparkles size={18} className="apl__title-icon" />
            AI Apply Agent
          </h1>
          <div className="apl__sub">
            Let the agent register you for every event on your plan.
          </div>
        </div>
      </div>

      <div className="apl__hero">
        <div className="apl__hero-stat">
          <div className="apl__hero-num">{total}</div>
          <div className="apl__hero-label">events on your plan</div>
        </div>
        {total > 0 && (running || applied > 0 || failed > 0) && (
          <div className="apl__progress">
            <div
              className="apl__progress-bar"
              style={{ width: `${Math.round(((applied + failed) / total) * 100)}%` }}
            />
            <div className="apl__progress-meta">
              <span className="apl__pill apl__pill--ok">
                <Check size={11} /> {applied} applied
              </span>
              {failed > 0 && (
                <span className="apl__pill apl__pill--bad">
                  <X size={11} /> {failed} flagged
                </span>
              )}
            </div>
          </div>
        )}
        <div className="apl__actions">
          {!running ? (
            <button
              className="apl__cta"
              disabled={total === 0}
              onClick={() => void start()}
            >
              <Play size={16} />
              {applied + failed > 0 ? 'Run again' : 'Run agent'}
            </button>
          ) : (
            <button className="apl__cta apl__cta--stop" onClick={stop}>
              <Pause size={16} /> Stop
            </button>
          )}
          {!running && (applied + failed > 0) && (
            <button className="apl__secondary" onClick={reset}>
              Reset
            </button>
          )}
        </div>
      </div>

      <div className="apl__list">
        {total === 0 && (
          <div className="apl__empty">
            No events on your plan yet. Pick some from the Schedule tab first.
          </div>
        )}
        {view.map((r) => (
          <article key={r.id} className={`apl-row apl-row--${r.status}`}>
            <div className="apl-row__status">
              <StatusIcon status={r.status} />
            </div>
            <div className="apl-row__body">
              <div className="apl-row__top">
                <span className="apl-row__tag">{r.tag}</span>
                <span className="apl-row__time">
                  Day {r.day} · {r.start}
                </span>
              </div>
              <h4 className="apl-row__title">{r.title}</h4>
              <div className="apl-row__meta">
                <span>
                  <MapPin size={12} /> {r.venue}
                </span>
              </div>
              {r.note && <div className="apl-row__note">{r.note}</div>}
            </div>
            <div className="apl-row__badge">
              <StatusBadge status={r.status} />
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: ApplyStatus }) {
  if (status === 'applying') return <Loader2 size={18} className="apl-spin" />
  if (status === 'applied') return <Check size={18} />
  if (status === 'failed') return <X size={18} />
  if (status === 'queued') return <span className="apl-dot" />
  if (status === 'skipped') return <span className="apl-dot apl-dot--dim" />
  return <span className="apl-dot apl-dot--dim" />
}

function StatusBadge({ status }: { status: ApplyStatus }) {
  const map: Record<ApplyStatus, string> = {
    idle: 'Pending',
    queued: 'Queued',
    applying: 'Applying…',
    applied: 'Applied',
    failed: 'Needs review',
    skipped: 'Skipped',
  }
  return <span className={`apl-badge apl-badge--${status}`}>{map[status]}</span>
}
