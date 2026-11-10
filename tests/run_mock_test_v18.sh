#!/usr/bin/env bash
# v0.18 full mock suite: everything from v0.17 (v0.1..v0.17), then
# the Liquid Glass test.
#   run_mock_test_v17.sh       regenerates tests/RESULTS.md (v0.1..v0.17)
#   mock_glass_test.py         the v0.18 material pass: both web
#                              dashboards carry the real glass
#                              (translucent --glass tokens,
#                              backdrop-filter blur(16px)
#                              saturate(150%), ambient
#                              radial-gradient body backdrop,
#                              @supports no-backdrop-filter AND
#                              prefers-reduced-transparency
#                              fallbacks re-pointing the tokens at
#                              the solid colours, accent CTA still
#                              solid yellow); the desktop
#                              simulation (RoundedCard surface fill
#                              PANEL_GLASS / outline GLASS_BORDER,
#                              exactly one rim-light item tagged
#                              "rim" surviving resizes, ghost
#                              RoundedButton rim + glass colour
#                              triple, RoundedEntry ENTRY_FILL /
#                              ENTRY_BORDER).
# The v0.18 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v17.sh

GLASS_OUTPUT="$(xvfb-run -a python3 tests/mock_glass_test.py)"
echo "$GLASS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.18 mock test — Liquid Glass (real web glass, simulated desktop glass)"
  echo
  echo "Web (both dashboards, beesky/cloud + beesky/web): real"
  echo "Liquid Glass — an ambient layered body backdrop (two subtle"
  echo "radial glows over the #0B0B0D base, fixed attachment), glass"
  echo "tokens (--glass rgba(255,255,255,.045), --glass-line .09,"
  echo "--glass-soft .05 / --glass-line-soft .10 for inputs, ghost"
  echo "buttons and chips, --glass-chrome for sidebar/top bars,"
  echo "--glass-head for table header rows), backdrop-filter"
  echo "blur(16px) saturate(150%) (10px for the soft tier) on cards,"
  echo "panels, stat tiles, sidebar, settings panels and table"
  echo "containers, the rim+depth shadow (inset 0 1px 0"
  echo "rgba(255,255,255,.08), 0 8px 32px rgba(0,0,0,.35)); the"
  echo "accent CTA stays solid #F5D800 and table rows stay"
  echo "transparent over a rgba(255,255,255,.03) header. Fallbacks:"
  echo "@supports not (backdrop-filter) and @media"
  echo "(prefers-reduced-transparency: reduce) re-point every glass"
  echo "token at the pre-v0.18 solids (#15151A/#1C1C22/#232329/"
  echo "#101014) and set the blur tokens to none — no layout or DOM"
  echo "change. Desktop (Tk cannot blur): simulated glass in"
  echo "beesky/ui_theme.py + beesky/rounded.py — PANEL_GLASS"
  echo "#191920 card fill, GLASS_BORDER #34343E outlines, a real"
  echo "canvas rim-light line (RIM_LIGHT #3D3D4A, top arc +"
  echo "straight inset 1px, tagged \"rim\") on RoundedCard and"
  echo "ghost RoundedButtons, GHOST_FILL #22222B, ENTRY_FILL"
  echo "#1E1E26 / ENTRY_BORDER #30303C; card-hosted ttk styles and"
  echo "in-card widget backdrops moved PANEL -> PANEL_GLASS so"
  echo "labels blend with the drawn surface; pills and the accent"
  echo "button stay solid. Changed test expectations (all still"
  echo "exact pins, listed in the root RESULTS.md v0.18 section):"
  echo "mock_theme_test Card.TFrame PANEL -> PANEL_GLASS + a new"
  echo "exact pin of the six glass tokens; mock_agent_bg_test"
  echo "release pin 0.17.0 -> 0.18.0. The new suite adds:"
  echo
  echo '```'
  echo "$GLASS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.18 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
