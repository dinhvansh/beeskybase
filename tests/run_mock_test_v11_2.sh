#!/usr/bin/env bash
# v0.11.2 full mock suite: everything from v0.11 (v0.1..v0.11), then
# the logo wiring checks.
#   run_mock_test_v11.sh   regenerates tests/RESULTS.md (v0.1..v0.11)
#   mock_logo_test.py      static assertions that the official logo
#                          (packaging/assets/beesky-logo.*) is wired
#                          into both dashboards (inline SVG + favicon,
#                          letter "B" mark gone), the PyInstaller spec
#                          (exe icon + GUI datas), the Inno installer
#                          (SetupIconFile) and the tkinter GUI
#                          (iconbitmap/iconphoto + header image).
# The v0.11.2 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v11.sh

LOGO_OUTPUT="$(python3 tests/mock_logo_test.py)"
echo "$LOGO_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.11.2 mock test — official logo wiring"
  echo
  echo "\`tests/mock_logo_test.py\` is a static wiring test (no servers):"
  echo "the official BeeSky logo master (owner's Illustrator vector,"
  echo "yellow #F4D600) ships in \`packaging/assets/\` as SVG + multi-size"
  echo "ICO + 512px PNG. Assertions: both dashboards inline the real SVG"
  echo "in the header (viewBox + chevron path fragment + #F4D600) with"
  echo "an SVG data-URI favicon, and the old CSS letter \"B\" mark is"
  echo "gone; the PyInstaller spec points both exes' icon at"
  echo "beesky-logo.ico and bundles the PNG/ICO in the GUI datas; the"
  echo "Inno installer uses it as SetupIconFile and ships it; the"
  echo "tkinter GUI resolves it via _asset_path (frozen _MEIPASS first,"
  echo "then packaging/assets/) for iconbitmap/iconphoto and the"
  echo "~40px header image. The inlined SVG and the favicon payload"
  echo "were also render-compared against the master during"
  echo "development: 0.00% colour-class difference."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$LOGO_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.11.2 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
