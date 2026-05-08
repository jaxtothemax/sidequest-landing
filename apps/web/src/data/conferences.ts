export type Conference = {
  id: string
  name: string
  meta: string
  gradient: string
  days: { dow: string; num: number; enabled: boolean }[]
  month: string
}

export const CONFERENCES: Conference[] = [
  {
    id: 'token2049',
    name: 'TOKEN2049 Dubai',
    meta: '29 Apr – 30 Apr · Madinat Jumeirah',
    gradient: 'linear-gradient(135deg, #FFD072, #E62C5A)',
    days: [
      { dow: 'Sun', num: 26, enabled: false },
      { dow: 'Mon', num: 27, enabled: false },
      { dow: 'Tue', num: 28, enabled: false },
      { dow: 'Wed', num: 29, enabled: true },
      { dow: 'Thu', num: 30, enabled: true },
      { dow: 'Fri', num: 1, enabled: false },
      { dow: 'Sat', num: 2, enabled: false },
    ],
    month: 'APRIL 2026',
  },
  {
    id: 'ethglobal',
    name: 'ETHGlobal Bangkok',
    meta: '15 May – 18 May · QSNCC',
    gradient: 'linear-gradient(135deg, #6088F7, #1E4EB0)',
    days: [],
    month: 'MAY 2026',
  },
  {
    id: 'consensus',
    name: 'Consensus Toronto',
    meta: '10 Jun – 13 Jun · MTCC',
    gradient: 'linear-gradient(135deg, #FF8C9E, #C61E4A)',
    days: [],
    month: 'JUNE 2026',
  },
]
