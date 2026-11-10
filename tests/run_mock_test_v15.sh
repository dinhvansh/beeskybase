#!/usr/bin/env bash
# v0.15 full mock suite: everything from v0.14 (v0.1..v0.14), then
# the shared-theme test.
#   run_mock_test_v14.sh    regenerates tests/RESULTS.md (v0.1..v0.14)
#   mock_theme_test.py      asserts ui_theme.setup_theme applies the
#                           cloud-dashboard palette to the ttk styles
#                           (entry field background/padding, accent
#                           button, treeview, card frame, root bg),
#                           that the agent window builds with its two
#                           cards ("Kết nối cloud" / "Quét tại trại")
#                           + the status pill, and that the main
#                           window builds with the toolbar card, the
#                           four stat cards and the detail card —
#                           with show_records() driving the stats.
# The v0.15 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v14.sh

THEME_OUTPUT="$(xvfb-run -a python3 tests/mock_theme_test.py)"
echo "$THEME_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.15 mock test — desktop apps visual overhaul (shared ui_theme)"
  echo
  echo "\`beesky/ui_theme.py\` is the new shared design system for both"
  echo "desktop windows: the cloud dashboard's palette (bg #0B0B0D,"
  echo "panels #15151A/#1C1C22, border #26262E, text #F2F2F3, muted"
  echo "#9CA3AF, accent #F5D800, status #34D399/#FBBF24/#F87171) on"
  echo "ttk 'clam' — card frames, label-above form fields, accent/ghost"
  echo "buttons, dark entries with a yellow focus border, a 30px-row"
  echo "treeview and a status pill. \`beesky/agent_gui.py\` is rebuilt"
  echo "on it: header (logo + title + version chip), a 'Kết nối"
  echo "cloud' card (Cloud URL, masked agent key with Hiện key toggle,"
  echo "Tên trại, the one-time-key note), a 'Quét tại trại' card (Dải"
  echo "IP quét, Chu kỳ quét), the three action buttons plus a status"
  echo "pill that follows Chạy thử (dim/warn/ok/bad). \`beesky/gui.py\`"
  echo "is rebuilt on it too: header band, a 'Mục tiêu quét' toolbar"
  echo "card (wide target entry, Quét ngay / Xuất phiếu sửa / Mở web"
  echo "tại chỗ / Quét lại, plus the stock-firmware User/Mật khẩu"
  echo "fields), FOUR stat cards (Tổng số máy / Tổng hashrate / Máy"
  echo "có vấn đề / Nhiệt độ cao nhất) driven by show_records(), the"
  echo "results tree and the detail pane as cards, and a footer status"
  echo "bar. All behaviour is unchanged — the v0.7 GUI smoke and the"
  echo "v0.14 agent-GUI assertions (fields, key mask toggle, save"
  echo "round-trip, auto-start state) run green inside the full"
  echo "chain above; \`tests/mock_theme_test.py\` adds the theme"
  echo "assertions below."
  echo
  echo '```'
  echo "$THEME_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.15 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
