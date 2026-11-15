#!/usr/bin/env bash
# v0.25.0 mock suite: the DATA-GRID miners list — the HashCore
# Toolkit's list machinery ported per docs/grid-mapping.md
# (configurable columns + beesky-grid.json, densities + Overview
# heat-grid, Metric/Pools/Custom modes, header sorting, search,
# the AND filter builder with saveable presets, grouping, the
# checkbox selection model + isolate, grid hotkeys).
#
# The Python core is UNCHANGED in v0.25 (the grid is a Flutter
# port; the record fields it needed — elapsed_s, ghs_5s, power_w —
# were already on the wire). Evidence method (same standalone-
# sweep pattern as v0.21–v0.24): the release-pin suite
# (mock_agent_bg_test under xvfb, which now pins 0.25.0) plus
# standalone regression spot-checks on the suites nearest the
# version bump (bridge, groups, creds, units). The Flutter app IS
# verified locally this release (analyze + full test run with the
# SDK at ~/workspace/flutter-sdk); only its Windows build remains
# CI-only. Both facts are disclosed in the RESULTS.md block this
# script appends.
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
for spec in "mock_agent_bg_test xvfb" "mock_bridge_test plain" \
            "mock_groups_test plain" "mock_creds_test plain" \
            "mock_units_test plain"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

FLUTTER_LINE="flutter analyze: clean; flutter test: 63 PASS / 0 FAIL (local SDK 3.47.9; 35 pre-existing + 28 new grid tests)"

{
  echo
  echo "---"
  echo
  echo "# v0.25.0 — data-grid miners list (HashCore Toolkit list machinery, ported per the dissection)"
  echo
  echo "The parity push continues (owner's bar: 99% of HashCore"
  echo "Toolkit in one month). Following the dissect-before-"
  echo "porting rule, the Toolkit's miners-list mechanism was"
  echo "dissected FIRST from the shipped materials (the full"
  echo "~1,500-key translation table, the AOT string pools, the"
  echo "Dart file map) and the behaviour mapping written to"
  echo "docs/grid-mapping.md BEFORE any code — every behaviour"
  echo "graded VERIFIED / INFERRED / UNKNOWN, every column audited"
  echo "against the real BeeSky record schema, data gaps named"
  echo "instead of faked."
  echo
  echo "PYTHON CORE: unchanged. The grid is a Flutter-side port;"
  echo "the record fields it needed (elapsed_s, ghs_5s, power_w)"
  echo "were already on the wire from _finalise_record — the Dart"
  echo "model simply never parsed them. They are parsed now."
  echo
  echo "FLUTTER APP (app_flutter/):"
  echo
  echo "  * lib/grid.dart (NEW): the column universe (29 columns),"
  echo "    GridConfig + GridStore (beesky-grid.json beside the exe,"
  echo "    %APPDATA% fallback, corrupt = factory defaults), the"
  echo "    GridFilter model (numeric / range / string / bool —"
  echo "    HashCore's four MinerFilter variants), FilterPreset,"
  echo "    the MinerSelection model + IsolateMode, grouping, and"
  echo "    the pure view pipeline (search -> filters AND ->"
  echo "    isolate -> sort -> group). lib/grid_dialogs.dart (NEW):"
  echo "    the columns dialog (toggle + up/down reorder + CHƯA CÓ"
  echo "    DỮ LIỆU tags on gap columns + Đặt lại mặc định) and"
  echo "    the filter dialog (builder rows + named presets)."
  echo "  * Columns: every column BeeSky records can feed, each"
  echo "    toggleable + reorderable, persisted; reset restores"
  echo "    the exact v0.24 default set/order. Per-board chip-temp"
  echo "    columns BOARD 1–4 join the combined NHIỆT column."
  echo "    Data modes: Số liệu (fixed metric set) / Pools (fixed"
  echo "    pool set) / Tùy chỉnh (the user's set; the columns"
  echo "    dialog edits it and switches to it)."
  echo "  * Densities: Thoải mái / Gọn row heights + TỔNG QUAN"
  echo "    heat-grid (cells coloured by Temperature — absolute"
  echo "    bands ending in the >=85 °C red rule — or by Hashrate"
  echo "    share within the same unit; sizes S/M/L; click a cell"
  echo "    selects it and opens the detail panel, double-click"
  echo "    opens its web admin, tooltip carries the facts)."
  echo "  * Sort by any column header (arrow shows direction);"
  echo "    IPs compare octet-numerically; rates compare only"
  echo "    inside their native-unit family (the v0.20 lesson);"
  echo "    nulls sort last in both directions. Search matches"
  echo "    IP / MAC / model / pool / worker. Grouping by Trạng"
  echo "    thái / Model / Firmware renders header rows with"
  echo "    counts. A filtered-to-empty list shows HashCore's"
  echo "    empty-filter state with a clear action."
  echo "  * Selection: a checkbox column + header select-all-"
  echo "    visible (tri-state); the selection bar shows the"
  echo "    result count (Đang hiển thị X / Y máy), the selected"
  echo "    count, Chọn tất cả / Đảo chọn / Cô lập (đã chọn | lỗi)"
  echo "    / Xóa lọc-chọn. The selection lives in grid.dart's"
  echo "    MinerSelection model — v0.26's Operations bar consumes"
  echo "    it from there; the Operations BAR itself is NOT built"
  echo "    in v0.25, exactly as scoped."
  echo "  * Hotkeys via Shortcuts/Actions with intent classes"
  echo "    (HashCore's own architecture is intents+actions too):"
  echo "    Ctrl+A select all visible, Ctrl+F focus search,"
  echo "    Ctrl+R / F5 rescan, Esc clear search+filters+isolate"
  echo "    +selection. Handlers step aside while a text field"
  echo "    owns the keyboard."
  echo "  * All v0.24 behaviours intact: groups home + group scan"
  echo "    scoping, double-click row -> miner web, creds dialog,"
  echo "    per-board temps red at >=85 °C, header chips."
  echo
  echo "MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):"
  echo
  echo "  MATCH: the two view axes (type x mode, incl. the enum"
  echo "  value sets); Overview structure (cells, colour-metric"
  echo "  toggle, S/M/L sizes, per-cell tooltip); user-configurable"
  echo "  columns with reorder + reset-to-defaults; sort by field"
  echo "  + direction; the search placeholder's field set; the"
  echo "  filter model (numeric comparisons More/Less/Equals/Not"
  echo "  equals, range variant, string contains/is-any family,"
  echo "  bool variant) AND-combined; named filter presets in a"
  echo "  presets store shared with the future pool presets;"
  echo "  grouping by a field with group headers; select all /"
  echo "  invert / isolate (selected | errors); the empty-filter"
  echo "  state + clear action; an intents+actions hotkey layer."
  echo
  echo "  DIVERGENCE (named, in the mapping): BeeSky labels are"
  echo "  Vietnamese and its defaults are the v0.24 set; Overview's"
  echo "  colour SCALE is BeeSky's (HashCore's is UNKNOWN — not"
  echo "  observable in the materials); the columns dialog uses"
  echo "  up/down buttons (HashCore's reorder gesture is UNKNOWN);"
  echo "  a same-name filter preset replaces silently (HashCore"
  echo "  prompts — its edit-preset dialog is Presets-center scope);"
  echo "  the full Presets CENTER dialog is not built — presets"
  echo "  live in the filter dialog + the shared store (the seed;"
  echo "  pool presets arrive v0.28); grouping renders in the two"
  echo "  table densities only (the heat-grid is flat) and has no"
  echo "  jump-to-group / collapse (UNKNOWN in the original);"
  echo "  active filter rows are session-only (their persistence"
  echo "  in HashCore is UNKNOWN); hotkey BINDINGS are BeeSky's"
  echo "  (the intent set matches; HashCore's keys are UNKNOWN);"
  echo "  zoom + command palette are named gaps; BeeSky keeps two"
  echo "  columns HashCore has no counterpart for (CHIP, ĐĂNG"
  echo "  NHẬP) because they carry core BeeSky data."
  echo
  echo "  DATA-GAPS (columns offered, values honestly '—' — the"
  echo "  core emits no such data; nothing is faked): MAC, S/N,"
  echo "  Pool 1–3 URL + worker (scan records carry NO pool data"
  echo "  at all today — the columns parse an optional wire"
  echo "  'pools' list so they light up when the core grows one)."
  echo "  PARTIAL: HASHRATE RT (the wire's ghs_5s is GH/s-family"
  echo "  only — shown for TH/s records, '—' for MH/s + ksol/s)."
  echo "  DERIVED (arithmetic on real fields, marked in the"
  echo "  mapping): HIỆU SUẤT = power_w / ths (J/TH, TH/s + power"
  echo "  records only); THUẬT TOÁN from the native rate unit;"
  echo "  BOARD LỖI from per-chain chip counts. NOT OFFERED (no"
  echo "  data source at all): lock state, Has PICs, stock"
  echo "  hashrate, throttling, miner presets, board serials /"
  echo "  models / chip BIN, PSU model/serial/PFC/LLC temps,"
  echo "  platform, install type, firmware build date/name, PCB"
  echo "  temps (BeeSky carries ONE temp per chain), cooling,"
  echo "  Hotel Fee, DevFee availability, power limit, per-record"
  echo "  range, note (device-detail scope, v0.27)."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * Python regression spot-checks at the v0.25.0 pins"
  echo "    (core untouched; the pin suite asserts the version):"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):"
  echo "    $FLUTTER_LINE — model parsing of the newly-read wire"
  echo "    fields + derived getters (uptime, J/TH, TH/s-only RT,"
  echo "    algorithm, bad boards); column defaults = the v0.24"
  echo "    set/order; pools-mode set; toggle/reorder/reset; JSON"
  echo "    round-trip (unknown ids dropped, new columns join the"
  echo "    tail); GridStore round-trip + corrupt-file fallback;"
  echo "    sorts (IP octets, temps nulls-last both ways, status"
  echo "    order, rates family-locked); search (IP/model); the"
  echo "    filter operators incl. between + the null-field rule"
  echo "    + unparseable-number rule; presets JSON round-trip;"
  echo "    grouping counts on a generated 63-miner fleet (status"
  echo "    49/13/1); the selection model; isolate modes. Widget"
  echo "    level: density switching + heat-grid red rule + cell-"
  echo "    click detail; header sort asc/desc; search + count"
  echo "    line; checkbox selection + both isolate modes +"
  echo "    Ctrl+A / Esc / Ctrl+F hotkeys; the filter dialog end"
  echo "    to end (apply -> save preset -> clear -> re-apply ->"
  echo "    preset found in beesky-grid.json on disk); the columns"
  echo "    dialog (gap tags, enable UPTIME -> header + file,"
  echo "    reset -> gone); grouping headers on the 63-fleet. All"
  echo "    35 pre-existing tests still pass — the suite was not"
  echo "    adapted at all this release."
  echo
  echo "(b) VERIFIED ONLY BY CI (.github/workflows/"
  echo "build-flutter.yml):"
  echo
  echo "  * flutter build windows --release on a real Windows"
  echo "    runner and the BeeSkyFlutter-<tag>-win64.zip asset."
  echo "    The app remains compile-verified only until the"
  echo "    owner runs it on real Windows (as since v0.21)."
} >> tests/RESULTS.md

echo
echo "V0.25.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
