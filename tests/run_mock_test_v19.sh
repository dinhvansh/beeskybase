#!/usr/bin/env bash
# v0.19 full mock suite: everything from v0.18 (v0.1..v0.18), then
# the table-beautification evidence.
#   run_mock_test_v18.sh       regenerates tests/RESULTS.md (v0.1..v0.18)
#   mock_theme_test.py         updated for v0.19: Treeview
#                              background pin moved PANEL ->
#                              TABLE_WELL (#121216), new exact pins
#                              for the Treeview border colours
#                              (pinned to the well so no light clam
#                              frame can render), the TABLE_HEADING
#                              (#1D1D24) heading strip + its
#                              border, the dark scrollbar (BORDER
#                              thumb, TABLE_WELL trough/border) and
#                              the three table tokens; new row-tag
#                              assertions (odd OK row carries the
#                              zebra "odd" tag, CHECK row keeps
#                              its "check" wash tag, no zebra).
#   mock_gui_test.py           the subprocess GUI smoke, unchanged
#                              assertions — the beautified table
#                              still reports the same rows/values.
# The v0.19 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v18.sh

THEME_OUTPUT="$(xvfb-run -a python3 tests/mock_theme_test.py)"
echo "$THEME_OUTPUT"
GUI_OUTPUT="$(xvfb-run -a python3 tests/mock_gui_test.py)"
echo "$GUI_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.19 mock test — miners table beautified (inset well, zebra, dark scrollbar, flat detail)"
  echo
  echo "The main window's results table was the last square surface:"
  echo "a white-framed Treeview with a light scrollbar inside the"
  echo "rounded glass card. Root cause of the white frame: the ttk"
  echo "Treeview style never pinned bordercolor/lightcolor/"
  echo "darkcolor, so clam fell back to its light default border."
  echo "v0.19 (beesky/ui_theme.py + beesky/gui.py only; the web"
  echo "dashboards are untouched):"
  echo
  echo "  * Treeview style pins bordercolor/lightcolor/darkcolor"
  echo "    to the new TABLE_WELL token (#121216) with borderwidth=0"
  echo "    / relief=flat; background/fieldbackground move PANEL ->"
  echo "    TABLE_WELL (rowheight stays 30). Treeview.Heading gets"
  echo "    the TABLE_HEADING strip (#1D1D24) with its border pinned"
  echo "    to the same colour, so the heading separator line"
  echo "    vanishes."
  echo "  * The table sits in an inset WELL inside its glass card:"
  echo "    a RoundedCard (radius 12, fill TABLE_WELL, hairline"
  echo "    #26262E outline, backdrop PANEL_GLASS) with the tree +"
  echo "    scrollbar packed inside at a 10px inset, so the tree's"
  echo "    square corners never touch the card's rounded corners."
  echo "  * Zebra rows: a new \"odd\" tag (TABLE_ZEBRA #17171D) is"
  echo "    applied at insertion time to odd-indexed PLAIN OK rows"
  echo "    only; problem rows keep exactly their \"check\"/\"error\""
  echo "    wash tags (parity never combines with a status tag), so"
  echo "    the dark-gold CHECK wash is untouched."
  echo "  * Scrollbar: Vertical.TScrollbar (and TScrollbar) restyled"
  echo "    dark — BORDER (#26262E) thumb, TABLE_WELL trough and"
  echo "    border, muted arrows."
  echo "  * Detail pane: the tk.Text loses its box (borderwidth=0,"
  echo "    highlightthickness=0) and its background moves PANEL2 ->"
  echo "    PANEL_GLASS, so the text sits flat on the glass card."
  echo
  echo "Changed test expectations (all still exact pins, listed in"
  echo "the root RESULTS.md v0.19 section): mock_theme_test"
  echo "Treeview background PANEL -> TABLE_WELL, plus the new pins"
  echo "above; mock_agent_bg_test release pin 0.18.1 -> 0.19.0."
  echo "No behaviour assertion was weakened. The updated suites:"
  echo
  echo '```'
  echo "$THEME_OUTPUT"
  echo '```'
  echo
  echo '```'
  echo "$GUI_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.19 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
