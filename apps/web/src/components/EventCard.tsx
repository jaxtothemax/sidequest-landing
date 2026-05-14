import { Check, MapPin, Plus, Users } from 'lucide-react'

import type { SeedEvent } from '../data/seedEvents'

export function EventCard({
  event,
  onToggle,
}: {
  event: SeedEvent
  onToggle?: () => void
}) {
  return (
    <article className={`ev-card ${event.inSchedule ? 'is-in' : ''}`}>
      <div className="ev-card__time">
        <div className="ev-card__start">{event.start}</div>
        <div className="ev-card__end">{event.end}</div>
      </div>
      <div className="ev-card__body">
        <div className="ev-card__top">
          <span className="ev-card__tag">{event.tag}</span>
          <span className="ev-card__match">{event.match}% match</span>
          {event.inSchedule && (
            <span className="ev-card__pin">
              <Check size={10} /> In your plan
            </span>
          )}
        </div>
        <h4 className="ev-card__title">{event.title}</h4>
        <p className="ev-card__desc">{event.desc}</p>
        <div className="ev-card__meta">
          <span>
            <MapPin size={12} /> {event.venue}
          </span>
          <span>
            <Users size={12} /> {event.attendees}
          </span>
        </div>
      </div>
      {onToggle && (
        <button
          className={`ev-card__action ${event.inSchedule ? 'is-remove' : 'is-add'}`}
          onClick={onToggle}
          aria-label={event.inSchedule ? 'Remove from schedule' : 'Add to schedule'}
        >
          {event.inSchedule ? <Check size={16} strokeWidth={2.5} /> : <Plus size={16} />}
        </button>
      )}
    </article>
  )
}
