import { Calendar as CalendarIcon, MessageSquare, User as UserIcon } from 'lucide-react'
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { ChatPage } from './Chat'
import { SchedulePage } from './Schedule'
import { ProfilePage } from './Profile'

export default function MainApp() {
  const location = useLocation()
  const isApp = location.pathname.startsWith('/app')
  if (!isApp) return <Navigate to="/app/chat" replace />

  return (
    <div className="sq-app">
      <div className="sq-frame ma">
        <div className="ma__page">
          <Routes>
            <Route index element={<Navigate to="chat" replace />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="schedule" element={<SchedulePage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Routes>
        </div>
        <BottomNav />
      </div>
    </div>
  )
}

function BottomNav() {
  const items = [
    { to: 'chat', label: 'Assistant', Icon: MessageSquare },
    { to: 'schedule', label: 'Schedule', Icon: CalendarIcon },
    { to: 'profile', label: 'Profile', Icon: UserIcon },
  ]
  return (
    <nav className="ma-nav">
      {items.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `ma-nav__item ${isActive ? 'is-active' : ''}`}
        >
          {({ isActive }) => (
            <>
              <Icon size={22} strokeWidth={isActive ? 2.4 : 1.8} />
              <span>{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
