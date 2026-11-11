#!/usr/bin/env bash
# v0.30.0 mock suite: VENDOR COVERAGE (ported per
# docs/vendor-coverage-mapping.md — HashCore's per-vendor
# adapters dissected from the extracted Toolkit AOT pool).
# The new mock_vendors_test suite runs against two new
# dialect mocks built from the dissected contracts
# (tests/mock_whatsminer.py — the socket dialect with its
# fan-field fingerprint + token refusal; tests/mock_avalon.py
# — a cgminer-envelope Avalon) alongside the pre-existing
# dashd / stock / cgminer mocks, proving detection does not
# collide in either direction and the scanner never sends
# get_token.
#
# Evidence method (same standalone-sweep pattern as
# v0.21–v0.29): the new suite + the release-pin suite
# (mock_agent_bg_test under xvfb, pinning 0.30.0) +
# standalone regression spot-checks (bridge, creds, groups,
# units, ops, ops2, inspect, pools). The Flutter app IS
# verified locally this release (analyze + full test run
# with the SDK at ~/workspace/flutter-sdk); only its
# Windows build remains CI-only. Both facts are disclosed
# in the v0.30.0 block of tests/RESULTS.md (written
# alongside this script, not appended by it).
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
