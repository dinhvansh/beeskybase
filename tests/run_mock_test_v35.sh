#!/usr/bin/env bash
# v0.35.0 regression runner (docs/unlock-payload-mapping.md, docs/parity-audit.md).
# New surface: the unlock-payload research record (no code — the race
# attempt count is now documented as 10, recovered) and the audit's two
# small closable gaps — group descriptions (core + app) and MAC
# enrichment from the local ARP table (core arp.py + CLI wiring).
# The new suite mock_arp_test runs FIRST, then the full regression
# set at its established counts.
# Flutter apps are verified separately (analyze + full test runs with
# the SDK at ~/workspace/flutter-sdk — main app 159 + groups
# description assertions, agent app 34); their Windows builds remain
# CI-only.
set -uo pipefail
cd "$(dirname "$0")/.."

run_suite() {  # name, mode(plain|xvfb)
  local name="$1" mode="${2:-plain}"
  case "$mode" in
    xvfb) xvfb-run -a python3 "tests/$name.py" ;;
    *)    python3 "tests/$name.py" ;;
  esac
}

summary_line() {
  local out passes fails
  out="$(run_suite "$1" "${2:-plain}")"
  passes="$(printf '%s\n' "$out" | grep -c '^PASS')"
  fails="$(printf '%s\n' "$out" | grep -c '^FAIL')"
  echo "$1: $passes PASS / $fails FAIL (standalone)"
}

SUMMARY_LINES=""
for spec in "mock_arp_test plain" "mock_ipreport_test plain" \
            "mock_views_test plain" "mock_vendors2_test plain" \
            "mock_vendors_test plain" \
            "mock_agent_bg_test xvfb" \
            "mock_bridge_test plain" "mock_creds_test plain" \
            "mock_groups_test plain" "mock_units_test plain" \
            "mock_ops_test plain" "mock_ops2_test plain" \
            "mock_inspect_test plain" "mock_pools_test plain" \
            "mock_agent_app_test xvfb"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}\n"
done

echo
echo "Summary:"
printf '%s' "$SUMMARY_LINES"
