#!/usr/bin/env bash
# v0.33.0 mock suite: DOCS-BASED VENDOR ADAPTERS
# (docs/vendor-docs-mapping.md). New core surface: the Whatsminer
# token flow (md5crypt + privileged actions, G-W1 closed) and the
# LuxOS adapter (detection + reads + reboot/curtail) — the new
# suite mock_vendors2_test runs FIRST, then the full regression
# set at its established counts (the release-pin suite now pinning
# 0.33.0). Both Flutter apps are verified locally this release
# (analyze + full test runs with the SDK at ~/workspace/flutter-sdk
# — main app 141, agent app 34; the only Dart change is the LuxOS
# source label); their Windows builds remain CI-only.
# The v0.33.0 block of tests/RESULTS.md is written alongside this
# script, not appended by it.
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
for spec in "mock_views_test plain" "mock_vendors2_test plain" "mock_vendors_test plain" \
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
