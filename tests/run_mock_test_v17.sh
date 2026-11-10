#!/usr/bin/env bash
# v0.17 full mock suite: everything from v0.16 (v0.1..v0.16), then
# the rounded-corner test.
#   run_mock_test_v16.sh       regenerates tests/RESULTS.md (v0.1..v0.16)
#   mock_rounded_test.py       the v0.17 overhaul: radius tokens
#                              (16/12/999) in ui_theme AND as CSS
#                              custom properties in both web
#                              dashboards (no pre-token literal
#                              border-radius left); RoundedButton
#                              (click fires, release-outside cancels,
#                              Return/Space fire when focused, focus
#                              ring drawn, disabled never fires —
#                              click or invoke(), ttk-style
#                              configure/cget); RoundedEntry
#                              (textvariable round-trip, show="*"
#                              mask + configure(show="") unmask,
#                              accent outline on focus, .entry
#                              exposed); ui_theme.card() is a
#                              RoundedCard (still a ttk.Frame, title
#                              findable by tree walk, surface drawn);
#                              RoundedPill recolours via set_pill;
#                              both real windows construct with the
#                              swapped widgets in place.
# The v0.17 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v16.sh

ROUNDED_OUTPUT="$(xvfb-run -a python3 tests/mock_rounded_test.py)"
echo "$ROUNDED_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.17 mock test — rounded-corner overhaul (UI/UX Pro Max tokens)"
  echo
  echo "\`beesky/rounded.py\` renders the design system's rounded"
  echo "surfaces on tk.Canvas (ttk has no border-radius): RoundedCard"
  echo "(16px, a ttk.Frame whose surface is a canvas-drawn rounded"
  echo "rect — ui_theme.card() is reimplemented on it with the same"
  echo "signature and return contract), RoundedButton (12px, >= 36px"
  echo "tall, hover lightens / press darkens / release-outside"
  echo "cancels / accent focus ring / Return+Space activates /"
  echo "disabled never fires, with ttk-style configure/cget/invoke),"
  echo "RoundedEntry (12px frame, flat hosted tk.Entry, outline"
  echo "turns accent on focus, configure/cget delegate entry options"
  echo "such as show), RoundedPill (full-round, replaces the square"
  echo "label pill behind ui_theme.status_pill/set_pill). Both"
  echo "desktop apps use them for every card (incl. the four stat"
  echo "cards), every button and every form entry; the Treeview and"
  echo "detail text stay square inside their rounded cards. The web"
  echo "dashboards carry the same scale as CSS tokens"
  echo "(--radius-card 16px / --radius-widget 12px /"
  echo "--radius-pill 999px) with every pre-token literal radius"
  echo "mapped onto them. Adapted assertion: mock_agent_bg_test's"
  echo "version-sync pin moved 0.16.0 -> 0.17.0 with the release"
  echo "bump (same pin-update every release makes); no behaviour"
  echo "assertion was weakened — the ttk-specific widget assertions"
  echo "in the v0.14/v0.15/v0.16 suites (key_entry.cget('show'),"
  echo "autostart_button.cget('state'), pill cget('text'/'bg'),"
  echo "tree-walk labels) all pass unchanged against the rounded"
  echo "widgets' compatible APIs. The new suite adds:"
  echo
  echo '```'
  echo "$ROUNDED_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.17 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
