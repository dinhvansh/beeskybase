#!/usr/bin/env bash
# v0.32.0 mock suite: THE FIVE REMAINING VIEWS + THE SIDECAR FIX
# (docs/views-mapping.md). New core surface: the read-only
# `beesky tickets --dir … --json` verb and `scan --events-state`
# (mock_views_test, 20 assertions) — the sweep runs it FIRST,
# then the full regression set at its established counts (the
# release-pin suite now pinning 0.32.0). The views themselves
# and the missing-sidecar failure mode are Dart: BOTH Flutter
# apps are verified locally this release (analyze + full test
# runs with the SDK at ~/workspace/flutter-sdk — main app 141,
# agent app 34); their Windows builds remain CI-only, and the
# self-contained-zip staging lives in build-flutter.yml (CI).
# Both facts are disclosed in the v0.32.0 block of
# tests/RESULTS.md (written alongside this script, not appended
# by it).
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
for spec in "mock_views_test plain" "mock_vendors_test plain" \
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
