import type { Role } from '../types'

export const ROLES: { id: Role; label: string; emoji: string; desc: string }[] = [
  { id: 'founder', label: 'Founder', emoji: '🚀', desc: 'Building, raising, hiring' },
  { id: 'investor', label: 'Investor', emoji: '💸', desc: 'Sourcing deals' },
  { id: 'developer', label: 'Developer', emoji: '⌨️', desc: 'Building, learning' },
  { id: 'marketer', label: 'Marketer', emoji: '📈', desc: 'Growth, BD, partners' },
  { id: 'corporate', label: 'Corporate', emoji: '🏢', desc: 'Enterprise, strategy' },
  { id: 'journalist', label: 'Journalist', emoji: '📰', desc: 'Covering, writing' },
]

export const GOALS_BY_ROLE: Record<Role, { id: string; label: string; emoji: string; desc: string }[]> = {
  founder: [
    { id: 'fundraising', label: 'Fundraising', emoji: '💸', desc: 'Meet investors' },
    { id: 'partnerships', label: 'Partnerships', emoji: '🤝', desc: 'Build relationships' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Meet new people' },
    { id: 'hiring', label: 'Hiring', emoji: '🎯', desc: 'Find talent' },
    { id: 'learning', label: 'Learning', emoji: '📚', desc: 'New tech, trends' },
    { id: 'deals', label: 'Closing deals', emoji: '💼', desc: 'Sales, contracts' },
  ],
  investor: [
    { id: 'deals', label: 'Deal flow', emoji: '💸', desc: 'Source startups' },
    { id: 'lps', label: 'LP meetings', emoji: '🤝', desc: 'Talk to backers' },
    { id: 'research', label: 'Research', emoji: '📚', desc: 'Themes & trends' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Other funds' },
    { id: 'branding', label: 'Brand', emoji: '📢', desc: 'Visibility' },
    { id: 'portfolio', label: 'Portfolio', emoji: '📈', desc: 'Help founders' },
  ],
  developer: [
    { id: 'learning', label: 'Learning', emoji: '📚', desc: 'New tools' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Other devs' },
    { id: 'hackathons', label: 'Hackathons', emoji: '⚡', desc: 'Build & ship' },
    { id: 'jobs', label: 'Job search', emoji: '💼', desc: 'Next role' },
    { id: 'open-source', label: 'Open source', emoji: '🌐', desc: 'Contributions' },
    { id: 'research', label: 'Research', emoji: '🔬', desc: 'Deep dives' },
  ],
  marketer: [
    { id: 'partnerships', label: 'Partnerships', emoji: '🤝', desc: 'BD pipeline' },
    { id: 'leads', label: 'Lead gen', emoji: '🎯', desc: 'Pipeline' },
    { id: 'branding', label: 'Brand', emoji: '📢', desc: 'Awareness' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Peers' },
    { id: 'learning', label: 'Learning', emoji: '📚', desc: 'Trends' },
    { id: 'press', label: 'Press', emoji: '📰', desc: 'Coverage' },
  ],
  corporate: [
    { id: 'scouting', label: 'Scouting', emoji: '🔍', desc: 'Innovation tech' },
    { id: 'partnerships', label: 'Partnerships', emoji: '🤝', desc: 'Strategic deals' },
    { id: 'learning', label: 'Learning', emoji: '📚', desc: 'Industry trends' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Peers' },
    { id: 'hiring', label: 'Hiring', emoji: '🎯', desc: 'Talent' },
    { id: 'branding', label: 'Brand', emoji: '📢', desc: 'Visibility' },
  ],
  journalist: [
    { id: 'stories', label: 'Stories', emoji: '📰', desc: 'Find leads' },
    { id: 'interviews', label: 'Interviews', emoji: '🎙️', desc: 'Speakers, founders' },
    { id: 'networking', label: 'Networking', emoji: '👋', desc: 'Sources' },
    { id: 'research', label: 'Research', emoji: '📚', desc: 'Beat coverage' },
    { id: 'press', label: 'Press events', emoji: '📢', desc: 'Announcements' },
    { id: 'scoops', label: 'Scoops', emoji: '⚡', desc: 'Exclusive news' },
  ],
}

export const TOPICS = [
  'AI / ML', 'DeFi', 'Stablecoins', 'L2s & Rollups', 'Infra',
  'Privacy / ZK', 'Trading', 'SaaS', 'Climate', 'Consumer',
  'RWA', 'Gaming', 'Mobile', 'Hardware', 'Bio / Health',
  'Security', 'DePIN', 'Open-source',
]
