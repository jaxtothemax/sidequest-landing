import { useEffect, useMemo, useRef, useState } from "react";
import {
  MessageSquare,
  Calendar as CalendarIcon,
  User as UserIcon,
  Send,
  Plus,
  Check,
  X,
  Search,
  Filter,
  MapPin,
  Clock,
  Users,
  Edit2,
  Twitter,
  Linkedin,
  Globe,
  Mail,
  ChevronRight,
  LogOut,
} from "lucide-react";
import SymbolSVG from "../../imports/Symbol.svg";
import type { State as OnboardingState } from "./Onboarding";

type Tab = "chat" | "schedule" | "profile";

type Event = {
  id: string;
  title: string;
  day: number;
  start: string;
  end: string;
  venue: string;
  tag: string;
  attendees: number;
  match: number; // 0..100
  inSchedule: boolean;
  desc: string;
};

const SEED_EVENTS: Event[] = [
  { id: "e1", title: "Stable Summit IV", day: 29, start: "9:00 AM", end: "11:00 AM", venue: "Sheraton · Mina A'Salam", tag: "Founders", attendees: 320, match: 96, inSchedule: true, desc: "The flagship gathering for stablecoin builders, with talks from founders shipping at scale." },
  { id: "e2", title: "Investor Coffee — Seed Stage", day: 29, start: "11:30 AM", end: "12:30 PM", venue: "Madinat · Al Qasr Lobby", tag: "Investors", attendees: 80, match: 92, inSchedule: true, desc: "Curated 1:1 round-robin between founders and seed-stage funds." },
  { id: "e3", title: "DeFi Liquidity Panel", day: 29, start: "2:00 PM", end: "3:00 PM", venue: "Main Stage", tag: "DeFi", attendees: 600, match: 88, inSchedule: true, desc: "Top market makers and protocol leads on liquidity in the next cycle." },
  { id: "e4", title: "Token2049 Mainstage Keynote", day: 29, start: "4:00 PM", end: "5:00 PM", venue: "Main Stage", tag: "Keynote", attendees: 1200, match: 84, inSchedule: true, desc: "The mainstage keynote setting the tone for the conference." },
  { id: "e5", title: "Founders & Funds Rooftop", day: 29, start: "7:30 PM", end: "11:00 PM", venue: "Five Palm · Rooftop", tag: "Mixer", attendees: 220, match: 91, inSchedule: true, desc: "Quality networking under Dubai skyline. Limited capacity." },
  { id: "e6", title: "AI x Crypto Workshop", day: 30, start: "9:30 AM", end: "11:30 AM", venue: "Joharah Ballroom", tag: "Workshop", attendees: 150, match: 78, inSchedule: false, desc: "Hands-on builder session on agentic on-chain workflows." },
  { id: "e7", title: "Gulf Capital LP Lunch", day: 30, start: "12:30 PM", end: "2:00 PM", venue: "Pierchic", tag: "Investors", attendees: 60, match: 89, inSchedule: true, desc: "Invite-only LP/GP lunch hosted by regional family offices." },
  { id: "e8", title: "Layer 2 Scaling Roundtable", day: 30, start: "3:00 PM", end: "4:00 PM", venue: "Stage B", tag: "Tech", attendees: 200, match: 73, inSchedule: false, desc: "L2 leads compare notes on throughput, fees, and rollup direction." },
  { id: "e9", title: "Closing Yacht Party", day: 30, start: "8:00 PM", end: "1:00 AM", venue: "Dubai Harbour · Marina", tag: "Party", attendees: 400, match: 80, inSchedule: true, desc: "The unofficial closing party. Boarding starts at 8pm sharp." },
  { id: "e10", title: "Builders Breakfast — Bitcoin DeFi", day: 30, start: "8:00 AM", end: "9:15 AM", venue: "Bahri Bar", tag: "Founders", attendees: 50, match: 81, inSchedule: false, desc: "Small-format breakfast with Bitcoin DeFi protocol founders." },
  { id: "e11", title: "Press & Media Hour", day: 29, start: "1:00 PM", end: "2:00 PM", venue: "Press Lounge", tag: "Press", attendees: 90, match: 60, inSchedule: false, desc: "Open hour for journalists to meet founders." },
  { id: "e12", title: "MENA Regulators Fireside", day: 30, start: "10:00 AM", end: "11:00 AM", venue: "Main Stage", tag: "Policy", attendees: 800, match: 70, inSchedule: false, desc: "VARA leadership on the future of MENA crypto policy." },
];

type ChatMsg = { id: string; from: "agent" | "user"; text: string; chips?: string[]; events?: Event[] };

const INITIAL_MESSAGES: ChatMsg[] = [
  {
    id: "m1",
    from: "agent",
    text:
      "Welcome! I've curated 7 events across your 2 days based on your goals. Want me to walk you through Wednesday, swap anything, or just ask me about logistics?",
    chips: ["Walk me through Wed", "Swap an event", "Dress code?", "Best route between venues"],
  },
];

export default function MainApp({ state, onLogout }: { state: OnboardingState; onLogout?: () => void }) {
  const [tab, setTab] = useState<Tab>("chat");
  const [events, setEvents] = useState<Event[]>(SEED_EVENTS);

  const toggleEvent = (id: string) =>
    setEvents((es) => es.map((e) => (e.id === id ? { ...e, inSchedule: !e.inSchedule } : e)));

  return (
    <div className="sq-app">
      <div className="sq-frame ma">
        <div className="ma__page">
          {tab === "chat" && <ChatPage events={events} />}
          {tab === "schedule" && <SchedulePage events={events} onToggle={toggleEvent} />}
          {tab === "profile" && <ProfilePage state={state} onLogout={onLogout} />}
        </div>
        <BottomNav tab={tab} onChange={setTab} />
      </div>
    </div>
  );
}

/* ---------------- Bottom Nav ---------------- */

function BottomNav({ tab, onChange }: { tab: Tab; onChange: (t: Tab) => void }) {
  const items: { id: Tab; label: string; Icon: any }[] = [
    { id: "chat", label: "Assistant", Icon: MessageSquare },
    { id: "schedule", label: "Schedule", Icon: CalendarIcon },
    { id: "profile", label: "Profile", Icon: UserIcon },
  ];
  return (
    <nav className="ma-nav">
      {items.map(({ id, label, Icon }) => {
        const active = id === tab;
        return (
          <button
            key={id}
            className={`ma-nav__item ${active ? "is-active" : ""}`}
            onClick={() => onChange(id)}
          >
            <Icon size={22} strokeWidth={active ? 2.4 : 1.8} />
            <span>{label}</span>
          </button>
        );
      })}
    </nav>
  );
}

/* ---------------- Chat Page ---------------- */

function ChatPage({ events }: { events: Event[] }) {
  const [messages, setMessages] = useState<ChatMsg[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const userMsg: ChatMsg = { id: `u${Date.now()}`, from: "user", text: trimmed };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setThinking(true);
    setTimeout(() => {
      const reply = generateReply(trimmed, events);
      setMessages((m) => [...m, reply]);
      setThinking(false);
    }, 900);
  };

  const scheduledCount = events.filter((e) => e.inSchedule).length;

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__avatar">
          <img src={SymbolSVG} alt="" />
        </div>
        <div className="chat__title-wrap">
          <div className="chat__title">SideQuest Agent</div>
          <div className="chat__sub">
            <span className="chat__dot" /> {scheduledCount} events on your plan
          </div>
        </div>
      </div>

      <div ref={scrollRef} className="chat__scroll">
        {messages.map((m) => (
          <div key={m.id} className={`chat-msg chat-msg--${m.from}`}>
            {m.from === "agent" && (
              <div className="chat-msg__avatar">
                <img src={SymbolSVG} alt="" />
              </div>
            )}
            <div className="chat-msg__bubble">
              <div className="chat-msg__text">{m.text}</div>
              {m.events && m.events.length > 0 && (
                <div className="chat-msg__events">
                  {m.events.map((e) => (
                    <EventCard key={e.id} event={e} />
                  ))}
                </div>
              )}
              {m.chips && (
                <div className="chat-msg__chips">
                  {m.chips.map((c) => (
                    <button key={c} className="chat-chip" onClick={() => send(c)}>
                      {c}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {thinking && (
          <div className="chat-msg chat-msg--agent">
            <div className="chat-msg__avatar">
              <img src={SymbolSVG} alt="" />
            </div>
            <div className="chat-msg__bubble">
              <div className="chat-typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
      </div>

      <form
        className="chat__input"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your schedule, dress code, directions…"
        />
        <button type="submit" className="chat__send" disabled={!input.trim()} aria-label="Send">
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

function generateReply(text: string, events: Event[]): ChatMsg {
  const lower = text.toLowerCase();
  if (/dress|wear|outfit/.test(lower)) {
    return {
      id: `a${Date.now()}`,
      from: "agent",
      text:
        "Dubai in late April is hot (~32°C). Daytime: smart casual — linen shirt, chinos, comfortable shoes (Madinat has long walks). For the Founders & Funds Rooftop and the Closing Yacht Party, lean dressy — dark jeans + blazer or a summer dress. No suits required at any event on your plan.",
    };
  }
  if (/route|direction|map|how.*get|between/.test(lower)) {
    return {
      id: `a${Date.now()}`,
      from: "agent",
      text:
        "From Sheraton Mina A'Salam to the Main Stage it's a 6-min walk through the souk — or a 2-min buggy ride (shuttles every 5 min). After 4pm sessions, grab a Careem to Five Palm — about 12 min in traffic. Want me to add buffer time between Wednesday's afternoon sessions?",
      chips: ["Yes, add buffers", "Show me Thursday route"],
    };
  }
  if (/swap|change|replace|move/.test(lower)) {
    return {
      id: `a${Date.now()}`,
      from: "agent",
      text:
        "I can swap something. The lowest-match event on your plan right now is the Token2049 Mainstage Keynote (84%). Want me to drop it for the AI x Crypto Workshop on Thursday morning, or something else?",
      chips: ["Drop keynote, add workshop", "Show alternatives"],
    };
  }
  if (/ticket|badge|registration/.test(lower)) {
    return {
      id: `a${Date.now()}`,
      from: "agent",
      text:
        "Your TOKEN2049 Pro pass is registered to your email. Pick up your badge at Madinat Arena, Hall 2 between 8–10am Wednesday. The Yacht Party requires a separate RSVP — I can request you a +1 spot if you want.",
      chips: ["Request yacht party RSVP"],
    };
  }
  if (/walk.*me|wednesday|wed/.test(lower)) {
    const wed = events.filter((e) => e.day === 29 && e.inSchedule);
    return {
      id: `a${Date.now()}`,
      from: "agent",
      text:
        `Here's your Wednesday — ${wed.length} events. Tightest gap is between the DeFi panel and the keynote (1hr). Want me to suggest people to meet at each one?`,
      events: wed,
      chips: ["Suggest people", "Add a coffee break"],
    };
  }
  return {
    id: `a${Date.now()}`,
    from: "agent",
    text:
      "Got it. I can curate further, swap events, give you logistics, or pull up info on speakers. What would help most?",
    chips: ["Tighten my schedule", "Add networking time", "Speaker info"],
  };
}

/* ---------------- Schedule Page ---------------- */

function SchedulePage({ events, onToggle }: { events: Event[]; onToggle: (id: string) => void }) {
  const [view, setView] = useState<"mine" | "all">("mine");
  const [day, setDay] = useState<number | "all">("all");
  const [tag, setTag] = useState<string>("all");
  const [query, setQuery] = useState("");

  const tags = useMemo(() => Array.from(new Set(events.map((e) => e.tag))), [events]);
  const days = useMemo(() => Array.from(new Set(events.map((e) => e.day))).sort(), [events]);

  const filtered = useMemo(() => {
    return events.filter((e) => {
      if (view === "mine" && !e.inSchedule) return false;
      if (day !== "all" && e.day !== day) return false;
      if (tag !== "all" && e.tag !== tag) return false;
      if (query && !e.title.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [events, view, day, tag, query]);

  const grouped = useMemo(() => {
    const map: Record<number, Event[]> = {};
    filtered.forEach((e) => {
      map[e.day] = map[e.day] || [];
      map[e.day].push(e);
    });
    Object.values(map).forEach((arr) => arr.sort((a, b) => a.start.localeCompare(b.start)));
    return map;
  }, [filtered]);

  const mineCount = events.filter((e) => e.inSchedule).length;

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
          className={`sched__tab ${view === "mine" ? "is-active" : ""}`}
          onClick={() => setView("mine")}
        >
          My plan
        </button>
        <button
          className={`sched__tab ${view === "all" ? "is-active" : ""}`}
          onClick={() => setView("all")}
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
            className={`f-chip ${day === "all" ? "is-active" : ""}`}
            onClick={() => setDay("all")}
          >
            All days
          </button>
          {days.map((d) => (
            <button
              key={d}
              className={`f-chip ${day === d ? "is-active" : ""}`}
              onClick={() => setDay(d)}
            >
              {d === 29 ? "Wed 29" : d === 30 ? "Thu 30" : `Day ${d}`}
            </button>
          ))}
          <div className="sched__chips-divider" />
          <button
            className={`f-chip ${tag === "all" ? "is-active" : ""}`}
            onClick={() => setTag("all")}
          >
            <Filter size={12} /> All
          </button>
          {tags.map((t) => (
            <button
              key={t}
              className={`f-chip ${tag === t ? "is-active" : ""}`}
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
                {d === 29 ? "Wednesday, April 29" : d === 30 ? "Thursday, April 30" : `Day ${d}`}
              </h3>
              {grouped[d].map((e) => (
                <EventCard key={e.id} event={e} onToggle={() => onToggle(e.id)} />
              ))}
            </section>
          ))}
      </div>
    </div>
  );
}

function EventCard({ event, onToggle }: { event: Event; onToggle?: () => void }) {
  return (
    <article className={`ev-card ${event.inSchedule ? "is-in" : ""}`}>
      <div className="ev-card__time">
        <div className="ev-card__start">{event.start}</div>
        <div className="ev-card__end">{event.end}</div>
      </div>
      <div className="ev-card__body">
        <div className="ev-card__top">
          <span className="ev-card__tag">{event.tag}</span>
          <span className="ev-card__match">{event.match}% match</span>
        </div>
        <h4 className="ev-card__title">{event.title}</h4>
        <p className="ev-card__desc">{event.desc}</p>
        <div className="ev-card__meta">
          <span><MapPin size={12} /> {event.venue}</span>
          <span><Users size={12} /> {event.attendees}</span>
        </div>
      </div>
      {onToggle && (
        <button
          className={`ev-card__action ${event.inSchedule ? "is-remove" : "is-add"}`}
          onClick={onToggle}
          aria-label={event.inSchedule ? "Remove from schedule" : "Add to schedule"}
        >
          {event.inSchedule ? <X size={16} /> : <Plus size={16} />}
        </button>
      )}
    </article>
  );
}

/* ---------------- Profile Page ---------------- */

function ProfilePage({ state, onLogout }: { state: OnboardingState; onLogout?: () => void }) {
  const [name, setName] = useState("Alex Morgan");
  const [title, setTitle] = useState("Founder · Stable Labs");
  const [email, setEmail] = useState("alex@stablelabs.xyz");
  const [editing, setEditing] = useState(false);
  const [twitter, setTwitter] = useState("alexstable");
  const [linkedin, setLinkedin] = useState("alexmorgan");
  const [website, setWebsite] = useState("stablelabs.xyz");

  const summary = useMemo(() => {
    const parts: { label: string; value: string }[] = [
      { label: "Conference", value: state.conferenceId === "token2049" ? "TOKEN2049 Dubai" : state.conferenceId },
      { label: "Attendance", value: state.attendance ?? "—" },
      { label: "Days", value: state.days.length ? state.days.join(", ") : "—" },
      { label: "Role", value: state.role ?? "—" },
      { label: "Top goals", value: state.goals.slice(0, 3).join(", ") || "—" },
      { label: "Topics", value: state.topics.slice(0, 4).join(", ") || "—" },
      { label: "Pace", value: `${state.pace}` },
      { label: "Energy", value: `${state.energy}` },
      { label: "Social", value: `${state.social}` },
      { label: "Must-haves", value: state.mustHaves.join(", ") || "—" },
    ];
    return parts;
  }, [state]);

  return (
    <div className="prof">
      <div className="prof__hero">
        <div className="prof__avatar">{name.split(" ").map((n) => n[0]).join("").slice(0, 2)}</div>
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
            <button className="btn-primary" onClick={() => setEditing(false)}>Save</button>
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
          <button className="prof__retake">Retake quiz <ChevronRight size={14} /></button>
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
  );
}

function SocialRow({
  Icon,
  label,
  value,
  onChange,
  prefix,
}: {
  Icon: any;
  label: string;
  value: string;
  onChange: (v: string) => void;
  prefix?: string;
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
  );
}
