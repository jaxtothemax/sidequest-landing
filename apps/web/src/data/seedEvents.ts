/**
 * Local fallback / offline fixture used when the API hasn't been reached yet.
 * Real schedule data comes from `/api/events` (scraper-populated).
 */
export type SeedEvent = {
  id: string
  title: string
  day: number
  start: string
  end: string
  venue: string
  tag: string
  attendees: number
  match: number
  inSchedule: boolean
  desc: string
}

export const SEED_EVENTS: SeedEvent[] = [
  { id: 'e1',  title: 'Stable Summit IV',                day: 29, start: '9:00 AM',  end: '11:00 AM', venue: "Sheraton · Mina A'Salam", tag: 'Founders',  attendees: 320,  match: 96, inSchedule: true,  desc: 'The flagship gathering for stablecoin builders, with talks from founders shipping at scale.' },
  { id: 'e2',  title: 'Investor Coffee — Seed Stage',    day: 29, start: '11:30 AM', end: '12:30 PM', venue: 'Madinat · Al Qasr Lobby', tag: 'Investors', attendees: 80,   match: 92, inSchedule: true,  desc: 'Curated 1:1 round-robin between founders and seed-stage funds.' },
  { id: 'e3',  title: 'DeFi Liquidity Panel',            day: 29, start: '2:00 PM',  end: '3:00 PM',  venue: 'Main Stage',              tag: 'DeFi',      attendees: 600,  match: 88, inSchedule: true,  desc: 'Top market makers and protocol leads on liquidity in the next cycle.' },
  { id: 'e4',  title: 'Token2049 Mainstage Keynote',     day: 29, start: '4:00 PM',  end: '5:00 PM',  venue: 'Main Stage',              tag: 'Keynote',   attendees: 1200, match: 84, inSchedule: true,  desc: 'The mainstage keynote setting the tone for the conference.' },
  { id: 'e5',  title: 'Founders & Funds Rooftop',        day: 29, start: '7:30 PM',  end: '11:00 PM', venue: 'Five Palm · Rooftop',     tag: 'Mixer',     attendees: 220,  match: 91, inSchedule: true,  desc: 'Quality networking under Dubai skyline. Limited capacity.' },
  { id: 'e6',  title: 'AI x Crypto Workshop',            day: 30, start: '9:30 AM',  end: '11:30 AM', venue: 'Joharah Ballroom',        tag: 'Workshop',  attendees: 150,  match: 78, inSchedule: false, desc: 'Hands-on builder session on agentic on-chain workflows.' },
  { id: 'e7',  title: 'Gulf Capital LP Lunch',           day: 30, start: '12:30 PM', end: '2:00 PM',  venue: 'Pierchic',                tag: 'Investors', attendees: 60,   match: 89, inSchedule: true,  desc: 'Invite-only LP/GP lunch hosted by regional family offices.' },
  { id: 'e8',  title: 'Layer 2 Scaling Roundtable',      day: 30, start: '3:00 PM',  end: '4:00 PM',  venue: 'Stage B',                 tag: 'Tech',      attendees: 200,  match: 73, inSchedule: false, desc: 'L2 leads compare notes on throughput, fees, and rollup direction.' },
  { id: 'e9',  title: 'Closing Yacht Party',             day: 30, start: '8:00 PM',  end: '1:00 AM',  venue: 'Dubai Harbour · Marina',  tag: 'Party',     attendees: 400,  match: 80, inSchedule: true,  desc: 'The unofficial closing party. Boarding starts at 8pm sharp.' },
  { id: 'e10', title: 'Builders Breakfast — Bitcoin DeFi', day: 30, start: '8:00 AM',  end: '9:15 AM',  venue: 'Bahri Bar',               tag: 'Founders',  attendees: 50,   match: 81, inSchedule: false, desc: 'Small-format breakfast with Bitcoin DeFi protocol founders.' },
  { id: 'e11', title: 'Press & Media Hour',              day: 29, start: '1:00 PM',  end: '2:00 PM',  venue: 'Press Lounge',            tag: 'Press',     attendees: 90,   match: 60, inSchedule: false, desc: 'Open hour for journalists to meet founders.' },
  { id: 'e12', title: 'MENA Regulators Fireside',        day: 30, start: '10:00 AM', end: '11:00 AM', venue: 'Main Stage',              tag: 'Policy',    attendees: 800,  match: 70, inSchedule: false, desc: 'VARA leadership on the future of MENA crypto policy.' },
]
