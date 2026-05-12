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

case "$PHASE" in
  phase-0) phase_0 ;;
  phase-1) phase_1 ;;
  all) phase_0 && phase_1 ;;
  *)
    echo "unknown phase: $PHASE" >&2
    echo "available: phase-0, phase-1, all" >&2
    exit 2
    ;;
esac
