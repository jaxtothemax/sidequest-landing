import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AdminConferencesPanel } from './AdminConferencesPanel'
import { AdminEventsPanel } from './AdminEventsPanel'

type Tab = 'events' | 'conferences'

export default function Admin() {
  const [tab, setTab] = useState<Tab>('events')

  return (
    <div className="admin-shell">
      <div className="admin">
      <header className="admin__header">
        <div>
          <h1 className="admin__title">SideQuest admin</h1>
          <div className="admin__sub">Manage events and conferences</div>
        </div>
        <Link to="/app/chat" className="admin__exit">
          Back to app →
        </Link>
      </header>

      <nav className="admin__tabs">
        <button
          className={`admin__tab ${tab === 'events' ? 'is-active' : ''}`}
          onClick={() => setTab('events')}
        >
          Events
        </button>
        <button
          className={`admin__tab ${tab === 'conferences' ? 'is-active' : ''}`}
          onClick={() => setTab('conferences')}
        >
          Conferences
        </button>
      </nav>

      {tab === 'events' && <AdminEventsPanel />}
      {tab === 'conferences' && <AdminConferencesPanel />}
      </div>
    </div>
  )
}
