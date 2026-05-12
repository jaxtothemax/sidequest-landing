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

case "$PHASE" in
  phase-0) phase_0 ;;
  *)
    echo "unknown phase: $PHASE" >&2
    echo "available: phase-0" >&2
    exit 2
    ;;
esac
