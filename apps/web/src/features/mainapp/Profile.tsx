import { useMemo, useState } from 'react'
import {
  ChevronRight,
  Edit2,
  Globe,
  Linkedin,
  LogOut,
  Mail,
  Twitter,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { supabase } from '../../lib/supabase'
import { useOnboarding } from '../../stores/onboardingStore'

export function ProfilePage() {
  const navigate = useNavigate()
  const { state, reset } = useOnboarding()
  const [name, setName] = useState('Alex Morgan')
  const [title, setTitle] = useState('Founder · Stable Labs')
  const [email, setEmail] = useState('alex@stablelabs.xyz')
  const [editing, setEditing] = useState(false)
  const [twitter, setTwitter] = useState('alexstable')
  const [linkedin, setLinkedin] = useState('alexmorgan')
  const [website, setWebsite] = useState('stablelabs.xyz')

  const summary = useMemo(
    () => [
      { label: 'Conference', value: state.conferenceId === 'token2049' ? 'TOKEN2049 Dubai' : state.conferenceId },
      { label: 'Attendance', value: state.attendance ?? '—' },
      { label: 'Days', value: state.days.length ? state.days.join(', ') : '—' },
      { label: 'Role', value: state.role ?? '—' },
      { label: 'Top goals', value: state.goals.slice(0, 3).join(', ') || '—' },
      { label: 'Topics', value: state.topics.slice(0, 4).join(', ') || '—' },
      { label: 'Pace', value: `${state.pace}` },
      { label: 'Energy', value: `${state.energy}` },
      { label: 'Social', value: `${state.social}` },
      { label: 'Must-haves', value: state.mustHaves.join(', ') || '—' },
    ],
    [state],
  )

  const onLogout = async () => {
    await supabase.auth.signOut().catch(() => {})
    reset()
    navigate('/', { replace: true })
  }

  return (
    <div className="prof">
      <div className="prof__hero">
        <div className="prof__avatar">
          {name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .slice(0, 2)}
        </div>
        {!editing ? (
          <>
            <h1 className="prof__name">{name}</h1>
            <div className="prof__title">{title}</div>
            <button className="prof__edit-btn" onClick={() => setEditing(true)}>
              <Edit2 size={14} /> Edit profile
            </button>
          </>
        ) : (
          <div className="prof__edit">
            <label className="prof__field">
              <span>Name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="prof__field">
              <span>Title</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <label className="prof__field">
              <span>Email</span>
              <input value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <button className="btn-primary" onClick={() => setEditing(false)}>
              Save
            </button>
          </div>
        )}
      </div>

      <section className="prof__section">
        <h3 className="prof__section-title">Social</h3>
        <div className="prof__socials">
          <SocialRow Icon={Mail} label="Email" value={email} onChange={setEmail} />
          <SocialRow Icon={Twitter} label="Twitter" value={twitter} onChange={setTwitter} prefix="@" />
          <SocialRow Icon={Linkedin} label="LinkedIn" value={linkedin} onChange={setLinkedin} prefix="in/" />
          <SocialRow Icon={Globe} label="Website" value={website} onChange={setWebsite} />
        </div>
      </section>

      <section className="prof__section">
        <div className="prof__section-head">
          <h3 className="prof__section-title">Your preferences</h3>
          <button className="prof__retake" onClick={() => navigate('/onboarding')}>
            Retake quiz <ChevronRight size={14} />
          </button>
        </div>
        <div className="prof__pref-list">
          {summary.map((p) => (
            <div key={p.label} className="prof__pref-row">
              <div className="prof__pref-label">{p.label}</div>
              <div className="prof__pref-value">{p.value}</div>
              <button className="prof__pref-edit" aria-label={`Edit ${p.label}`}>
                <Edit2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="prof__section">
        <button className="prof__logout" onClick={onLogout}>
          <LogOut size={16} /> Log out
        </button>
      </section>
    </div>
  )
}

function SocialRow({
  Icon,
  label,
  value,
  onChange,
  prefix,
}: {
  Icon: typeof Mail
  label: string
  value: string
  onChange: (v: string) => void
  prefix?: string
}) {
  return (
    <label className="soc-row">
      <Icon size={16} />
      <span className="soc-row__label">{label}</span>
      <div className="soc-row__input">
        {prefix && <span className="soc-row__prefix">{prefix}</span>}
        <input value={value} onChange={(e) => onChange(e.target.value)} />
      </div>
    </label>
  )
}
