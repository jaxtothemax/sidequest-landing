#!/usr/bin/env bash
# Phase-by-phase smoke tests against a running local API.
# Usage: ./scripts/smoke.sh phase-0
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
PHASE="${1:-phase-0}"

phase_0() {
  echo "==> GET $BASE/health"
  curl -sf "$BASE/health" | tee /dev/stderr | grep -q '"status":"ok"'
  echo
  echo "phase-0 OK"
}

phase_1() {
  echo "==> GET $BASE/api/conferences"
  COUNT=$(curl -sf "$BASE/api/conferences" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))")
  [ "$COUNT" -eq 3 ] || { echo "expected 3 conferences, got $COUNT" >&2; exit 1; }
  echo "  → $COUNT conferences"

  echo "==> GET $BASE/api/conferences/token2049"
  curl -sf "$BASE/api/conferences/token2049" | python3 -c "
import sys,json
c = json.load(sys.stdin)
assert c['name'] == 'TOKEN2049 Dubai', c
assert sorted(d['num'] for d in c['days'] if d['enabled']) == [29, 30]
print('  → name OK, days 29 & 30 enabled')
"

  echo "==> GET $BASE/api/conferences/token2049/events"
  EVCOUNT=$(curl -sf "$BASE/api/conferences/token2049/events" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))")
  [ "$EVCOUNT" -eq 12 ] || { echo "expected 12 events, got $EVCOUNT" >&2; exit 1; }
  echo "  → $EVCOUNT events"

  echo "==> 404 path"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/conferences/does-not-exist")
  [ "$STATUS" = "404" ] || { echo "expected 404, got $STATUS" >&2; exit 1; }
  echo "  → 404 OK"

  echo
  echo "phase-1 OK"
}

phase_2() {
  echo "==> POST $BASE/api/curate (real OpenRouter call — may take 10–30s)"
  ANON_ID="${ANON_ID:-$(uuidgen | tr 'A-Z' 'a-z')}"
  PAYLOAD=$(cat <<JSON
{
  "anon_id": "$ANON_ID",
  "onboarding": {
    "conferenceId": "token2049",
    "attendance": "partial",
    "days": [29, 30],
    "role": "founder",
    "goals": ["fundraising", "networking", "partnerships"],
    "topics": ["DeFi", "AI / ML", "Stablecoins"],
    "pace": 50,
    "energy": 60,
    "social": 70,
    "mustHaves": ["a16zcrypto", "hayden"]
  }
}
JSON
)
  RESP=$(curl -sf -X POST "$BASE/api/curate" -H 'content-type: application/json' -d "$PAYLOAD")
  echo "$RESP" | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['curate_id'], d
assert isinstance(d['schedule'], list), d
assert len(d['schedule']) >= 1, ('schedule empty', d)
print(f'  → curate_id={d[\"curate_id\"][:8]}…  schedule_len={len(d[\"schedule\"])}  tokens={d[\"tokens_used\"]}')
print(f'  → first event: {d[\"schedule\"][0][\"event_id\"]}  priority={d[\"schedule\"][0][\"priority\"]}')
print(f'    rationale: {d[\"schedule\"][0][\"rationale\"][:120]}')
"
  echo
  echo "phase-2 OK"
}

phase_3() {
  : "${SUPABASE_URL:?SUPABASE_URL not set (source apps/api/.env first)}"
  : "${SUPABASE_SERVICE_KEY:?SUPABASE_SERVICE_KEY not set}"

  HERE="$(cd "$(dirname "$0")" && pwd)"
  JWT=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py")
  USER_ID=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py" --user-id-only)
  echo "==> minted JWT for $USER_ID"

  ANON_ID=$(uuidgen | tr 'A-Z' 'a-z')
  PAYLOAD=$(cat <<JSON
{"anon_id":"$ANON_ID","onboarding":{"conferenceId":"token2049","attendance":"partial","days":[29,30],"role":"founder","goals":["fundraising"],"topics":["DeFi"],"pace":40,"energy":60,"social":50,"mustHaves":[]}}
JSON
)

  echo "==> POST /api/curate (real LLM call)"
  curl -sf -X POST "$BASE/api/curate" -H 'content-type: application/json' -d "$PAYLOAD" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['curate_id']==\"$ANON_ID\"; assert len(d['schedule'])>=1; print(f'  → schedule_len={len(d[\"schedule\"])}  tokens={d[\"tokens_used\"]}')"

  echo "==> POST /api/auth/claim"
  curl -sf -X POST "$BASE/api/auth/claim" \
    -H "authorization: Bearer $JWT" -H 'content-type: application/json' \
    -d "{\"anon_id\":\"$ANON_ID\"}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['ok']; print(f'  → user_curation_id={d[\"user_curation_id\"][:8]}…')"

  echo "==> POST /api/auth/claim (idempotent reject)"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/claim" \
    -H "authorization: Bearer $JWT" -H 'content-type: application/json' \
    -d "{\"anon_id\":\"$ANON_ID\"}")
  [ "$STATUS" = "409" ] || { echo "expected 409 on re-claim, got $STATUS" >&2; exit 1; }
  echo "  → 409 OK"

  echo "==> POST /api/unlock"
  curl -sf -X POST "$BASE/api/unlock" -H "authorization: Bearer $JWT" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['unlocked']; print('  → unlocked=true')"

  echo "==> GET /api/me/schedule"
  curl -sf "$BASE/api/me/schedule" -H "authorization: Bearer $JWT" \
    | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['conference_id']=='token2049', d
assert len(d['schedule'])>=1, d
first = d['schedule'][0]
for k in ('id','title','start','rationale','priority','inSchedule'):
    assert k in first, (k, first)
print(f'  → {len(d[\"schedule\"])} items; first={first[\"title\"]!r} priority={first[\"priority\"]}')
"

  echo "==> reject unauthenticated /api/me/schedule"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/me/schedule")
  [ "$STATUS" = "401" ] || { echo "expected 401, got $STATUS" >&2; exit 1; }
  echo "  → 401 OK"

  echo
  echo "phase-3 OK"
}

case "$PHASE" in
  phase-0) phase_0 ;;
  phase-1) phase_1 ;;
  phase-2) phase_2 ;;
  phase-3) phase_3 ;;
  all) phase_0 && phase_1 && phase_2 && phase_3 ;;
  *)
    echo "unknown phase: $PHASE" >&2
    echo "available: phase-0, phase-1, phase-2, phase-3, all" >&2
    exit 2
    ;;
esac
