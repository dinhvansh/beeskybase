#!/usr/bin/env bash
# v0.7 full mock suite: everything from v0.6 (v0.1..v0.6), then the
# desktop-GUI smoke test under a virtual display.
#   run_mock_test_v6.sh   regenerates tests/RESULTS.md (v0.1..v0.6)
#   mock_gui_test.py      starts the scripted S19 Pro, runs
#                         `beesky gui --smoke 127.0.0.1` under
#                         xvfb-run and asserts the Treeview row.
# The v0.7 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v6.sh

GUI_OUTPUT="$(xvfb-run -a python3 tests/mock_gui_test.py)"
echo "$GUI_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.7 mock test — desktop GUI (tkinter, headless smoke)"
  echo
  echo "\`tests/mock_gui_test.py\` runs under \`xvfb-run\`: the scripted"
  echo "S19 Pro on 127.0.0.1:4028, then the real GUI via \`beesky gui"
  echo "--smoke\` — window built, one scan, Treeview rows printed."
  echo
  echo '```'
  echo "$GUI_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.7 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
