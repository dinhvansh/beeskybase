#!/usr/bin/env bash
# v0.21.0 mock suite: scan/sysinfo JSON bridge + Flutter stage 1.
#
# Evidence method (this release, same standalone-sweep pattern as
# v0.20 — the nested historical chain halts mid-run in this
# sandbox): the NEW mock_bridge_test in full, plus standalone
# regression spot-checks on the suites nearest the cli.py change
# (units, cloud, web) and the release-pin suite (agent_bg, under
# xvfb like the sweeps before it). The Flutter app itself cannot
# be built in this sandbox (the Flutter tool's own pub update
# fails through the sandbox egress proxy — see the RESULTS.md
# block); its verification is CI (.github/workflows/
# build-flutter.yml) plus a local SDK parser pass over the Dart
# sources, both disclosed in the block this script appends.
set -uo pipefail
cd "$(dirname "$0")/.."

run_suite() {  # name, mode(plain|xvfb)
  local name="$1" mode="${2:-plain}"
  case "$mode" in
    xvfb) xvfb-run -a python3 "tests/$name.py" ;;
    *)    python3 "tests/$name.py" ;;
  esac
}

BRIDGE_OUTPUT="$(run_suite mock_bridge_test)"; echo "$BRIDGE_OUTPUT"

summary_line() {
  local out passes fails
  out="$(run_suite "$1" "${2:-plain}")"
  passes="$(printf '%s\n' "$out" | grep -c '^PASS')"
  fails="$(printf '%s\n' "$out" | grep -c '^FAIL')"
  echo "$1: $passes PASS / $fails FAIL (standalone)"
}

SUMMARY_LINES=""
for spec in "mock_units_test plain" "mock_cloud_test plain" \
            "mock_web_test plain" "mock_agent_bg_test xvfb"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

{
  echo
  echo "---"
  echo
  echo "# v0.21.0 — Flutter main app (stage 1) + scan/sysinfo JSON bridge"
  echo
  echo "The owner chose the full Flutter rewrite of the desktop"
  echo "apps (the Tk UI compared unfavourably with the HashCore"
  echo "Toolkit's Flutter UI). Stage 1: the Python core stays the"
  echo "only engine; a new Flutter shell (app_flutter/) drives the"
  echo "beesky CLI exe as a sidecar. The Tk apps are untouched and"
  echo "keep shipping as the fallback."
  echo
  echo "Bridge (beesky/cli.py):"
  echo
  echo "  * \`scan --json\` with no value (or \`-\`) is bridge mode:"
  echo "    stdout is exactly ONE JSON document"
  echo "    {\"records\": [...], \"scanned\": N, \"found\": M,"
  echo "    \"elapsed_s\": X}; ticket notes go to stderr there."
  echo "    \`--json FILE\` keeps its legacy behaviour byte-for-"
  echo "    byte. Records are the very dicts the agent/cloud path"
  echo "    serialises (wire key \`problems\`; native rate_value /"
  echo "    rate_unit since v0.20) — no second schema. A bridge-"
  echo "    only _jsonable() sanitiser coerces tuples/sets/other"
  echo "    non-JSON values rather than touching the record"
  echo "    builders."
  echo "  * \`sysinfo --json\`: {\"version\": ..., \"default_target\":"
  echo "    default_scan_target()} so the shell pre-fills the"
  echo "    target without reimplementing subnet detection."
  echo "  * Release pins bumped to 0.21.0 (__init__, both .iss,"
  echo "    mock_agent_bg_test)."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * mock_bridge_test — 24 assertions: stdout purity (the"
  echo "    whole stdout json.loads), envelope keys, scanned=254"
  echo "    for a /24, L9 14.54 MH/s + Z15 1101 ksol/s intact,"
  echo "    sanitiser coercions, --json does not swallow the next"
  echo "    flag, bridge+--tickets keeps stdout pure, legacy file"
  echo "    mode unchanged, sysinfo stubbed + live, and an end-to-"
  echo "    end subprocess scan against mock_dashd. Full output:"
  echo
  echo '```'
  echo "$BRIDGE_OUTPUT"
  echo '```'
  echo
  echo "  * Regression spot-checks at the v0.21.0 code:"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "  * Flutter SDK 3.47.9 (Dart 3.13.7) was fetched and runs"
  echo "    on this VM; every Dart source (lib/ + test/) passes"
  echo "    the SDK's own parser/formatter (dart format: 7 files,"
  echo "    no parse errors), and the windows/ scaffold was"
  echo "    rendered from that SDK's flutter-create templates."
  echo
  echo "(b) VERIFIED ONLY BY CI (.github/workflows/"
  echo "build-flutter.yml — sibling workflow, independent job, so"
  echo "the Tk release assets publish regardless):"
  echo
  echo "  * flutter pub get / test / build windows --release on"
  echo "    a real Windows runner, and the release asset"
  echo "    BeeSkyFlutter-<tag>-win64.zip. Local \`flutter create\`"
  echo "    /\`pub get\` could NOT run in this sandbox: the Flutter"
  echo "    tool's own package update stalls/fails through the"
  echo "    sandbox's authenticated egress proxy (curl to pub.dev"
  echo "    succeeds; the Dart pub client does not complete), so"
  echo "    \`flutter analyze\` and \`flutter test\` are likewise"
  echo "    CI-verified, not locally verified. The Dart widget/"
  echo "    unit tests are written against the same mock fleet as"
  echo "    the Python bridge test."
  echo
  echo "(c) KNOWINGLY NOT YET WIRED (stage 1):"
  echo
  echo "  * No Flutter installer yet — the CI zip is the runner"
  echo "    folder; beesky.exe must sit beside beesky_app.exe."
  echo "  * Export tickets shells \`scan --tickets\` (a second"
  echo "    scan pass — there is no records->tickets verb; TODO"
  echo "    marked in sidecar.dart). Open-web shells \`serve\` +"
  echo "    the OS browser opener (TODO: url_launcher)."
  echo "  * The Flutter app covers scan/stats/table/detail/"
  echo "    tickets/web for ONE local pass; heat map, cloud views"
  echo "    and the Agent app are later stages. Self-update"
  echo "    signing stays inert (owner key setup outstanding,"
  echo "    as since v0.10)."
} >> tests/RESULTS.md

echo
echo "V0.21.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
