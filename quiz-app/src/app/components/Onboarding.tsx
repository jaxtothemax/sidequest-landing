import { useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronLeft,
  Calendar,
  CalendarDays,
  Ban,
  Search,
  Plus,
  X,
  Info,
  Zap,
  Clock,
  Eye,
  Moon,
  Star,
  Compass,
  User as UserIcon,
} from "lucide-react";
import SymbolSVG from "../../imports/Symbol.svg";
import WhiteLogoSVG from "../../imports/White.svg";

type Role =
  | "founder"
  | "investor"
  | "developer"
  | "marketer"
  | "corporate"
  | "journalist";
type Attendance = "full" | "partial" | "side-only";

export type State = {
  conferenceId: string;
  attendance: Attendance | null;
  days: number[]; // day numbers selected
  role: Role | null;
  goals: string[]; // ranked
  topics: string[];
  pace: number; // 0..100
  energy: number; // 0..100 (low = morning)
  social: number; // 0..100 (low = quality)
  mustHaves: string[];
};

const CONFERENCES = [
  {
    id: "token2049",
    name: "TOKEN2049 Dubai",
    meta: "29 Apr – 30 Apr · Madinat Jumeirah",
    gradient: "linear-gradient(135deg, #FFD072, #E62C5A)",
    days: [
      { dow: "Sun", num: 26, enabled: false },
      { dow: "Mon", num: 27, enabled: false },
      { dow: "Tue", num: 28, enabled: false },
      { dow: "Wed", num: 29, enabled: true },
      { dow: "Thu", num: 30, enabled: true },
      { dow: "Fri", num: 1, enabled: false },
      { dow: "Sat", num: 2, enabled: false },
    ],
    month: "APRIL 2026",
  },
  {
    id: "ethglobal",
    name: "ETHGlobal Bangkok",
    meta: "15 May – 18 May · QSNCC",
    gradient: "linear-gradient(135deg, #6088F7, #1E4EB0)",
    days: [],
    month: "MAY 2026",
  },
  {
    id: "consensus",
    name: "Consensus Toronto",
    meta: "10 Jun – 13 Jun · MTCC",
    gradient: "linear-gradient(135deg, #FF8C9E, #C61E4A)",
    days: [],
    month: "JUNE 2026",
  },
];

const ROLES: { id: Role; label: string; emoji: string; desc: string }[] = [
  { id: "founder", label: "Founder", emoji: "🚀", desc: "Building, raising, hiring" },
  { id: "investor", label: "Investor", emoji: "💸", desc: "Sourcing deals" },
  { id: "developer", label: "Developer", emoji: "⌨️", desc: "Building, learning" },
  { id: "marketer", label: "Marketer", emoji: "📈", desc: "Growth, BD, partners" },
  { id: "corporate", label: "Corporate", emoji: "🏢", desc: "Enterprise, strategy" },
  { id: "journalist", label: "Journalist", emoji: "📰", desc: "Covering, writing" },
];

const GOALS_BY_ROLE: Record<Role, { id: string; label: string; emoji: string; desc: string }[]> = {
  founder: [
    { id: "fundraising", label: "Fundraising", emoji: "💸", desc: "Meet investors" },
    { id: "partnerships", label: "Partnerships", emoji: "🤝", desc: "Build relationships" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Meet new people" },
    { id: "hiring", label: "Hiring", emoji: "🎯", desc: "Find talent" },
    { id: "learning", label: "Learning", emoji: "📚", desc: "New tech, trends" },
    { id: "deals", label: "Closing deals", emoji: "💼", desc: "Sales, contracts" },
  ],
  investor: [
    { id: "deals", label: "Deal flow", emoji: "💸", desc: "Source startups" },
    { id: "lps", label: "LP meetings", emoji: "🤝", desc: "Talk to backers" },
    { id: "research", label: "Research", emoji: "📚", desc: "Themes & trends" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Other funds" },
    { id: "branding", label: "Brand", emoji: "📢", desc: "Visibility" },
    { id: "portfolio", label: "Portfolio", emoji: "📈", desc: "Help founders" },
  ],
  developer: [
    { id: "learning", label: "Learning", emoji: "📚", desc: "New tools" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Other devs" },
    { id: "hackathons", label: "Hackathons", emoji: "⚡", desc: "Build & ship" },
    { id: "jobs", label: "Job search", emoji: "💼", desc: "Next role" },
    { id: "open-source", label: "Open source", emoji: "🌐", desc: "Contributions" },
    { id: "research", label: "Research", emoji: "🔬", desc: "Deep dives" },
  ],
  marketer: [
    { id: "partnerships", label: "Partnerships", emoji: "🤝", desc: "BD pipeline" },
    { id: "leads", label: "Lead gen", emoji: "🎯", desc: "Pipeline" },
    { id: "branding", label: "Brand", emoji: "📢", desc: "Awareness" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Peers" },
    { id: "learning", label: "Learning", emoji: "📚", desc: "Trends" },
    { id: "press", label: "Press", emoji: "📰", desc: "Coverage" },
  ],
  corporate: [
    { id: "scouting", label: "Scouting", emoji: "🔍", desc: "Innovation tech" },
    { id: "partnerships", label: "Partnerships", emoji: "🤝", desc: "Strategic deals" },
    { id: "learning", label: "Learning", emoji: "📚", desc: "Industry trends" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Peers" },
    { id: "hiring", label: "Hiring", emoji: "🎯", desc: "Talent" },
    { id: "branding", label: "Brand", emoji: "📢", desc: "Visibility" },
  ],
  journalist: [
    { id: "stories", label: "Stories", emoji: "📰", desc: "Find leads" },
    { id: "interviews", label: "Interviews", emoji: "🎙️", desc: "Speakers, founders" },
    { id: "networking", label: "Networking", emoji: "👋", desc: "Sources" },
    { id: "research", label: "Research", emoji: "📚", desc: "Beat coverage" },
    { id: "press", label: "Press events", emoji: "📢", desc: "Announcements" },
    { id: "scoops", label: "Scoops", emoji: "⚡", desc: "Exclusive news" },
  ],
};

const TOPICS = [
  "AI / ML", "DeFi", "Stablecoins", "L2s & Rollups", "Infra",
  "Privacy / ZK", "Trading", "SaaS", "Climate", "Consumer",
  "RWA", "Gaming", "Mobile", "Hardware", "Bio / Health",
  "Security", "DePIN", "Open-source",
];

const SUGGESTIONS = [
  { id: "stani", initials: "SC", name: "Stani Kulechov", role: "Founder · Aave", grad: undefined },
  { id: "rune", initials: "RC", name: "Rune Christensen", role: "Founder · Sky / MakerDAO", grad: "linear-gradient(135deg, #6088F7, #1E4EB0)" },
  { id: "hayden", initials: "HA", name: "Hayden Adams", role: "Founder · Uniswap", grad: "linear-gradient(135deg, #FF8C9E, #C61E4A)" },
];

const TOTAL_STEPS = 10;

const SQMark = ({ size = 100 }: { size?: number; color?: string }) => (
  <img src={SymbolSVG} alt="SideQuest" style={{ width: size, height: size }} />
);

function Slider({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const setFromClientX = (clientX: number) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
    onChange(Math.round(pct));
  };
  const onPointerDown = (e: React.PointerEvent) => {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    setFromClientX(e.clientX);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (e.buttons === 0) return;
    setFromClientX(e.clientX);
  };
  return (
    <div
      ref={ref}
      className="slider-track"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
    >
      <div className="slider-fill" style={{ width: `${value}%` }} />
      <div className="slider-thumb" style={{ left: `${value}%` }} />
    </div>
  );
}

function Header({
  step,
  total,
  onBack,
  onSkip,
  hideSkip,
  hideBack,
}: {
  step: number;
  total: number;
  onBack?: () => void;
  onSkip?: () => void;
  hideSkip?: boolean;
  hideBack?: boolean;
}) {
  return (
    <div className="scr__top">
      <button
        className="scr__back"
        onClick={onBack}
        disabled={hideBack}
        style={hideBack ? { visibility: "hidden" } : undefined}
        aria-label="Back"
      >
        <ChevronLeft />
      </button>
      <div className="scr__progress">
        {Array.from({ length: total }).map((_, i) => (
          <span key={i} className={i < step - 1 ? "done" : i === step - 1 ? "cur" : ""} />
        ))}
      </div>
      <button
        className="scr__skip"
        onClick={onSkip}
        style={{ visibility: hideSkip ? "hidden" : "visible" }}
      >
        Skip
      </button>
    </div>
  );
}

export default function Onboarding({ onComplete }: { onComplete?: (state: State) => void } = {}) {
  const [step, setStep] = useState(0); // 0 = welcome, 1..10 = steps, 11 = curating, 12 = done
  const [state, setState] = useState<State>({
    conferenceId: "token2049",
    attendance: null,
    days: [],
    role: null,
    goals: [],
    topics: [],
    pace: 60,
    energy: 30,
    social: 38,
    mustHaves: [],
  });

  const conf = useMemo(
    () => CONFERENCES.find((c) => c.id === state.conferenceId)!,
    [state.conferenceId],
  );

  const next = () => setStep((s) => s + 1);
  const back = () => setStep((s) => Math.max(0, s - 1));
  const skip = () => setStep((s) => s + 1);
  const goTo = (s: number) => setStep(s);

  // Auto-advance loading -> done
  useEffect(() => {
    if (step === 11) {
      const t = setTimeout(() => setStep(12), 3200);
      return () => clearTimeout(t);
    }
  }, [step]);

  return (
    <div className="sq-app">
      <div className="sq-frame">
        {step === 0 && <Welcome onStart={next} onSkip={() => setStep(12)} />}
        {step === 1 && (
          <ConferencePicker
            value={state.conferenceId}
            onChange={(v) => setState((s) => ({ ...s, conferenceId: v }))}
            onBack={back}
            onNext={next}
          />
        )}
        {step === 2 && (
          <AttendanceStep
            conf={conf}
            value={state.attendance}
            onChange={(v) => setState((s) => ({ ...s, attendance: v }))}
            onBack={back}
            onNext={() => setStep(state.attendance === "full" ? 4 : 3)}
          />
        )}
        {step === 3 && (
          <DaysStep
            conf={conf}
            value={state.days}
            onChange={(v) => setState((s) => ({ ...s, days: v }))}
            onBack={back}
            onNext={next}
          />
        )}
        {step === 4 && (
          <RoleStep
            value={state.role}
            onChange={(v) => setState((s) => ({ ...s, role: v }))}
            onBack={back}
            onNext={next}
          />
        )}
        {step === 5 && (
          <GoalsStep
            role={state.role}
            value={state.goals}
            onChange={(v) => setState((s) => ({ ...s, goals: v }))}
            onBack={back}
            onNext={next}
          />
        )}
        {step === 6 && (
          <TopicsStep
            value={state.topics}
            onChange={(v) => setState((s) => ({ ...s, topics: v }))}
            onBack={back}
            onSkip={skip}
            onNext={next}
          />
        )}
        {step === 7 && (
          <ScheduleStep
            pace={state.pace}
            energy={state.energy}
            onChange={(p, e) => setState((s) => ({ ...s, pace: p, energy: e }))}
            onBack={back}
            onSkip={skip}
            onNext={next}
          />
        )}
        {step === 8 && (
          <SocialStep
            value={state.social}
            onChange={(v) => setState((s) => ({ ...s, social: v }))}
            onBack={back}
            onSkip={skip}
            onNext={next}
          />
        )}
        {step === 9 && (
          <MustHavesStep
            value={state.mustHaves}
            onChange={(v) => setState((s) => ({ ...s, mustHaves: v }))}
            onBack={back}
            onSkip={skip}
            onNext={next}
          />
        )}
        {step === 10 && (
          <ReviewStep
            state={state}
            conf={conf}
            onBack={back}
            onEdit={goTo}
            onNext={() => setStep(11)}
          />
        )}
        {step === 11 && <Curating role={state.role} />}
        {step === 12 && <Done conf={conf} onRestart={() => setStep(0)} onEnter={() => onComplete?.(state)} />}
      </div>
    </div>
  );
}

/* ---------- Step components ---------- */

function Welcome({ onStart, onSkip }: { onStart: () => void; onSkip: () => void }) {
  return (
    <div className="scr-welcome">
      <div className="scr-welcome__hero">
        <button className="scr-welcome__skip" onClick={onSkip}>Skip</button>
        <img src={WhiteLogoSVG} alt="SideQuest" className="scr-welcome__lockup" />
      </div>
      <div className="scr-welcome__panel">
        <Header step={1} total={TOTAL_STEPS} hideBack hideSkip />
        <div className="scr__step-label">Step 1 of 10</div>
        <h1 className="scr-welcome__title">
          Your <em>perfect</em> conference, planned in 90 seconds.
        </h1>
        <p className="scr-welcome__body">
          Tell us a little about you. We'll build a schedule of talks, side-events
          and people worth meeting — tuned to how you work the room.
        </p>
        <ul className="scr-welcome__bullets">
          <li>Talks matched to your goals</li>
          <li>Side-events for your style</li>
          <li>People worth meeting</li>
        </ul>
        <button className="btn-primary" style={{ marginTop: "auto" }} onClick={onStart}>
          Get started
        </button>
      </div>
    </div>
  );
}

function ConferencePicker({
  value, onChange, onBack, onNext,
}: { value: string; onChange: (v: string) => void; onBack: () => void; onNext: () => void }) {
  return (
    <div className="scr">
      <Header step={2} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">Step 2 of 10</div>
      <h1 className="scr__title">Which conference?</h1>
      <p className="scr__sub">We'll plan around the dates and venue.</p>
      {CONFERENCES.map((c) => (
        <button
          key={c.id}
          className={`conf-card${value === c.id ? " active" : ""}`}
          onClick={() => onChange(c.id)}
        >
          <div className="conf-card__img" style={{ background: c.gradient }} />
          <div className="conf-card__body">
            <div className="conf-card__title">{c.name}</div>
            <div className="conf-card__meta">{c.meta}</div>
          </div>
          <div className="conf-card__radio" />
        </button>
      ))}
      <button className="btn-tertiary" style={{ alignSelf: "flex-start" }}>
        + Search for another conference
      </button>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function AttendanceStep({
  conf, value, onChange, onBack, onNext,
}: {
  conf: typeof CONFERENCES[number];
  value: Attendance | null;
  onChange: (v: Attendance) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const opts: { id: Attendance; title: string; desc: string; Icon: any }[] = [
    { id: "full", title: "Full attendance", desc: "All days — main stage and side events", Icon: Calendar },
    { id: "partial", title: "Partial — only some days", desc: "You'll pick which days next", Icon: CalendarDays },
    { id: "side-only", title: "Side events only", desc: "No main pass — focus on networking", Icon: Ban },
  ];
  return (
    <div className="scr">
      <Header step={3} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">{conf.name} · Step 3 of 10</div>
      <h1 className="scr__title">How are you attending?</h1>
      <p className="scr__sub">Lets us tune the schedule to your time on the ground.</p>
      {opts.map((o) => (
        <button
          key={o.id}
          className={`opt${value === o.id ? " active" : ""}`}
          onClick={() => onChange(o.id)}
        >
          <div className="opt__icon"><o.Icon /></div>
          <div className="opt__body">
            <div className="opt__title">{o.title}</div>
            <div className="opt__desc">{o.desc}</div>
          </div>
        </button>
      ))}
      <div className="scr__cta">
        <button className="btn-primary" disabled={!value} onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function DaysStep({
  conf, value, onChange, onBack, onNext,
}: {
  conf: typeof CONFERENCES[number];
  value: number[];
  onChange: (v: number[]) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const toggle = (n: number) => {
    onChange(value.includes(n) ? value.filter((x) => x !== n) : [...value, n]);
  };
  const days = conf.days.length ? conf.days : [
    { dow: "Mon", num: 1, enabled: true },
    { dow: "Tue", num: 2, enabled: true },
    { dow: "Wed", num: 3, enabled: true },
  ];
  const selected = days.filter((d) => value.includes(d.num));
  return (
    <div className="scr">
      <Header step={4} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">Step 4 of 10</div>
      <h1 className="scr__title">Which days are you in?</h1>
      <p className="scr__sub">Tap to select. We'll only suggest events on these days.</p>

      <div style={{
        fontSize: 11, fontWeight: 600, color: "var(--fg-muted)",
        marginBottom: 8, letterSpacing: "0.05em",
      }}>{conf.month}</div>
      <div className="days-row">
        {days.map((d) => (
          <button
            key={d.num}
            className={`day${value.includes(d.num) ? " active" : ""}${!d.enabled ? " disabled" : ""}`}
            onClick={() => d.enabled && toggle(d.num)}
            disabled={!d.enabled}
          >
            <span className="day__dow">{d.dow}</span>
            <span className="day__num">{String(d.num).padStart(2, "0")}</span>
          </button>
        ))}
      </div>
      <div style={{
        fontSize: 12, color: "var(--fg-muted)",
        padding: "12px 14px", background: "var(--bg-surface)",
        borderRadius: 10, display: "flex", gap: 8, alignItems: "center",
      }}>
        <Info size={14} style={{ color: "var(--fg-action)" }} />
        <span>
          {selected.length > 0 ? (
            <>You'll be in town for <strong style={{ color: "var(--fg-default)" }}>{selected.length} day{selected.length > 1 ? "s" : ""}</strong>
              {" · "}
              {selected.map((s) => s.dow).join(" & ")}
            </>
          ) : (
            "Select at least one day"
          )}
        </span>
      </div>

      <div className="scr__cta">
        <button className="btn-primary" disabled={value.length === 0} onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function RoleStep({
  value, onChange, onBack, onNext,
}: { value: Role | null; onChange: (v: Role) => void; onBack: () => void; onNext: () => void }) {
  return (
    <div className="scr">
      <Header step={5} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">Step 5 of 10</div>
      <h1 className="scr__title">Which best describes you?</h1>
      <p className="scr__sub">Pick one. You can always change it later in your profile.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {ROLES.map((r) => (
          <button
            key={r.id}
            className={`opt opt--vertical${value === r.id ? " active" : ""}`}
            onClick={() => onChange(r.id)}
          >
            <div className="opt__icon">{r.emoji}</div>
            <div>
              <div className="opt__title">{r.label}</div>
              <div className="opt__desc">{r.desc}</div>
            </div>
          </button>
        ))}
      </div>
      <div className="scr__cta">
        <button className="btn-primary" disabled={!value} onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function GoalsStep({
  role, value, onChange, onBack, onNext,
}: {
  role: Role | null;
  value: string[];
  onChange: (v: string[]) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const goals = role ? GOALS_BY_ROLE[role] : GOALS_BY_ROLE.founder;
  const roleLabel = role ? ROLES.find((r) => r.id === role)!.label : "you";
  const toggle = (id: string) => {
    if (value.includes(id)) {
      onChange(value.filter((x) => x !== id));
    } else if (value.length < 3) {
      onChange([...value, id]);
    }
  };
  return (
    <div className="scr">
      <Header step={6} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">Step 6 of 10</div>
      <h1 className="scr__title">As a {roleLabel}, what are you here to do?</h1>
      <p className="scr__sub">Pick up to 3 — order matters, top one weighs most.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
        {goals.map((g) => {
          const idx = value.indexOf(g.id);
          const active = idx >= 0;
          return (
            <button
              key={g.id}
              className={`opt opt--vertical${active ? " active" : ""}`}
              onClick={() => toggle(g.id)}
            >
              {active && <div className="opt__rank">{idx + 1}</div>}
              <div className="opt__icon">{g.emoji}</div>
              <div>
                <div className="opt__title">{g.label}</div>
                <div className="opt__desc">{g.desc}</div>
              </div>
            </button>
          );
        })}
      </div>
      <div style={{ fontSize: 12, color: "var(--fg-muted)", textAlign: "center" }}>
        {value.length} of 3 selected
      </div>
      <div className="scr__cta">
        <button className="btn-primary" disabled={value.length === 0} onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function TopicsStep({
  value, onChange, onBack, onSkip, onNext,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  onBack: () => void;
  onSkip: () => void;
  onNext: () => void;
}) {
  const toggle = (t: string) => {
    onChange(value.includes(t) ? value.filter((x) => x !== t) : [...value, t]);
  };
  return (
    <div className="scr">
      <Header step={7} total={TOTAL_STEPS} onBack={onBack} onSkip={onSkip} />
      <div className="scr__step-label">Step 7 of 10</div>
      <h1 className="scr__title">What topics interest you?</h1>
      <p className="scr__sub">Tap any number. We'll surface talks and people across these.</p>
      <div className="chip-grid">
        {TOPICS.map((t) => (
          <button
            key={t}
            className={`chip${value.includes(t) ? " active" : ""}`}
            onClick={() => toggle(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <div style={{ fontSize: 12, color: "var(--fg-muted)" }}>{value.length} selected</div>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>
          Continue{value.length > 0 ? ` (${value.length})` : ""}
        </button>
      </div>
    </div>
  );
}

function ScheduleStep({
  pace, energy, onChange, onBack, onSkip, onNext,
}: {
  pace: number;
  energy: number;
  onChange: (p: number, e: number) => void;
  onBack: () => void;
  onSkip: () => void;
  onNext: () => void;
}) {
  const paceLabel = pace < 25 ? "Relaxed" : pace < 55 ? "Selective" : pace < 80 ? "Balanced" : "Packed";
  const energyLabel = energy < 35 ? "Early bird" : energy < 70 ? "Mid-day" : "Night owl";
  const eventsPerDay = Math.round(3 + (pace / 100) * 6);
  const startTime = energy < 35 ? "8:00 AM" : energy < 70 ? "10:00 AM" : "12:00 PM";

  return (
    <div className="scr">
      <Header step={8} total={TOTAL_STEPS} onBack={onBack} onSkip={onSkip} />
      <div className="scr__step-label">Step 8 of 10</div>
      <h1 className="scr__title">How do you like to do conferences?</h1>
      <p className="scr__sub">Tune the pace. We'll match.</p>

      <div className="slider-block">
        <div className="slider-block__label"><span>Pace</span><strong>{paceLabel}</strong></div>
        <Slider value={pace} onChange={(v) => onChange(v, energy)} />
        <div className="slider-block__caps">
          <span>Relaxed (3–4 / day)</span><span>Packed (8+)</span>
        </div>
      </div>

      <div className="slider-block">
        <div className="slider-block__label"><span>Energy</span><strong>{energyLabel}</strong></div>
        <Slider value={energy} onChange={(v) => onChange(pace, v)} />
        <div className="slider-block__caps">
          <span>🌅 Mornings</span><span>Late nights 🌙</span>
        </div>
      </div>

      <div style={{
        marginTop: 8, padding: 14, borderRadius: 12,
        background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
        fontSize: 13, lineHeight: 1.5,
      }}>
        <span style={{ color: "var(--fg-muted)" }}>We'll plan you </span>
        <strong>~{eventsPerDay} events per day</strong>
        <span style={{ color: "var(--fg-muted)" }}>, starting around </span>
        <strong>{startTime}</strong>.
      </div>

      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function SocialStep({
  value, onChange, onBack, onSkip, onNext,
}: {
  value: number;
  onChange: (v: number) => void;
  onBack: () => void;
  onSkip: () => void;
  onNext: () => void;
}) {
  const styleTitle = value < 35 ? "Quality conversations" : value < 70 ? "Mix it up" : "Big rooms";
  const styleDesc =
    value < 35
      ? "We'll prioritize founder dinners, smaller meetups, and 1:1 intro requests over big mixers."
      : value < 70
      ? "A balance of mixers and intimate dinners — we'll alternate."
      : "We'll lean into big mixers, parties, and conference-wide socials.";
  return (
    <div className="scr">
      <Header step={9} total={TOTAL_STEPS} onBack={onBack} onSkip={onSkip} />
      <div className="scr__step-label">Step 9 of 10</div>
      <h1 className="scr__title">How do you like to network?</h1>
      <p className="scr__sub">Quality vs. quantity. Move the slider — no wrong answer.</p>
      <div style={{ marginTop: 8 }}>
        <div style={{
          display: "flex", justifyContent: "space-between", marginBottom: 16,
          fontSize: 12, color: "var(--fg-muted)",
        }}>
          <div style={{ textAlign: "center", maxWidth: 80 }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>🪴</div>Deep, fewer
          </div>
          <div style={{ textAlign: "center", maxWidth: 80 }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>🎉</div>Big rooms
          </div>
        </div>
        <Slider value={value} onChange={onChange} />
        <div style={{
          marginTop: 24, padding: 16, borderRadius: 14,
          background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
        }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
            textTransform: "uppercase", color: "var(--fg-muted)", marginBottom: 8,
          }}>Your style</div>
          <div style={{
            fontFamily: "var(--font-display)", fontWeight: 700,
            fontSize: 18, lineHeight: 1.2, marginBottom: 6,
          }}>{styleTitle}</div>
          <div style={{ fontSize: 13, color: "var(--fg-muted)", lineHeight: 1.5 }}>
            {styleDesc}
          </div>
        </div>
      </div>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function MustHavesStep({
  value, onChange, onBack, onSkip, onNext,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  onBack: () => void;
  onSkip: () => void;
  onNext: () => void;
}) {
  const [tab, setTab] = useState<"people" | "companies" | "speakers">("people");
  const [query, setQuery] = useState("");
  const add = (id: string) => {
    if (!value.includes(id)) onChange([...value, id]);
  };
  const remove = (id: string) => onChange(value.filter((x) => x !== id));
  const idToLabel = (id: string) => {
    const s = SUGGESTIONS.find((x) => x.id === id);
    return s ? s.name : id;
  };
  const idToGrad = (id: string) => SUGGESTIONS.find((x) => x.id === id)?.grad;
  const visibleSuggestions = SUGGESTIONS.filter(
    (s) => !value.includes(s.id) && s.name.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <div className="scr">
      <Header step={10} total={TOTAL_STEPS} onBack={onBack} onSkip={onSkip} />
      <div className="scr__step-label">Step 10 of 10</div>
      <h1 className="scr__title">Anyone you want to meet?</h1>
      <p className="scr__sub">
        People, speakers, or companies. We'll keep an eye out and ping you when paths cross.
      </p>
      <div className="seg-tabs">
        {(["people", "companies", "speakers"] as const).map((t) => (
          <button
            key={t}
            className={tab === t ? "on" : ""}
            onClick={() => setTab(t)}
          >
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>
      <div className="search">
        <Search />
        <input
          placeholder={`Search ${tab}…`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {value.length > 0 && (
        <div className="pill-list">
          {value.map((v) => (
            <span key={v} className="pill">
              <span className="av" style={idToGrad(v) ? { background: idToGrad(v) } : undefined} />
              {idToLabel(v)}
              <button className="x" onClick={() => remove(v)}><X size={12} /></button>
            </span>
          ))}
        </div>
      )}
      <div style={{
        fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
        textTransform: "uppercase", color: "var(--fg-subtle)", margin: "8px 0",
      }}>
        Suggested
      </div>
      <div className="suggest-list">
        {visibleSuggestions.map((s) => (
          <button key={s.id} className="suggest" onClick={() => add(s.id)}>
            <div className="suggest__av" style={s.grad ? { background: s.grad } : undefined}>
              {s.initials}
            </div>
            <div className="suggest__body">
              <div className="suggest__name">{s.name}</div>
              <div className="suggest__role">{s.role}</div>
            </div>
            <div className="suggest__add"><Plus /></div>
          </button>
        ))}
      </div>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>Build my schedule</button>
        <button className="btn-tertiary" onClick={onSkip}>Skip — no specific names</button>
      </div>
    </div>
  );
}

function ReviewStep({
  state, conf, onBack, onEdit, onNext,
}: {
  state: State;
  conf: typeof CONFERENCES[number];
  onBack: () => void;
  onEdit: (step: number) => void;
  onNext: () => void;
}) {
  const dayLabels = conf.days.filter((d) => state.days.includes(d.num)).map((d) => d.dow);
  const daysVal =
    state.attendance === "full"
      ? "All days"
      : dayLabels.length
      ? dayLabels.join(" & ")
      : "—";
  const role = state.role ? ROLES.find((r) => r.id === state.role)!.label : "—";
  const goals = state.goals
    .map((g) => GOALS_BY_ROLE[state.role || "founder"].find((x) => x.id === g)?.label)
    .filter(Boolean)
    .join(", ");
  const paceLabel = state.pace < 25 ? "Relaxed" : state.pace < 55 ? "Selective" : state.pace < 80 ? "Balanced" : "Packed";
  const energyLabel = state.energy < 35 ? "Mornings" : state.energy < 70 ? "Mid-day" : "Nights";
  const socialLabel = state.social < 35 ? "Quality" : state.social < 70 ? "Mixed" : "Big rooms";

  const rows: { Icon: any; label: string; val: string; step: number }[] = [
    { Icon: Calendar, label: "Conference · Days", val: `${conf.name} · ${daysVal}`, step: 1 },
    { Icon: UserIcon, label: "You", val: `${role}${goals ? ` · ${goals}` : ""}`, step: 4 },
    { Icon: Compass, label: "Topics", val: state.topics.length ? state.topics.join(", ") : "—", step: 6 },
    { Icon: Clock, label: "Style", val: `${paceLabel} · ${energyLabel} · ${socialLabel}`, step: 7 },
    { Icon: Star, label: "Must-haves", val: state.mustHaves.length ? `${state.mustHaves.length} ${state.mustHaves.length === 1 ? "person" : "people"}` : "—", step: 9 },
  ];

  return (
    <div className="scr">
      <Header step={10} total={TOTAL_STEPS} onBack={onBack} hideSkip />
      <div className="scr__step-label">Last step</div>
      <h1 className="scr__title">Look good?</h1>
      <p className="scr__sub">Tap any line to tweak before we build your plan.</p>
      <div className="review-list">
        {rows.map((r) => (
          <button key={r.label} className="review-row" onClick={() => onEdit(r.step)}>
            <div className="review-row__icon"><r.Icon /></div>
            <div className="review-row__body">
              <div className="review-row__label">{r.label}</div>
              <div className="review-row__val">{r.val}</div>
            </div>
            <span className="review-row__edit">Edit</span>
          </button>
        ))}
      </div>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onNext}>Curate my schedule</button>
      </div>
    </div>
  );
}

function Curating({ role }: { role: Role | null }) {
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setPhase((p) => Math.min(3, p + 1)), 800);
    return () => clearInterval(t);
  }, []);
  const steps = [
    "Pulled 384 events",
    "Matched to your goals",
    "Routing your days",
    "Picking people to meet",
  ];
  const roleLabel = role ? ROLES.find((r) => r.id === role)!.label.toLowerCase() : "professional";
  return (
    <div className="scr-load">
      <div className="scr-load__mark">
        <SQMark size={96} color="var(--fg-default)" />
      </div>
      <div className="scr-load__title">Building your schedule</div>
      <div className="scr-load__sub">
        A few seconds. We're picking the right talks for a {roleLabel}.
      </div>
      <ul className="scr-load__steps">
        {steps.map((s, i) => (
          <li
            key={s}
            className={`scr-load__step ${i < phase ? "done" : i === phase ? "cur" : ""}`}
          >
            <span className="dot" />
            {s}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Done({ conf, onRestart, onEnter }: { conf: typeof CONFERENCES[number]; onRestart: () => void; onEnter?: () => void }) {
  return (
    <div className="scr" style={{ paddingTop: 56 }}>
      <div style={{ marginBottom: 24 }}>
        <SQMark size={56} color="var(--fg-default)" />
      </div>
      <h1
        className="scr-done__title"
        style={{
          fontFamily: "var(--font-display)", fontWeight: 700,
          fontSize: 30, lineHeight: 1.1, letterSpacing: "-0.02em",
          marginBottom: 14,
        }}
      >
        Your <em>{conf.name.split(" ")[0]}</em> is ready.
      </h1>
      <p className="scr__sub" style={{ marginBottom: 24 }}>
        21 events across 2 days. 6 people on watch. Tweak anytime.
      </p>
      <div className="scr-stats">
        <div className="scr-stat">
          <div className="scr-stat__num">21</div>
          <div className="scr-stat__lbl">events curated</div>
        </div>
        <div className="scr-stat">
          <div className="scr-stat__num">6</div>
          <div className="scr-stat__lbl">people on watch</div>
        </div>
        <div className="scr-next">
          <div className="scr-next__lbl">Up next</div>
          <div className="scr-next__title">Stable Summit IV — 9:00 AM</div>
          <div className="scr-next__sub">Sheraton · 3 founders to meet</div>
        </div>
      </div>
      <div className="scr__cta">
        <button className="btn-primary" onClick={onEnter}>See my schedule</button>
        <button className="btn-tertiary" onClick={onRestart}>Restart onboarding</button>
      </div>
    </div>
  );
}
