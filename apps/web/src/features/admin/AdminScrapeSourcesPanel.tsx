import { FormEvent, useState } from 'react'
import { Link2, Play, Plus, Trash2 } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addScrapeSource,
  deleteScrapeSource,
  listScrapeSources,
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

export function AdminScrapeSourcesPanel({ conferenceId }: { conferenceId: string }) {
  const queryClient = useQueryClient()
  const [newUrl, setNewUrl] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [runMessage, setRunMessage] = useState<string | null>(null)
  const [runIsError, setRunIsError] = useState(false)

  const q = useQuery({
    queryKey: ['admin', 'sources', conferenceId],
    queryFn: () => listScrapeSources(conferenceId),
    enabled: !!conferenceId,
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['admin', 'sources', conferenceId] })

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

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteScrapeSource(id),
    onSuccess: invalidate,
  })

  const runMut = useMutation({
    mutationFn: () => triggerScrape(conferenceId),
    onSuccess: (r) => {
      setRunIsError(false)
      setRunMessage(r.message)
      invalidate()
    },
    onError: (e: Error) => {
      setRunIsError(true)
      setRunMessage(e.message)
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

  return (
    <section className="admin-sources">
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

      <div className="admin-sources__schedule">
        <span className="admin-sources__schedule-label">Auto-schedule</span>
        <span className="admin-sources__pill">coming soon</span>
        <span className="admin-sources__schedule-hint">
          We'll let you set a per-source scrape interval here later.
        </span>
      </div>
    </section>
  )
}
