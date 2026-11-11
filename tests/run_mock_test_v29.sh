#!/usr/bin/env bash
# v0.29.0 mock suite: THE VNISH OPS TAIL (ported per
# docs/vnish-ops-mapping.md — the spec is dashd's own
# api-doc.json). The new mock_ops2_test suite runs against
# the extended contract mock (tests/mock_dashd.py now serves
# the tail endpoints and records the winning auth kind per
# hit, so request SHAPE is asserted, not just success).
#
# Evidence method (same standalone-sweep pattern as
# v0.21–v0.28): the new suite + the release-pin suite
# (mock_agent_bg_test under xvfb, pinning 0.29.0) +
# standalone regression spot-checks (bridge, creds, groups,
# units, ops, inspect, pools). The Flutter app IS verified
# locally this release (analyze + full test run with the
# SDK at ~/workspace/flutter-sdk); only its Windows build
# remains CI-only. Both facts are disclosed in the v0.29.0
# block of tests/RESULTS.md (written alongside this
# script, not appended by it).
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
for spec in "mock_ops2_test plain" "mock_agent_bg_test xvfb" \
            "mock_bridge_test plain" "mock_creds_test plain" \
            "mock_groups_test plain" "mock_units_test plain" \
            "mock_ops_test plain" "mock_inspect_test plain" \
            "mock_pools_test plain"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}\n"
done

echo
echo "Summary:"
printf '%s' "$SUMMARY_LINES"
