-- Seed the three conferences. Only TOKEN2049 Dubai (29–30 Apr 2026) is fleshed out;
-- the other two are stubs so the conference picker has options to display.

insert into conferences (id, name, city, venue, start_date, end_date, timezone, meta) values
  ('token2049', 'TOKEN2049 Dubai',    'Dubai',   'Madinat Jumeirah', '2026-04-29', '2026-04-30', 'Asia/Dubai',
    jsonb_build_object('gradient', 'linear-gradient(135deg, #FFD072, #E62C5A)', 'meta_short', '29 Apr – 30 Apr · Madinat Jumeirah', 'month', 'APRIL 2026')),
  ('ethglobal', 'ETHGlobal Bangkok',  'Bangkok', 'QSNCC',            '2026-05-15', '2026-05-18', 'Asia/Bangkok',
    jsonb_build_object('gradient', 'linear-gradient(135deg, #6088F7, #1E4EB0)', 'meta_short', '15 May – 18 May · QSNCC', 'month', 'MAY 2026')),
  ('consensus', 'Consensus Toronto',  'Toronto', 'MTCC',             '2026-06-10', '2026-06-13', 'America/Toronto',
    jsonb_build_object('gradient', 'linear-gradient(135deg, #FF8C9E, #C61E4A)', 'meta_short', '10 Jun – 13 Jun · MTCC',     'month', 'JUNE 2026'))
on conflict (id) do nothing;

-- TOKEN2049 days (the picker shows a wider window so attendees can mark side-event days too)
insert into conference_days (conference_id, day_num, dow, date, enabled) values
  ('token2049', 26, 'Sun', '2026-04-26', false),
  ('token2049', 27, 'Mon', '2026-04-27', false),
  ('token2049', 28, 'Tue', '2026-04-28', false),
  ('token2049', 29, 'Wed', '2026-04-29', true),
  ('token2049', 30, 'Thu', '2026-04-30', true),
  ('token2049',  1, 'Fri', '2026-05-01', false),
  ('token2049',  2, 'Sat', '2026-05-02', false)
on conflict (conference_id, day_num) do nothing;

-- TOKEN2049 seed events — all times in Asia/Dubai (UTC+4). Stored as timestamptz.
insert into events (id, conference_id, title, description, starts_at, ends_at, venue, tags, attendees, source) values
  ('t2049-e1',  'token2049', 'Stable Summit IV',                'The flagship gathering for stablecoin builders, with talks from founders shipping at scale.', '2026-04-29 09:00:00+04', '2026-04-29 11:00:00+04', 'Sheraton · Mina A''Salam',  array['Founders'],  320,  'seed'),
  ('t2049-e2',  'token2049', 'Investor Coffee — Seed Stage',    'Curated 1:1 round-robin between founders and seed-stage funds.',                              '2026-04-29 11:30:00+04', '2026-04-29 12:30:00+04', 'Madinat · Al Qasr Lobby',   array['Investors'], 80,   'seed'),
  ('t2049-e3',  'token2049', 'DeFi Liquidity Panel',            'Top market makers and protocol leads on liquidity in the next cycle.',                       '2026-04-29 14:00:00+04', '2026-04-29 15:00:00+04', 'Main Stage',                array['DeFi'],      600,  'seed'),
  ('t2049-e4',  'token2049', 'Token2049 Mainstage Keynote',     'The mainstage keynote setting the tone for the conference.',                                 '2026-04-29 16:00:00+04', '2026-04-29 17:00:00+04', 'Main Stage',                array['Keynote'],   1200, 'seed'),
  ('t2049-e5',  'token2049', 'Founders & Funds Rooftop',        'Quality networking under Dubai skyline. Limited capacity.',                                  '2026-04-29 19:30:00+04', '2026-04-29 23:00:00+04', 'Five Palm · Rooftop',       array['Mixer'],     220,  'seed'),
  ('t2049-e6',  'token2049', 'AI x Crypto Workshop',            'Hands-on builder session on agentic on-chain workflows.',                                    '2026-04-30 09:30:00+04', '2026-04-30 11:30:00+04', 'Joharah Ballroom',          array['Workshop'],  150,  'seed'),
  ('t2049-e7',  'token2049', 'Gulf Capital LP Lunch',           'Invite-only LP/GP lunch hosted by regional family offices.',                                 '2026-04-30 12:30:00+04', '2026-04-30 14:00:00+04', 'Pierchic',                  array['Investors'], 60,   'seed'),
  ('t2049-e8',  'token2049', 'Layer 2 Scaling Roundtable',      'L2 leads compare notes on throughput, fees, and rollup direction.',                          '2026-04-30 15:00:00+04', '2026-04-30 16:00:00+04', 'Stage B',                   array['Tech'],      200,  'seed'),
  ('t2049-e9',  'token2049', 'Closing Yacht Party',             'The unofficial closing party. Boarding starts at 8pm sharp.',                                '2026-04-30 20:00:00+04', '2026-05-01 01:00:00+04', 'Dubai Harbour · Marina',    array['Party'],     400,  'seed'),
  ('t2049-e10', 'token2049', 'Builders Breakfast — Bitcoin DeFi','Small-format breakfast with Bitcoin DeFi protocol founders.',                                '2026-04-30 08:00:00+04', '2026-04-30 09:15:00+04', 'Bahri Bar',                 array['Founders'],  50,   'seed'),
  ('t2049-e11', 'token2049', 'Press & Media Hour',              'Open hour for journalists to meet founders.',                                                '2026-04-29 13:00:00+04', '2026-04-29 14:00:00+04', 'Press Lounge',              array['Press'],     90,   'seed'),
  ('t2049-e12', 'token2049', 'MENA Regulators Fireside',        'VARA leadership on the future of MENA crypto policy.',                                       '2026-04-30 10:00:00+04', '2026-04-30 11:00:00+04', 'Main Stage',                array['Policy'],    800,  'seed')
on conflict (id) do nothing;

-- Suggestions (people, companies, speakers) — all attached to TOKEN2049 for v1.
insert into conference_suggestions (id, conference_id, kind, name, role) values
  ('stani',        'token2049', 'people', 'Stani Kulechov',    'Founder · Aave'),
  ('rune',         'token2049', 'people', 'Rune Christensen',  'Founder · Sky / MakerDAO'),
  ('hayden',       'token2049', 'people', 'Hayden Adams',      'Founder · Uniswap'),
  ('sandeep',      'token2049', 'people', 'Sandeep Nailwal',   'Co-founder · Polygon'),
  ('jesse',        'token2049', 'people', 'Jesse Pollak',      'Creator · Base'),
  ('kain',         'token2049', 'people', 'Kain Warwick',      'Founder · Infinex'),
  ('andre',        'token2049', 'people', 'Andre Cronje',      'Founder · Sonic Labs'),
  ('tarun',        'token2049', 'people', 'Tarun Chitra',      'Founder · Gauntlet'),
  ('sam-k',        'token2049', 'people', 'Sam Kazemian',      'Founder · Frax Finance'),
  ('sreeram',      'token2049', 'people', 'Sreeram Kannan',    'Founder · EigenLayer'),
  ('mustafa',      'token2049', 'people', 'Mustafa Al-Bassam', 'Co-founder · Celestia'),
  ('robert-l',     'token2049', 'people', 'Robert Leshner',    'Founder · Superstate'),
  ('hasu',         'token2049', 'people', 'Hasu',              'Strategy Lead · Flashbots'),
  ('tom-s',        'token2049', 'people', 'Tom Shaughnessy',   'Founder · Delphi Digital'),
  ('coinbase',     'token2049', 'companies', 'Coinbase',          'Public exchange · L2 (Base)'),
  ('binance',      'token2049', 'companies', 'Binance',           'Global exchange'),
  ('a16zcrypto',   'token2049', 'companies', 'a16z crypto',       'Crypto VC fund'),
  ('paradigm',     'token2049', 'companies', 'Paradigm',          'Research-driven crypto fund'),
  ('variant',      'token2049', 'companies', 'Variant Fund',      'Early-stage Web3 fund'),
  ('multicoin',    'token2049', 'companies', 'Multicoin Capital', 'Thesis-driven fund'),
  ('pantera',      'token2049', 'companies', 'Pantera Capital',   'Crypto fund'),
  ('dragonfly',    'token2049', 'companies', 'Dragonfly',         'Crypto fund'),
  ('galaxy',       'token2049', 'companies', 'Galaxy Digital',    'Digital asset financial services'),
  ('circle',       'token2049', 'companies', 'Circle',            'USDC issuer'),
  ('tether',       'token2049', 'companies', 'Tether',            'USDT issuer'),
  ('lido',         'token2049', 'companies', 'Lido',              'Liquid staking on Ethereum'),
  ('ef',           'token2049', 'companies', 'Ethereum Foundation','Non-profit · Ethereum'),
  ('solana-fnd',   'token2049', 'companies', 'Solana Foundation', 'Non-profit · Solana'),
  ('polygon-labs', 'token2049', 'companies', 'Polygon Labs',      'Polygon ecosystem'),
  ('chainlink-l',  'token2049', 'companies', 'Chainlink Labs',    'Oracle network'),
  ('uniswap-l',    'token2049', 'companies', 'Uniswap Labs',      'DEX protocol'),
  ('fireblocks',   'token2049', 'companies', 'Fireblocks',        'Institutional custody'),
  ('anchorage',    'token2049', 'companies', 'Anchorage Digital', 'Federally chartered crypto bank'),
  ('ledger',       'token2049', 'companies', 'Ledger',            'Hardware wallets'),
  ('magic-eden',   'token2049', 'companies', 'Magic Eden',        'Multi-chain NFT marketplace'),
  ('phantom',      'token2049', 'companies', 'Phantom',           'Multi-chain wallet'),
  ('flashbots',    'token2049', 'companies', 'Flashbots',         'MEV research'),
  ('eigenlayer',   'token2049', 'companies', 'EigenLayer',        'Restaking on Ethereum'),
  ('celestia',     'token2049', 'companies', 'Celestia',          'Modular DA layer'),
  ('sui-fnd',      'token2049', 'companies', 'Sui Foundation',    'Sui blockchain'),
  ('aptos-l',      'token2049', 'companies', 'Aptos Labs',        'Aptos blockchain'),
  ('vitalik',      'token2049', 'speakers', 'Vitalik Buterin',    'Co-founder · Ethereum'),
  ('cz',           'token2049', 'speakers', 'Changpeng Zhao',     'Founder · Binance'),
  ('anatoly',      'token2049', 'speakers', 'Anatoly Yakovenko',  'Co-founder · Solana'),
  ('armstrong',    'token2049', 'speakers', 'Brian Armstrong',    'CEO · Coinbase'),
  ('arthur',       'token2049', 'speakers', 'Arthur Hayes',       'Founder · Maelstrom'),
  ('novogratz',    'token2049', 'speakers', 'Mike Novogratz',     'CEO · Galaxy Digital'),
  ('allaire',      'token2049', 'speakers', 'Jeremy Allaire',     'CEO · Circle'),
  ('ardoino',      'token2049', 'speakers', 'Paolo Ardoino',      'CEO · Tether'),
  ('cobie',        'token2049', 'speakers', 'Cobie',              'Host · UpOnly / Lightspeed'),
  ('shin',         'token2049', 'speakers', 'Laura Shin',         'Host · Unchained'),
  ('russo',        'token2049', 'speakers', 'Camila Russo',       'Founder · The Defiant'),
  ('voorhees',     'token2049', 'speakers', 'Erik Voorhees',      'Founder · ShapeShift'),
  ('lubin',        'token2049', 'speakers', 'Joseph Lubin',       'Founder · Consensys'),
  ('balaji',       'token2049', 'speakers', 'Balaji Srinivasan',  'Investor / author'),
  ('raoul',        'token2049', 'speakers', 'Raoul Pal',          'Founder · Real Vision')
on conflict (id) do nothing;
