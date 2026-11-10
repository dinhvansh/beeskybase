#!/usr/bin/env bash
# v0.19.7 mock suite: the suites affected by the first-run view
# fixes, run standalone (the historical chain is unchanged by
# this patch).
#   mock_gui_test.py        subprocess GUI smoke, EXTENDED: after
#                           a scan with results the first row is
#                           auto-selected and the detail pane
#                           shows that miner; an empty scan (new
#                           phase, target 127.0.0.2 before the
#                           mock starts) keeps the placeholder and
#                           no selection; the window geometry is
#                           asserted screen-fitted + centred.
#   mock_theme_test.py      calls show_records directly — the
#                           landing must NOT live there; its
#                           stats/tag assertions are unchanged.
#   mock_rounded_test.py    untouched by this release; regression.
#   mock_glass_test.py      untouched by this release; regression.
#   mock_agent_app_test.py  agent app suite (release-independent).
#   mock_agent_bg_test.py   carries the release pin 0.19.6 ->
#                           0.19.7.
#   mock_targets_test.py    untouched by this release; regression.
# The v0.19.7 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

GUI_OUTPUT="$(xvfb-run -a python3 tests/mock_gui_test.py)"
echo "$GUI_OUTPUT"
THEME_OUTPUT="$(xvfb-run -a python3 tests/mock_theme_test.py)"
echo "$THEME_OUTPUT"
ROUNDED_OUTPUT="$(xvfb-run -a python3 tests/mock_rounded_test.py)"
echo "$ROUNDED_OUTPUT"
GLASS_OUTPUT="$(xvfb-run -a python3 tests/mock_glass_test.py)"
echo "$GLASS_OUTPUT"
AGENT_APP_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_app_test.py)"
echo "$AGENT_APP_OUTPUT"
AGENT_BG_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_bg_test.py)"
echo "$AGENT_BG_OUTPUT"
TARGETS_OUTPUT="$(xvfb-run -a python3 tests/mock_targets_test.py)"
echo "$TARGETS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.19.7 mock test — auto-select first miner + window fits the screen"
  echo
  echo "Field reports from the owner's first real fleet scan"
  echo "(63 miners found on 192.168.2.0/24): (1) after the scan"
  echo "nothing was selected, so the detail pane kept its"
  echo "placeholder and he concluded details could not be viewed;"
  echo "(2) the fixed 1120x880 window was taller than his"
  echo "laptop's usable screen (Windows scaling), the bottom sank"
  echo "under the taskbar and the flexible table row collapsed"
  echo "to about one visible row."
  echo
  echo "v0.19.7 (beesky/gui.py only):"
  echo
  echo "  * _poll_queue's records branch now calls _land_on_first"
  echo "    after show_records: with >= 1 row it selects + focuses"
  echo "    the first row, scrolls it into view and fills the"
  echo "    detail pane through the same _on_select path a click"
  echo "    uses. The rows were just rebuilt, so the selection can"
  echo "    never point at a dead row. With 0 rows it restores the"
  echo "    DETAIL_PLACEHOLDER text instead of leaving a previous"
  echo "    scan's detail on screen. show_records itself is"
  echo "    unchanged — it is also called directly by the theme"
  echo "    test, where no landing is wanted."
  echo "  * _fit_window replaces the fixed center_window call:"
  echo "    size = min(1120, screen_w - 32) x min(880,"
  echo "    screen_h - 72), centred ((sw-w)/2, (sh-h)/2); the"
  echo "    min size (940, 720) now tracks the cap so it cannot"
  echo "    fight it on a small screen. On the default Xvfb"
  echo "    screen (1280x1024) the window is exactly 1120x880 at"
  echo "    +80+72; verified manually on a 1500x1100 screen too:"
  echo "    exactly 1120x880 at +190+110."
  echo "  * gui --smoke additionally prints the post-scan"
  echo "    selection, the detail pane's first line and the fitted"
  echo "    geometry (screen size included) for the test."
  echo
  echo "Changed test expectations: mock_gui_test gains an"
  echo "empty-scan phase (127.0.0.2, exit 1 as before; selection"
  echo "'-' and the placeholder intact) and asserts selection ="
  echo "first row, detail = first miner (not the placeholder),"
  echo "and geometry = the fitted formula, centred within 2px"
  echo "and fully on screen. mock_agent_bg_test release pin"
  echo "0.19.6 -> 0.19.7 (plus __init__ and both .iss). No"
  echo "behaviour assertion was weakened. The updated suites:"
  echo
  echo '```'
  echo "$GUI_OUTPUT"
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
  echo "$TARGETS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.19.7 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
