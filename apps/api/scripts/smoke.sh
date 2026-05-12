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

phase_4() {
  : "${SUPABASE_URL:?source apps/api/.env first}"
  HERE="$(cd "$(dirname "$0")" && pwd)"
  JWT=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py")

  echo "==> baseline: GET /api/me/schedule"
  BASE_IDS=$(curl -sf "$BASE/api/me/schedule" -H "authorization: Bearer $JWT" \
    | python3 -c "import sys,json; print(','.join(s['id'] for s in json.load(sys.stdin)['schedule']))")
  echo "  → $BASE_IDS"

  # Pick one curated event to hide (first one in the list) and one non-curated
  HIDE_ID=$(echo "$BASE_IDS" | cut -d',' -f1)
  ADD_ID=""
  for cand in t2049-e6 t2049-e8 t2049-e9 t2049-e10 t2049-e11 t2049-e12; do
    if ! echo ",$BASE_IDS," | grep -q ",$cand,"; then
      ADD_ID="$cand"; break
    fi
  done
  [ -n "$ADD_ID" ] || { echo "no non-curated event available to add" >&2; exit 1; }
  export HIDE_ID ADD_ID
  echo "==> will hide $HIDE_ID and add $ADD_ID"

  echo "==> POST /api/events/pin (hide $HIDE_ID)"
  curl -sf -X POST "$BASE/api/events/pin" \
    -H "authorization: Bearer $JWT" -H 'content-type: application/json' \
    -d "{\"event_id\":\"$HIDE_ID\",\"pinned\":false}" >/dev/null

  echo "==> POST /api/events/pin (add $ADD_ID)"
  curl -sf -X POST "$BASE/api/events/pin" \
    -H "authorization: Bearer $JWT" -H 'content-type: application/json' \
    -d "{\"event_id\":\"$ADD_ID\",\"pinned\":true}" >/dev/null

  echo "==> GET /api/me/schedule (after pins)"
  curl -sf "$BASE/api/me/schedule" -H "authorization: Bearer $JWT" \
    | python3 -c "
import sys,json,os
d = json.load(sys.stdin)
ids = [s['id'] for s in d['schedule']]
hide = os.environ['HIDE_ID']
add  = os.environ['ADD_ID']
assert hide not in ids, ('expected hidden', hide, ids)
assert add  in ids,     ('expected added',  add,  ids)
added = next(s for s in d['schedule'] if s['id']==add)
assert added['priority']=='must', added
print(f'  → {len(ids)} items; {hide} hidden, {add} added (priority={added[\"priority\"]})')
"

  echo "==> GET /api/me/events (pinned-only list)"
  curl -sf "$BASE/api/me/events" -H "authorization: Bearer $JWT" \
    | python3 -c "
import sys,json,os
items = json.load(sys.stdin)
ids = [e['id'] for e in items]
add = os.environ['ADD_ID']
assert ids == [add], (ids, add)
print(f'  → {ids}')
"

  echo
  echo "phase-4 OK"
}

phase_5() {
  : "${SUPABASE_URL:?source apps/api/.env first}"
  HERE="$(cd "$(dirname "$0")" && pwd)"

  ADMIN_JWT=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py" --admin --email "admin+sq@sidequest.local")
  USER_JWT=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py" --email "test+sq@sidequest.local")
  EVENT_ID="manual-smoke-$(date +%s)"
  export EVENT_ID
  echo "==> using event id $EVENT_ID"

  echo "==> non-admin user is rejected with 403"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/admin/events" -H "authorization: Bearer $USER_JWT")
  [ "$STATUS" = "403" ] || { echo "expected 403, got $STATUS" >&2; exit 1; }
  echo "  → 403 OK"

  echo "==> POST /api/admin/events (admin creates manual event)"
  curl -sf -X POST "$BASE/api/admin/events" \
    -H "authorization: Bearer $ADMIN_JWT" -H 'content-type: application/json' \
    -d "{\"id\":\"$EVENT_ID\",\"conference_id\":\"token2049\",\"title\":\"Smoke test side event\",\"starts_at\":\"2026-04-29T20:00:00+04:00\",\"ends_at\":\"2026-04-29T22:00:00+04:00\",\"venue\":\"Beach Club\",\"tags\":[\"Side Events\"]}" \
    | python3 -c "
import sys,json,os
d = json.load(sys.stdin)
assert d['id']==os.environ['EVENT_ID']
assert d['is_manual'] is True
assert d['locked'] is True
print(f'  → is_manual={d[\"is_manual\"]} locked={d[\"locked\"]}')
"

  echo "==> PATCH /api/admin/events/t2049-e3 (admin edits a scraped event)"
  curl -sf -X PATCH "$BASE/api/admin/events/t2049-e3" \
    -H "authorization: Bearer $ADMIN_JWT" -H 'content-type: application/json' \
    -d '{"venue":"Hand-corrected venue"}' \
    | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['venue']=='Hand-corrected venue'
assert d['locked'] is True
assert d['is_manual'] is False  # scraper origin
print(f'  → venue updated, locked flipped to true')
"

  echo "==> POST /api/admin/events/t2049-e3/lock (unlock back)"
  curl -sf -X POST "$BASE/api/admin/events/t2049-e3/lock" \
    -H "authorization: Bearer $ADMIN_JWT" -H 'content-type: application/json' \
    -d '{"locked":false}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['locked'] is False; print('  → locked=false')"

  echo "==> filter list: locked=true"
  curl -sf "$BASE/api/admin/events?conference_id=token2049&locked=true" \
    -H "authorization: Bearer $ADMIN_JWT" \
    | python3 -c "
import sys,json,os
items = json.load(sys.stdin)
ids = [e['id'] for e in items]
assert os.environ['EVENT_ID'] in ids, ('manual event missing', ids)
assert 't2049-e3' not in ids, ('e3 should be unlocked again', ids)
print(f'  → {len(ids)} locked events; manual present, e3 absent')
"

  echo "==> DELETE the manual event (cleanup)"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/api/admin/events/$EVENT_ID" -H "authorization: Bearer $ADMIN_JWT")
  [ "$STATUS" = "204" ] || { echo "expected 204, got $STATUS" >&2; exit 1; }
  echo "  → 204 deleted"

  # Restore the venue we corrupted on t2049-e3 for the next smoke run
  curl -sf -X PATCH "$BASE/api/admin/events/t2049-e3" \
    -H "authorization: Bearer $ADMIN_JWT" -H 'content-type: application/json' \
    -d '{"venue":"Main Stage"}' >/dev/null
  curl -sf -X POST "$BASE/api/admin/events/t2049-e3/lock" \
    -H "authorization: Bearer $ADMIN_JWT" -H 'content-type: application/json' \
    -d '{"locked":false}' >/dev/null

  echo
  echo "phase-5 OK"
}

phase_6() {
  : "${SUPABASE_URL:?source apps/api/.env first}"
  HERE="$(cd "$(dirname "$0")" && pwd)"
  JWT=$(uv run --project "$HERE/.." python "$HERE/mint_test_jwt.py")

  echo "==> POST /api/chat (SSE stream)"
  RESP=$(mktemp)
  curl -sN -X POST "$BASE/api/chat" \
    -H "authorization: Bearer $JWT" \
    -H 'content-type: application/json' \
    -d '{"messages":[{"role":"user","content":"In one short sentence: what is my highest priority event on day 1 and why?"}]}' \
    > "$RESP"

  python3 -c "
import sys, json
body = open('$RESP').read()
delta_count = 0
got_done = False
got_terminator = False
combined = []
for line in body.splitlines():
    if not line.startswith('data:'):
        continue
    data = line[5:].strip()
    if not data:
        continue
    if data == '[DONE]':
        got_terminator = True
        continue
    obj = json.loads(data)
    t = obj.get('type')
    if t == 'delta':
        delta_count += 1
        combined.append(obj.get('content',''))
    elif t == 'done':
        got_done = True
    elif t == 'error':
        print('ERROR FRAME:', obj.get('content'), file=sys.stderr)
        sys.exit(2)
assert delta_count >= 1, ('no delta frames', body[:400])
assert got_done, 'missing done frame'
assert got_terminator, 'missing [DONE] terminator'
text = ''.join(combined)
print(f'  → {delta_count} delta frames, done + [DONE] terminator received')
print(f'  → assistant: {text[:200]}')
"
  rm -f "$RESP"

  echo
  echo "phase-6 OK"
}

case "$PHASE" in
  phase-0) phase_0 ;;
  phase-1) phase_1 ;;
  phase-2) phase_2 ;;
  phase-3) phase_3 ;;
  phase-4) phase_4 ;;
  phase-5) phase_5 ;;
  phase-6) phase_6 ;;
  all) phase_0 && phase_1 && phase_2 && phase_3 && phase_4 && phase_5 && phase_6 ;;
  *)
    echo "unknown phase: $PHASE" >&2
    echo "available: phase-0..phase-6, all" >&2
    exit 2
    ;;
esac
