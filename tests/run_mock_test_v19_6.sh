#!/usr/bin/env bash
# v0.19.6 mock suite: the suites affected by the target changes,
# run standalone (the historical chain is unchanged by this patch).
#   mock_targets_test.py    NEW — default_scan_target() with the
#                           socket layer stubbed (detect -> /24;
#                           failure / loopback / link-local /
#                           unspecified -> fallback, never raises),
#                           parse_targets() multi-range union
#                           (union, first-seen order, overlap
#                           de-dup, whitespace, mixed forms, cap on
#                           the union, one-bad-item rejection,
#                           single-spec unchanged), both desktop
#                           apps' pre-fills from the (stubbed)
#                           helper, CLI gui default plumbing, and
#                           comma targets reaching the scan/config
#                           unchanged.
#   mock_gui_test.py        subprocess GUI smoke, unchanged.
#   mock_agent_app_test.py  agent app suite (release-independent).
#   mock_agent_bg_test.py   carries the release pin 0.19.5 -> 0.19.6.
#   mock_theme_test.py      constructs both apps with defaults; the
#                           pre-fill must not disturb its assertions.
#   mock_rounded_test.py    untouched by this release; regression.
#   mock_glass_test.py      untouched by this release; regression.
# The v0.19.6 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

TARGETS_OUTPUT="$(xvfb-run -a python3 tests/mock_targets_test.py)"
echo "$TARGETS_OUTPUT"
GUI_OUTPUT="$(xvfb-run -a python3 tests/mock_gui_test.py)"
echo "$GUI_OUTPUT"
AGENT_APP_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_app_test.py)"
echo "$AGENT_APP_OUTPUT"
AGENT_BG_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_bg_test.py)"
echo "$AGENT_BG_OUTPUT"
THEME_OUTPUT="$(xvfb-run -a python3 tests/mock_theme_test.py)"
echo "$THEME_OUTPUT"
ROUNDED_OUTPUT="$(xvfb-run -a python3 tests/mock_rounded_test.py)"
echo "$ROUNDED_OUTPUT"
GLASS_OUTPUT="$(xvfb-run -a python3 tests/mock_glass_test.py)"
echo "$GLASS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.19.6 mock test — auto-detected default target + multi-range targets"
  echo
  echo "Field bug: on the owner's laptop the scan target defaulted to"
  echo "the hard-coded 192.168.1.0/24; his fleet is on 192.168.2.0/24,"
  echo "so the first sweep found 0 miners and the app read as broken."
  echo "And BTC Tools beside it scanned several /24 ranges at once."
  echo
  echo "v0.19.6 (beesky/core/discover.py, beesky/gui.py,"
  echo "beesky/cli.py, beesky/agent_gui.py, beesky/agent_app.py):"
  echo
  echo "  * New discover.default_scan_target(): the primary LAN"
  echo "    IPv4 via the UDP-connect trick (no packet is sent),"
  echo "    returned as its /24. Any failure, and loopback /"
  echo "    link-local / unspecified results, fall back to"
  echo "    192.168.1.0/24; the helper never raises."
  echo "  * The helper pre-fills the main GUI target (default_target"
  echo "    now None -> helper), the agent config window on first"
  echo "    run (no config file yet; a saved config still wins),"
  echo "    the main GUI's empty-field fallback in open_local_web,"
  echo "    and the CLI gui --target default (None -> helper)."
  echo "    Fields stay fully editable — pre-fill only."
  echo "  * parse_targets() now builds the multi-range union"
  echo "    explicitly: comma-separated items (IP / CIDR / range)"
  echo "    are parsed as before, de-duplicated preserving"
  echo "    first-seen order (each item expands ascending, so a"
  echo "    single spec yields exactly the list it always did),"
  echo "    and the MAX_HOSTS cap applies to the de-duplicated"
  echo "    union. One invalid item still rejects the whole spec."
  echo "    Help texts (CLI scan/watch/agent, agent window hint)"
  echo "    now say comma-separated mixes scan several ranges."
  echo
  echo "Changed test expectations: mock_agent_bg_test release pin"
  echo "0.19.5 -> 0.19.6 (plus __init__ and both .iss). New suite"
  echo "mock_targets_test.py; the real (unstubbed) subnet never"
  echo "leaks into an assertion — the helper is stubbed at each"
  echo "app's import seam and at the socket layer. No behaviour"
  echo "assertion was weakened. The updated suites:"
  echo
  echo '```'
  echo "$TARGETS_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$GUI_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$AGENT_APP_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$AGENT_BG_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$THEME_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$ROUNDED_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$GLASS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.19.6 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
