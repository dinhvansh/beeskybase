#!/usr/bin/env bash
# v0.31.0 mock suite: FLUTTER STAGE 2 (the agent config app in
# Flutter + the unified installer, per docs/agent-app-mapping.md).
# This release changes NO Python behaviour — the core is the spec
# and stays untouched — so the sweep is the full regression set at
# its established counts: the vendor suite (the newest core suite)
# + the release-pin suite (mock_agent_bg_test under xvfb, now
# pinning 0.31.0 across __init__ + both .iss files) + standalone
# spot-checks (bridge, creds, groups, units, ops, ops2, inspect,
# pools). The new code is Dart: BOTH Flutter apps are verified
# locally this release (analyze + full test runs with the SDK at
# ~/workspace/flutter-sdk — main app 125, agent app 34); only
# their Windows builds remain CI-only. Both facts are disclosed
# in the v0.31.0 block of tests/RESULTS.md (written alongside
# this script, not appended by it).
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
for spec in "mock_vendors_test plain" "mock_agent_bg_test xvfb" \
            "mock_bridge_test plain" "mock_creds_test plain" \
            "mock_groups_test plain" "mock_units_test plain" \
            "mock_ops_test plain" "mock_ops2_test plain" \
            "mock_inspect_test plain" "mock_pools_test plain"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}\n"
done

echo
echo "Summary:"
printf '%s' "$SUMMARY_LINES"
