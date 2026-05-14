import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  listConferences,
  upsertAdminConference,
  type AdminConferenceDay,
  type ConferenceFromApi,
} from '../../api/admin'

function jsonStringify(meta: Record<string, unknown>): string {
  try {
    return JSON.stringify(meta, null, 2)
  } catch {
    return '{}'
  }
}

export function AdminConferencesPanel() {
  const queryClient = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'conferences'],
    queryFn: listConferences,
  })

  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Auto-select first conference once data lands.
  useEffect(() => {
    if (!selectedId && q.data && q.data.length) {
      setSelectedId(q.data[0].id)
    }
  }, [q.data, selectedId])

  const selected = useMemo(
    () => q.data?.find((c) => c.id === selectedId) ?? null,
    [q.data, selectedId],
  )

  return (
    <div className="admin__panel admin__panel--two-col">
      <aside className="admin__sidebar">
        <div className="admin__sidebar-head">Conferences</div>
        {q.isLoading && <div className="admin__count">Loading…</div>}
        {q.data?.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`admin__side-item ${c.id === selectedId ? 'is-active' : ''}`}
            onClick={() => setSelectedId(c.id)}
          >
            <div className="admin__side-name">{c.name}</div>
            <div className="admin__side-meta">{c.id}</div>
          </button>
        ))}
      </aside>

      <section className="admin__detail admin-edit-surface">
        {selected ? (
          <ConferenceEditor
            conference={selected}
            onSaved={() => queryClient.invalidateQueries({ queryKey: ['admin', 'conferences'] })}
          />
        ) : (
          <div className="admin__empty">Select a conference to edit.</div>
        )}
      </section>
    </div>
  )
}

function ConferenceEditor(props: {
  conference: ConferenceFromApi
  onSaved: () => void
}) {
  const c = props.conference

  const [name, setName] = useState(c.name)
  const [city, setCity] = useState(c.city ?? '')
  const [venue, setVenue] = useState(c.venue ?? '')
  const [startDate, setStartDate] = useState(c.start_date ?? '')
  const [endDate, setEndDate] = useState(c.end_date ?? '')
  const [timezone, setTimezone] = useState(c.timezone ?? '')
  const [metaText, setMetaText] = useState(jsonStringify(c.meta))
  const [metaError, setMetaError] = useState<string | null>(null)
  const [days, setDays] = useState<AdminConferenceDay[]>(
    c.days.map((d) => ({
      day_num: d.num,
      dow: d.dow,
      date: d.date,
      enabled: d.enabled,
    })),
  )
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    // When the selected conference changes, reset all form fields.
    setName(c.name)
    setCity(c.city ?? '')
    setVenue(c.venue ?? '')
    setStartDate(c.start_date ?? '')
    setEndDate(c.end_date ?? '')
    setTimezone(c.timezone ?? '')
    setMetaText(jsonStringify(c.meta))
    setMetaError(null)
    setDays(
      c.days.map((d) => ({
        day_num: d.num,
        dow: d.dow,
        date: d.date,
        enabled: d.enabled,
      })),
    )
    setSaveError(null)
  }, [c.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const mut = useMutation({
    mutationFn: (body: Parameters<typeof upsertAdminConference>[0]) =>
      upsertAdminConference(body),
    onSuccess: () => {
      setSaveError(null)
      props.onSaved()
    },
    onError: (e: Error) => setSaveError(e.message),
  })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    let parsedMeta: Record<string, unknown> = {}
    try {
      parsedMeta = metaText.trim() ? JSON.parse(metaText) : {}
      setMetaError(null)
    } catch (err) {
      setMetaError(`Invalid JSON: ${(err as Error).message}`)
      return
    }
    mut.mutate({
      id: c.id,
      name: name.trim(),
      city: city.trim() || null,
      venue: venue.trim() || null,
      start_date: startDate || null,
      end_date: endDate || null,
      timezone: timezone.trim() || null,
      meta: parsedMeta,
      days,
    })
  }

  const toggleDay = (day_num: number) => {
    setDays((arr) =>
      arr.map((d) => (d.day_num === day_num ? { ...d, enabled: !d.enabled } : d)),
    )
  }

  return (
    <form className="admin__form" onSubmit={submit}>
      <div className="admin-drawer__row">
        <label className="admin__field">
          <span>Id (immutable)</span>
          <input value={c.id} readOnly disabled />
        </label>
        <label className="admin__field">
          <span>Name</span>
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>
      </div>

      <div className="admin-drawer__row">
        <label className="admin__field">
          <span>City</span>
          <input value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label className="admin__field">
          <span>Venue</span>
          <input value={venue} onChange={(e) => setVenue(e.target.value)} />
        </label>
      </div>

      <div className="admin-drawer__row">
        <label className="admin__field">
          <span>Start date</span>
          <input
            type="date"
            value={startDate ?? ''}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>
        <label className="admin__field">
          <span>End date</span>
          <input
            type="date"
            value={endDate ?? ''}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>
      </div>

      <label className="admin__field">
        <span>Timezone (IANA)</span>
        <input
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          placeholder="Asia/Dubai"
        />
      </label>

      <label className="admin__field">
        <span>Meta (JSON — gradient, meta_short, month)</span>
        <textarea
          rows={6}
          value={metaText}
          onChange={(e) => setMetaText(e.target.value)}
          spellCheck={false}
          style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: 12 }}
        />
        {metaError && <span className="admin__error">{metaError}</span>}
      </label>

      <div className="admin__days">
        <div className="admin__days-head">
          Days
          <span className="admin__days-hint">Toggle which days are open for attendance</span>
        </div>
        <div className="admin__days-grid">
          {days.length === 0 && (
            <span className="admin__days-empty">
              No day rows yet — add them directly in the Supabase SQL editor for now.
            </span>
          )}
          {days.map((d) => (
            <label
              key={d.day_num}
              className={`admin__day-chip ${d.enabled ? 'is-on' : ''}`}
              title={d.date ?? ''}
            >
              <input
                type="checkbox"
                checked={d.enabled}
                onChange={() => toggleDay(d.day_num)}
              />
              <span>{d.dow}</span>
              <span className="admin__day-num">{d.day_num}</span>
            </label>
          ))}
        </div>
      </div>

      {saveError && <div className="admin__error">{saveError}</div>}

      <div className="admin-drawer__actions">
        <button
          type="submit"
          className="admin-btn admin-btn--primary"
          disabled={mut.isPending}
        >
          {mut.isPending ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </form>
  )
}
