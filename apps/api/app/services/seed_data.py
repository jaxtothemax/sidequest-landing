"""
In-memory mirror of supabase/migrations/0002_seed_token2049.sql.

Used by the InMemoryCatalogRepo when Supabase isn't configured (local dev,
tests, demos). Keep this in sync with the SQL seed.
"""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

DUBAI = timezone(timedelta(hours=4))


def _dt(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=DUBAI)


CONFERENCES: list[dict] = [
    {
        "id": "token2049",
        "name": "TOKEN2049 Dubai",
        "city": "Dubai",
        "venue": "Madinat Jumeirah",
        "start_date": date(2026, 4, 29),
        "end_date": date(2026, 4, 30),
        "timezone": "Asia/Dubai",
        "meta": {
            "gradient": "linear-gradient(135deg, #FFD072, #E62C5A)",
            "meta_short": "29 Apr – 30 Apr · Madinat Jumeirah",
            "month": "APRIL 2026",
        },
    },
    {
        "id": "ethglobal",
        "name": "ETHGlobal Bangkok",
        "city": "Bangkok",
        "venue": "QSNCC",
        "start_date": date(2026, 5, 15),
        "end_date": date(2026, 5, 18),
        "timezone": "Asia/Bangkok",
        "meta": {
            "gradient": "linear-gradient(135deg, #6088F7, #1E4EB0)",
            "meta_short": "15 May – 18 May · QSNCC",
            "month": "MAY 2026",
        },
    },
    {
        "id": "consensus",
        "name": "Consensus Toronto",
        "city": "Toronto",
        "venue": "MTCC",
        "start_date": date(2026, 6, 10),
        "end_date": date(2026, 6, 13),
        "timezone": "America/Toronto",
        "meta": {
            "gradient": "linear-gradient(135deg, #FF8C9E, #C61E4A)",
            "meta_short": "10 Jun – 13 Jun · MTCC",
            "month": "JUNE 2026",
        },
    },
]

CONFERENCE_DAYS: list[dict] = [
    {"conference_id": "token2049", "day_num": 26, "dow": "Sun", "date": date(2026, 4, 26), "enabled": False},
    {"conference_id": "token2049", "day_num": 27, "dow": "Mon", "date": date(2026, 4, 27), "enabled": False},
    {"conference_id": "token2049", "day_num": 28, "dow": "Tue", "date": date(2026, 4, 28), "enabled": False},
    {"conference_id": "token2049", "day_num": 29, "dow": "Wed", "date": date(2026, 4, 29), "enabled": True},
    {"conference_id": "token2049", "day_num": 30, "dow": "Thu", "date": date(2026, 4, 30), "enabled": True},
    {"conference_id": "token2049", "day_num": 1,  "dow": "Fri", "date": date(2026, 5, 1),  "enabled": False},
    {"conference_id": "token2049", "day_num": 2,  "dow": "Sat", "date": date(2026, 5, 2),  "enabled": False},
]

EVENTS: list[dict] = [
    {"id": "t2049-e1",  "conference_id": "token2049", "title": "Stable Summit IV",                 "description": "The flagship gathering for stablecoin builders, with talks from founders shipping at scale.", "starts_at": _dt(2026, 4, 29,  9, 0),  "ends_at": _dt(2026, 4, 29, 11, 0),  "venue": "Sheraton · Mina A'Salam",  "tags": ["Founders"],   "attendees": 320},
    {"id": "t2049-e2",  "conference_id": "token2049", "title": "Investor Coffee — Seed Stage",     "description": "Curated 1:1 round-robin between founders and seed-stage funds.",                              "starts_at": _dt(2026, 4, 29, 11, 30), "ends_at": _dt(2026, 4, 29, 12, 30), "venue": "Madinat · Al Qasr Lobby",  "tags": ["Investors"],  "attendees": 80},
    {"id": "t2049-e3",  "conference_id": "token2049", "title": "DeFi Liquidity Panel",             "description": "Top market makers and protocol leads on liquidity in the next cycle.",                       "starts_at": _dt(2026, 4, 29, 14, 0),  "ends_at": _dt(2026, 4, 29, 15, 0),  "venue": "Main Stage",               "tags": ["DeFi"],       "attendees": 600},
    {"id": "t2049-e4",  "conference_id": "token2049", "title": "Token2049 Mainstage Keynote",      "description": "The mainstage keynote setting the tone for the conference.",                                 "starts_at": _dt(2026, 4, 29, 16, 0),  "ends_at": _dt(2026, 4, 29, 17, 0),  "venue": "Main Stage",               "tags": ["Keynote"],    "attendees": 1200},
    {"id": "t2049-e5",  "conference_id": "token2049", "title": "Founders & Funds Rooftop",         "description": "Quality networking under Dubai skyline. Limited capacity.",                                  "starts_at": _dt(2026, 4, 29, 19, 30), "ends_at": _dt(2026, 4, 29, 23, 0),  "venue": "Five Palm · Rooftop",      "tags": ["Mixer"],      "attendees": 220},
    {"id": "t2049-e6",  "conference_id": "token2049", "title": "AI x Crypto Workshop",             "description": "Hands-on builder session on agentic on-chain workflows.",                                    "starts_at": _dt(2026, 4, 30,  9, 30), "ends_at": _dt(2026, 4, 30, 11, 30), "venue": "Joharah Ballroom",         "tags": ["Workshop"],   "attendees": 150},
    {"id": "t2049-e7",  "conference_id": "token2049", "title": "Gulf Capital LP Lunch",            "description": "Invite-only LP/GP lunch hosted by regional family offices.",                                 "starts_at": _dt(2026, 4, 30, 12, 30), "ends_at": _dt(2026, 4, 30, 14, 0),  "venue": "Pierchic",                 "tags": ["Investors"],  "attendees": 60},
    {"id": "t2049-e8",  "conference_id": "token2049", "title": "Layer 2 Scaling Roundtable",       "description": "L2 leads compare notes on throughput, fees, and rollup direction.",                          "starts_at": _dt(2026, 4, 30, 15, 0),  "ends_at": _dt(2026, 4, 30, 16, 0),  "venue": "Stage B",                  "tags": ["Tech"],       "attendees": 200},
    {"id": "t2049-e9",  "conference_id": "token2049", "title": "Closing Yacht Party",              "description": "The unofficial closing party. Boarding starts at 8pm sharp.",                                "starts_at": _dt(2026, 4, 30, 20, 0),  "ends_at": _dt(2026, 5,  1,  1, 0),  "venue": "Dubai Harbour · Marina",   "tags": ["Party"],      "attendees": 400},
    {"id": "t2049-e10", "conference_id": "token2049", "title": "Builders Breakfast — Bitcoin DeFi","description": "Small-format breakfast with Bitcoin DeFi protocol founders.",                                "starts_at": _dt(2026, 4, 30,  8, 0),  "ends_at": _dt(2026, 4, 30,  9, 15), "venue": "Bahri Bar",                "tags": ["Founders"],   "attendees": 50},
    {"id": "t2049-e11", "conference_id": "token2049", "title": "Press & Media Hour",               "description": "Open hour for journalists to meet founders.",                                                "starts_at": _dt(2026, 4, 29, 13, 0),  "ends_at": _dt(2026, 4, 29, 14, 0),  "venue": "Press Lounge",             "tags": ["Press"],      "attendees": 90},
    {"id": "t2049-e12", "conference_id": "token2049", "title": "MENA Regulators Fireside",         "description": "VARA leadership on the future of MENA crypto policy.",                                       "starts_at": _dt(2026, 4, 30, 10, 0),  "ends_at": _dt(2026, 4, 30, 11, 0),  "venue": "Main Stage",               "tags": ["Policy"],     "attendees": 800},
]
