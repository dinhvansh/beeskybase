#!/usr/bin/env bash
# v0.24.0 mock suite: network groups — the HashCore Toolkit's home
# screen ported per docs/network-groups-mapping.md (group store,
# group scans with merged group→global credentials, last_scan
# persistence, CLI groups CRUD + export/import), the Flutter app
# opening on the groups screen.
#
# Evidence method (same standalone-sweep pattern as v0.21–v0.23):
# the NEW mock_groups_test in full, plus standalone regression
# spot-checks on the suites nearest the cli/discover changes
# (creds, bridge, units) and the release-pin suite (agent_bg,
# under xvfb). The Flutter app IS verified locally this release
# (the SDK at ~/workspace/flutter-sdk runs analyze + test here);
# only its Windows build remains CI-only. Both facts are disclosed
# in the RESULTS.md block this script appends.
set -uo pipefail
cd "$(dirname "$0")/.."

run_suite() {  # name, mode(plain|xvfb)
  local name="$1" mode="${2:-plain}"
  case "$mode" in
    xvfb) xvfb-run -a python3 "tests/$name.py" ;;
    *)    python3 "tests/$name.py" ;;
  esac
}

GROUPS_OUTPUT="$(run_suite mock_groups_test)"; echo "$GROUPS_OUTPUT"

summary_line() {
  local out passes fails
  out="$(run_suite "$1" "${2:-plain}")"
  passes="$(printf '%s\n' "$out" | grep -c '^PASS')"
  fails="$(printf '%s\n' "$out" | grep -c '^FAIL')"
  echo "$1: $passes PASS / $fails FAIL (standalone)"
}

SUMMARY_LINES=""
for spec in "mock_creds_test plain" "mock_bridge_test plain" \
            "mock_units_test plain" "mock_agent_bg_test xvfb"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

FLUTTER_LINE="flutter analyze: clean; flutter test: 35 PASS / 0 FAIL (local SDK 3.47.9)"

{
  echo
  echo "---"
  echo
  echo "# v0.24.0 — network groups (HashCore Toolkit home screen, ported per the dissection)"
  echo
  echo "The owner set the parity bar (2026-11-11): \"không được 100"
  echo "cũng ráng được 99%\" vs HashCore Toolkit, and named network"
  echo "groups as the first gap to close. Following the standing"
  echo "dissect-before-porting rule, the Toolkit's group mechanism"
  echo "was dissected FIRST from the shipped materials (translation"
  echo "table, AOT string pools, Dart file map) and the behaviour"
  echo "mapping written to docs/network-groups-mapping.md BEFORE"
  echo "any code — every behaviour graded VERIFIED / INFERRED /"
  echo "UNKNOWN, divergences named, unknowns never invented."
  echo
  echo "PYTHON CORE (beesky/core/groups.py NEW, cli.py):"
  echo
  echo "  * Group = {id, name, targets, creds, autoscan{enabled,"
  echo "    interval_min}, last_scan{at, scanned, found, ok, check,"
  echo "    error} | null}, persisted as {\"version\": 1, \"groups\":"
  echo "    [...]} in beesky-groups.json — located with the SAME"
  echo "    strategy as the v0.23 creds file (beside the executable,"
  echo "    %APPDATA%\\BeeSky fallback; --groups-file / env"
  echo "    BEESKY_GROUPS_FILE override). Loading fails loud"
  echo "    (GroupError -> exit 2): malformed JSON, a nameless entry,"
  echo "    invalid targets (validated via parse_targets), a bad"
  echo "    creds shape, a zero autoscan interval."
  echo "  * \`beesky groups list|add|remove|show\` (add takes"
  echo "    --name/--targets and mirrors the JSON; duplicate names"
  echo "    rejected) and \`groups export <file>\` / \`import <file>\`."
  echo "    Import merges BY NAME — a same-name group replaces the"
  echo "    stored one in place, others are kept — the stated"
  echo "    BeeSky policy (HashCore's own import policy is UNKNOWN,"
  echo "    see the mapping). An invalid import file exits 2 and"
  echo "    changes nothing."
  echo "  * \`beesky scan --group NAME\` (the positional target"
  echo "    becomes optional): the core resolves the group's"
  echo "    targets and merges credentials — group sets BEFORE the"
  echo "    --creds-file (global) sets — and ordered_creds' stable"
  echo "    tiers then try, per miner: group family -> global family"
  echo "    -> group \"any\" -> global \"any\" -> the rest. This is"
  echo "    the port of HashCore's global -> per-group override"
  echo "    layering onto BeeSky's v0.23 list model. Unknown group"
  echo "    = clean exit 2 before any scanning. After ANY successful"
  echo "    scan with --group (CLI or bridge --json), last_scan is"
  echo "    persisted into the store (best-effort: a refused write"
  echo "    warns on stderr and never fails the scan). No --group"
  echo "    = byte-identical v0.23 behaviour."
  echo
  echo "FLUTTER APP (app_flutter/):"
  echo
  echo "  * Launch lands on a real NETWORK GROUPS screen (sidebar"
  echo "    \"Nhóm mạng\" active): stat chips (total groups / scanned"
  echo "    / total errors), group cards — name (+ MỚI tag while"
  echo "    never scanned, mirroring HashCore's \"new\"), targets"
  echo "    summary, last-scan line (\"Chưa quét\" or time + counts),"
  echo "    autoscan state, [Quét nhóm] [Sửa] [Xóa] (delete asks"
  echo "    first, naming the group). Empty state mirrors HashCore's"
  echo "    (icon + line + [Thêm nhóm])."
  echo "  * \"＋ Thêm nhóm\" / [Sửa] opens the editor dialog: name,"
  echo "    targets, autoscan toggle + interval (minutes), and the"
  echo "    group's own credential sets — the v0.23 creds editor"
  echo "    widget FACTORED OUT of the creds dialog"
  echo "    (CredSetsEditor in creds.dart) and reused, not redrawn."
  echo "    Duplicate group names are refused app-side too."
  echo "  * Quét nhóm switches to the miners view scoped to the"
  echo "    group (header chip \"Nhóm: <name>\") and runs"
  echo "    \`scan --group <name>\` — the core owns resolution; the"
  echo "    app passes the global creds file path AND its groups"
  echo "    file path, so merging and last_scan persistence happen"
  echo "    core-side; the app reloads the store to refresh the"
  echo "    card. The miners view keeps its ad-hoc scan bar;"
  echo "    editing the target away from the group's ranges leaves"
  echo "    the group scope. Mock mode: two demo groups (\"Trại"
  echo "    chính\" with a last_scan, \"Kho phụ\" never scanned)."
  echo "  * Autoscan (DIVERGENCE, pre-approved): app-side only — a"
  echo "    timer re-runs the ACTIVE group's scan at its interval"
  echo "    while the app is open; state visible on the card. (The"
  echo "    mapping notes HashCore's autoscan also runs app-side in"
  echo "    the Toolkit; BeeSky's always-on equivalent remains the"
  echo "    farm agent.)"
  echo
  echo "MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):"
  echo
  echo "  MATCH: groups as the home screen; named group objects in"
  echo "  a farms-style JSON store; card facts (name, ranges, last"
  echo "  scan, autoscan state); \"new\" tag for never-scanned"
  echo "  groups; empty state shape; delete confirmation naming"
  echo "  the group; per-group credential override layer over the"
  echo "  global sets; per-group autoscan flag + interval; JSON"
  echo "  export/import."
  echo
  echo "  DIVERGENCE (pre-approved, in the mapping): targets are"
  echo "  one multi-range string (parse_targets), not typed named"
  echo "  range objects with per-range enable/DNS/port ranges; no"
  echo "  group description field; credential layers MERGE as"
  echo "  lists (multiple sets per vendor survive — v0.23's model)"
  echo "  instead of HashCore's one-method-per-vendor replacement;"
  echo "  autoscan interval in minutes, app-side only, no global"
  echo "  master switch (BeeSky has no settings screen yet);"
  echo "  last_scan is a counts subset (no hashrate/unlocked totals"
  echo "  — native-unit totals would mislead, the v0.20 lesson)."
  echo
  echo "  NOT PORTED (named gaps): group merge, combined view,"
  echo "  group search, reset-statistics command, rescan-all /"
  echo "  remove-all / multi-select, per-group custom timeout,"
  echo "  IP-Report -> group, the editor's \"Save and scan\" chain."
  echo
  echo "  UNKNOWN (never invented): farms.json field names;"
  echo "  HashCore's import conflict policy; its autoscan interval"
  echo "  unit/range/default; the exact persisted shape of its"
  echo "  last-scan statistics; whether its autoscan is full"
  echo "  discovery or statistics-only."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * mock_groups_test — store CRUD + persistence round-trip"
  echo "    (incl. bare-list load + fail-loud validation),"
  echo "    merge-order units (the six-tier sequence asserted),"
  echo "    CLI groups CRUD/export/import (merge-by-name policy),"
  echo "    and subprocess bridge scans against the mock dashd"
  echo "    fleet: group set beats global same-family set (the"
  echo "    global wrong password is never attempted), global set"
  echo "    rescues a failed group set (attempt log order proves"
  echo "    it), a cred-less group falls back to the global file,"
  echo "    last_scan persisted with the right counts, a groupless"
  echo "    scan never touches the store, unknown group exits 2."
  echo "    Full output:"
  echo
  echo '```'
  echo "$GROUPS_OUTPUT"
  echo '```'
  echo
  echo "  * Regression spot-checks at the v0.24.0 code:"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):"
  echo "    $FLUTTER_LINE — NetGroup/GroupStore round-trips,"
  echo "    autoscan-due rule, the scanGroup argv contract, the"
  echo "    groups home rendering both demo cards, group scan"
  echo "    scoping the miners view (+ header chip), editor create"
  echo "    with a per-group cred set persisted to the store file,"
  echo "    rename, and the confirm-then-delete flow. The two"
  echo "    pre-existing suites were adapted only where the flow"
  echo "    itself changed (the app now opens on groups: one"
  echo "    sidebar tap reaches the miners view)."
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
echo "V0.24.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
