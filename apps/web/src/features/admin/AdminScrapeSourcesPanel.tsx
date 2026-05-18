import { FormEvent, useState } from 'react'
import { Link2, Play, Plus, Trash2 } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addScrapeSource,
  deleteScrapeSource,
  getSchedulerSettings,
  listScrapeSources,
  setSchedulerEnabled,
  triggerScrape,
  updateScrapeSource,
  type ScrapeSource,
} from '../../api/admin'

function fmtTimestamp(iso: string | null): string {
  if (!iso) return 'never'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString([], {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const INTERVAL_OPTIONS: { value: string; label: string; minutes: number | null }[] = [
  { value: 'off', label: 'Off', minutes: null },
  { value: '15', label: 'Every 15 min', minutes: 15 },
  { value: '60', label: 'Every hour', minutes: 60 },
  { value: '360', label: 'Every 6 h', minutes: 360 },
  { value: '1440', label: 'Every 24 h', minutes: 1440 },
]

function intervalValue(minutes: number | null): string {
  if (minutes === null) return 'off'
  // If a value not in the presets is set (e.g. manually), keep it in the
  // select as a synthetic option so the UI doesn't silently drop it.
  return INTERVAL_OPTIONS.some((o) => o.minutes === minutes) ? String(minutes) : String(minutes)
}

export function AdminScrapeSourcesPanel({ conferenceId }: { conferenceId: string }) {
  const queryClient = useQueryClient()
  const [newUrl, setNewUrl] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [runMessage, setRunMessage] = useState<string | null>(null)
  const [runIsError, setRunIsError] = useState(false)
  const [runFailedEvents, setRunFailedEvents] = useState<
    {
      api_id: string | null
      reason: string
      detail: string | null
      url: string | null
      title: string | null
    }[]
  >([])

  const q = useQuery({
    queryKey: ['admin', 'sources', conferenceId],
    queryFn: () => listScrapeSources(conferenceId),
    enabled: !!conferenceId,
  })

  const schedQ = useQuery({
    queryKey: ['admin', 'scheduler'],
    queryFn: getSchedulerSettings,
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['admin', 'sources', conferenceId] })

  const schedMut = useMutation({
    mutationFn: (enabled: boolean) => setSchedulerEnabled(enabled),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['admin', 'scheduler'] }),
  })

  const addMut = useMutation({
    mutationFn: (url: string) => addScrapeSource(conferenceId, { url }),
    onSuccess: () => {
      setNewUrl('')
      setAddError(null)
      invalidate()
    },
    onError: (e: Error) => setAddError(e.message),
  })

  const toggleMut = useMutation({
    mutationFn: (vars: { id: string; enabled: boolean }) =>
      updateScrapeSource(vars.id, { enabled: vars.enabled }),
    onSuccess: invalidate,
  })

  const intervalMut = useMutation({
    mutationFn: (vars: { id: string; minutes: number | null }) =>
      updateScrapeSource(vars.id, { scrape_interval_minutes: vars.minutes }),
    onSuccess: invalidate,
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteScrapeSource(id),
    onSuccess: invalidate,
  })

  const runMut = useMutation({
    mutationFn: () => triggerScrape(conferenceId),
    onSuccess: (r) => {
      setRunIsError(false)
      setRunMessage(r.message)
      setRunFailedEvents(r.failed_events ?? [])
      invalidate()
    },
    onError: (e: Error) => {
      setRunIsError(true)
      setRunMessage(e.message)
      setRunFailedEvents([])
    },
  })

  const submitNew = (e: FormEvent) => {
    e.preventDefault()
    if (!newUrl.trim()) return
    addMut.mutate(newUrl.trim())
  }

  const onDelete = (s: ScrapeSource) => {
    if (!confirm(`Remove this source?\n\n${s.url}`)) return
    deleteMut.mutate(s.id)
  }

  if (!conferenceId) return null

  const sched = schedQ.data
  const schedEnabled = sched?.enabled ?? false
  const schedTick = sched?.tick_seconds ?? 60

  return (
    <section className="admin-sources">
      <div className="admin-sources__scheduler">
        <label className="admin-sources__scheduler-toggle">
          <input
            type="checkbox"
            checked={schedEnabled}
            disabled={schedQ.isLoading || schedMut.isPending}
            onChange={(e) => schedMut.mutate(e.target.checked)}
          />
          <span>
            Auto-scrape scheduler:{' '}
            <strong>{schedEnabled ? 'on' : 'off'}</strong>
          </span>
        </label>
        <span className="admin-sources__scheduler-hint">
          {schedEnabled
            ? `Checks for due sources every ${schedTick}s (global, across all conferences).`
            : 'Toggle on to start running enabled sources on their configured interval.'}
        </span>
      </div>

      <header className="admin-sources__head">
        <div>
          <div className="admin-sources__title">Luma sources</div>
          <div className="admin-sources__sub">
            URLs the scraper will fetch events from when triggered.
          </div>
        </div>
        <button
          type="button"
          className="admin-btn admin-btn--primary"
          onClick={() => runMut.mutate()}
          disabled={runMut.isPending || !q.data?.some((s) => s.enabled)}
          title={
            q.data?.some((s) => s.enabled)
              ? 'Run all enabled sources now'
              : 'Add an enabled source first'
          }
        >
          <Play size={14} />
          {runMut.isPending ? 'Scraping…' : 'Scrape now'}
        </button>
      </header>

      {runMessage && (
        <div className={`admin-sources__run ${runIsError ? 'is-error' : ''}`}>
          {runMessage}
        </div>
      )}

      {runFailedEvents.length > 0 && (
        <details className="admin-sources__failed">
          <summary>
            {runFailedEvents.length} event{runFailedEvents.length === 1 ? '' : 's'} couldn't
            be saved — click for details
          </summary>
          <ul>
            {runFailedEvents.map((f, i) => {
              const label = f.title ?? f.api_id ?? '(no id)'
              return (
                <li key={`${f.api_id ?? 'noid'}-${i}`}>
                  {f.url ? (
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="admin-sources__failed-link"
                    >
                      {label} ↗
                    </a>
                  ) : (
                    <span>{label}</span>
                  )}
                  {' · '}
                  <strong>{f.reason}</strong>
                  {f.detail && (
                    <>
                      {' — '}
                      <span>{f.detail}</span>
                    </>
                  )}
                </li>
              )
            })}
          </ul>
        </details>
      )}

      <ul className="admin-sources__list">
        {q.isLoading && <li className="admin-sources__empty">Loading…</li>}
        {!q.isLoading && (q.data?.length ?? 0) === 0 && (
          <li className="admin-sources__empty">No sources yet — add one below.</li>
        )}
        {q.data?.map((s) => (
          <li key={s.id} className={`admin-sources__row ${s.enabled ? '' : 'is-off'}`}>
            <div className="admin-sources__row-main">
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer noopener"
                className="admin-sources__url"
              >
                <Link2 size={12} />
                {s.url}
              </a>
              <div className="admin-sources__meta">
                last scraped: <strong>{fmtTimestamp(s.last_scraped_at)}</strong>
                {s.last_status && (
                  <>
                    {' · '}
                    status: <strong>{s.last_status}</strong>
                  </>
                )}
                {s.scrape_interval_minutes !== null && (
                  <>
                    {' · '}
                    auto: <strong>every {s.scrape_interval_minutes}m</strong>
                  </>
                )}
                {s.last_status === 'pending' && s.last_error && (
                  <>
                    {' · '}
                    <span className="admin-sources__hint" title={s.last_error}>
                      stub
                    </span>
                  </>
                )}
              </div>
            </div>

            <label className="admin-sources__interval" title="Auto-scrape interval">
              <span className="admin-sources__interval-label">Schedule</span>
              <select
                value={intervalValue(s.scrape_interval_minutes)}
                onChange={(e) => {
                  const picked = INTERVAL_OPTIONS.find((o) => o.value === e.target.value)
                  intervalMut.mutate({
                    id: s.id,
                    minutes: picked ? picked.minutes : null,
                  })
                }}
                disabled={intervalMut.isPending}
              >
                {INTERVAL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
                {/* Preserve any non-preset value already on the row */}
                {s.scrape_interval_minutes !== null &&
                  !INTERVAL_OPTIONS.some((o) => o.minutes === s.scrape_interval_minutes) && (
                    <option value={String(s.scrape_interval_minutes)}>
                      Every {s.scrape_interval_minutes}m (custom)
                    </option>
                  )}
              </select>
            </label>

            <label className="admin-sources__toggle">
              <input
                type="checkbox"
                checked={s.enabled}
                onChange={() => toggleMut.mutate({ id: s.id, enabled: !s.enabled })}
              />
              <span>{s.enabled ? 'enabled' : 'disabled'}</span>
            </label>

            <button
              type="button"
              className="admin-btn admin-btn--icon admin-btn--danger"
              title="Remove"
              onClick={() => onDelete(s)}
              disabled={deleteMut.isPending}
            >
              <Trash2 size={14} />
            </button>
          </li>
        ))}
      </ul>

      <form className="admin-sources__add" onSubmit={submitNew}>
        <input
          type="url"
          placeholder="https://lu.ma/ethmilan2026"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          required
        />
        <button
          type="submit"
          className="admin-btn admin-btn--primary"
          disabled={addMut.isPending || !newUrl.trim()}
        >
          <Plus size={14} />
          {addMut.isPending ? 'Adding…' : 'Add source'}
        </button>
      </form>
      {addError && <div className="admin__error">{addError}</div>}
    </section>
  )
}
