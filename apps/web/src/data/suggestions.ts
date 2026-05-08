export type SuggestionKind = 'people' | 'companies' | 'speakers'

export type Suggestion = {
  id: string
  kind: SuggestionKind
  initials: string
  name: string
  role: string
  grad?: string
}

export const SUGGESTIONS: Suggestion[] = [
  /* people */
  { id: 'stani',    kind: 'people', initials: 'SK', name: 'Stani Kulechov',    role: 'Founder · Aave' },
  { id: 'rune',     kind: 'people', initials: 'RC', name: 'Rune Christensen',  role: 'Founder · Sky / MakerDAO', grad: 'linear-gradient(135deg, #6088F7, #1E4EB0)' },
  { id: 'hayden',   kind: 'people', initials: 'HA', name: 'Hayden Adams',      role: 'Founder · Uniswap',         grad: 'linear-gradient(135deg, #FF8C9E, #C61E4A)' },
  { id: 'sandeep',  kind: 'people', initials: 'SN', name: 'Sandeep Nailwal',   role: 'Co-founder · Polygon',      grad: 'linear-gradient(135deg, #8247E5, #B19CD9)' },
  { id: 'jesse',    kind: 'people', initials: 'JP', name: 'Jesse Pollak',      role: 'Creator · Base',            grad: 'linear-gradient(135deg, #0052FF, #4285F4)' },
  { id: 'kain',     kind: 'people', initials: 'KW', name: 'Kain Warwick',      role: 'Founder · Infinex' },
  { id: 'andre',    kind: 'people', initials: 'AC', name: 'Andre Cronje',      role: 'Founder · Sonic Labs' },
  { id: 'tarun',    kind: 'people', initials: 'TC', name: 'Tarun Chitra',      role: 'Founder · Gauntlet' },
  { id: 'sam-k',    kind: 'people', initials: 'SK', name: 'Sam Kazemian',      role: 'Founder · Frax Finance' },
  { id: 'sreeram',  kind: 'people', initials: 'SK', name: 'Sreeram Kannan',    role: 'Founder · EigenLayer' },
  { id: 'mustafa',  kind: 'people', initials: 'MA', name: 'Mustafa Al-Bassam', role: 'Co-founder · Celestia' },
  { id: 'robert-l', kind: 'people', initials: 'RL', name: 'Robert Leshner',    role: 'Founder · Superstate' },
  { id: 'hasu',     kind: 'people', initials: 'Hs', name: 'Hasu',              role: 'Strategy Lead · Flashbots' },
  { id: 'tom-s',    kind: 'people', initials: 'TS', name: 'Tom Shaughnessy',   role: 'Founder · Delphi Digital' },

  /* companies */
  { id: 'coinbase',     kind: 'companies', initials: 'Cb', name: 'Coinbase',          role: 'Public exchange · L2 (Base)', grad: 'linear-gradient(135deg, #0052FF, #4285F4)' },
  { id: 'binance',      kind: 'companies', initials: 'Bn', name: 'Binance',           role: 'Global exchange',              grad: 'linear-gradient(135deg, #F0B90B, #FCD535)' },
  { id: 'a16zcrypto',   kind: 'companies', initials: 'a16', name: 'a16z crypto',      role: 'Crypto VC fund' },
  { id: 'paradigm',     kind: 'companies', initials: 'Pa', name: 'Paradigm',          role: 'Research-driven crypto fund' },
  { id: 'variant',      kind: 'companies', initials: 'Va', name: 'Variant Fund',      role: 'Early-stage Web3 fund' },
  { id: 'multicoin',    kind: 'companies', initials: 'Mc', name: 'Multicoin Capital', role: 'Thesis-driven fund' },
  { id: 'pantera',      kind: 'companies', initials: 'Pn', name: 'Pantera Capital',   role: 'Crypto fund' },
  { id: 'dragonfly',    kind: 'companies', initials: 'Df', name: 'Dragonfly',         role: 'Crypto fund' },
  { id: 'galaxy',       kind: 'companies', initials: 'Gx', name: 'Galaxy Digital',    role: 'Digital asset financial services' },
  { id: 'circle',       kind: 'companies', initials: 'Ci', name: 'Circle',            role: 'USDC issuer' },
  { id: 'tether',       kind: 'companies', initials: 'Te', name: 'Tether',            role: 'USDT issuer' },
  { id: 'lido',         kind: 'companies', initials: 'Li', name: 'Lido',              role: 'Liquid staking on Ethereum' },
  { id: 'ef',           kind: 'companies', initials: 'EF', name: 'Ethereum Foundation', role: 'Non-profit · Ethereum',     grad: 'linear-gradient(135deg, #627EEA, #8A92B2)' },
  { id: 'solana-fnd',   kind: 'companies', initials: 'SF', name: 'Solana Foundation', role: 'Non-profit · Solana',          grad: 'linear-gradient(135deg, #9945FF, #14F195)' },
  { id: 'polygon-labs', kind: 'companies', initials: 'PL', name: 'Polygon Labs',      role: 'Polygon ecosystem',            grad: 'linear-gradient(135deg, #8247E5, #B19CD9)' },
  { id: 'chainlink-l',  kind: 'companies', initials: 'CL', name: 'Chainlink Labs',    role: 'Oracle network',               grad: 'linear-gradient(135deg, #375BD2, #4F89E0)' },
  { id: 'uniswap-l',    kind: 'companies', initials: 'UL', name: 'Uniswap Labs',      role: 'DEX protocol',                 grad: 'linear-gradient(135deg, #FF007A, #FF66A6)' },
  { id: 'fireblocks',   kind: 'companies', initials: 'Fb', name: 'Fireblocks',        role: 'Institutional custody' },
  { id: 'anchorage',    kind: 'companies', initials: 'An', name: 'Anchorage Digital', role: 'Federally chartered crypto bank' },
  { id: 'ledger',       kind: 'companies', initials: 'Le', name: 'Ledger',            role: 'Hardware wallets' },
  { id: 'magic-eden',   kind: 'companies', initials: 'ME', name: 'Magic Eden',        role: 'Multi-chain NFT marketplace' },
  { id: 'phantom',      kind: 'companies', initials: 'Ph', name: 'Phantom',           role: 'Multi-chain wallet' },
  { id: 'flashbots',    kind: 'companies', initials: 'Fl', name: 'Flashbots',         role: 'MEV research' },
  { id: 'eigenlayer',   kind: 'companies', initials: 'El', name: 'EigenLayer',        role: 'Restaking on Ethereum' },
  { id: 'celestia',     kind: 'companies', initials: 'Ce', name: 'Celestia',          role: 'Modular DA layer' },
  { id: 'sui-fnd',      kind: 'companies', initials: 'Su', name: 'Sui Foundation',    role: 'Sui blockchain' },
  { id: 'aptos-l',      kind: 'companies', initials: 'Ap', name: 'Aptos Labs',        role: 'Aptos blockchain' },

  /* speakers */
  { id: 'vitalik',   kind: 'speakers', initials: 'VB', name: 'Vitalik Buterin',   role: 'Co-founder · Ethereum',     grad: 'linear-gradient(135deg, #627EEA, #4B60B8)' },
  { id: 'cz',        kind: 'speakers', initials: 'CZ', name: 'Changpeng Zhao',    role: 'Founder · Binance',          grad: 'linear-gradient(135deg, #F0B90B, #FCD535)' },
  { id: 'anatoly',   kind: 'speakers', initials: 'AY', name: 'Anatoly Yakovenko', role: 'Co-founder · Solana',        grad: 'linear-gradient(135deg, #9945FF, #14F195)' },
  { id: 'armstrong', kind: 'speakers', initials: 'BA', name: 'Brian Armstrong',   role: 'CEO · Coinbase',             grad: 'linear-gradient(135deg, #0052FF, #4285F4)' },
  { id: 'arthur',    kind: 'speakers', initials: 'AH', name: 'Arthur Hayes',      role: 'Founder · Maelstrom' },
  { id: 'novogratz', kind: 'speakers', initials: 'MN', name: 'Mike Novogratz',    role: 'CEO · Galaxy Digital' },
  { id: 'allaire',   kind: 'speakers', initials: 'JA', name: 'Jeremy Allaire',    role: 'CEO · Circle' },
  { id: 'ardoino',   kind: 'speakers', initials: 'PA', name: 'Paolo Ardoino',     role: 'CEO · Tether' },
  { id: 'cobie',     kind: 'speakers', initials: 'Co', name: 'Cobie',             role: 'Host · UpOnly / Lightspeed' },
  { id: 'shin',      kind: 'speakers', initials: 'LS', name: 'Laura Shin',        role: 'Host · Unchained' },
  { id: 'russo',     kind: 'speakers', initials: 'CR', name: 'Camila Russo',      role: 'Founder · The Defiant' },
  { id: 'voorhees',  kind: 'speakers', initials: 'EV', name: 'Erik Voorhees',     role: 'Founder · ShapeShift' },
  { id: 'lubin',     kind: 'speakers', initials: 'JL', name: 'Joseph Lubin',      role: 'Founder · Consensys' },
  { id: 'balaji',    kind: 'speakers', initials: 'BS', name: 'Balaji Srinivasan', role: 'Investor / author' },
  { id: 'raoul',     kind: 'speakers', initials: 'RP', name: 'Raoul Pal',         role: 'Founder · Real Vision' },
]
