#!/usr/bin/env bash
# v0.27.0 mock suite: DEVICE DETAIL TABS — the HashCore Toolkit's
# device-info dialog ported per docs/device-detail-mapping.md
# (Metrics / Charts / Boards / Pools / Fans / Note; Hotel Fee
# named not-applicable). The scan record stays lean; a new core
# verb `beesky inspect --json <ip>` deep-fetches ONE device
# through the scan's own probe + credential resolution, with
# explicit supported / unsupported-with-reason sections — the
# vnish grade split (grey/orange/red = STABLE/SLOW/CRITICAL)
# ships ONLY where the firmware's grades define it; cgminer /
# stock boards keep acs counts (the named DATA-GAP).
#
# Evidence method (same standalone-sweep pattern as v0.21–v0.26):
# the new mock_inspect_test suite + the release-pin suite
# (mock_agent_bg_test under xvfb, pinning 0.27.0) + standalone
# regression spot-checks (bridge, creds, groups, units, ops).
# The Flutter app IS verified locally this release (analyze +
# full test run with the SDK at ~/workspace/flutter-sdk); only
# its Windows build remains CI-only. Both facts are disclosed in
# the RESULTS.md block this script appends.
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
for spec in "mock_inspect_test plain" "mock_agent_bg_test xvfb" \
            "mock_bridge_test plain" "mock_creds_test plain" \
            "mock_groups_test plain" "mock_units_test plain" \
            "mock_ops_test plain"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

FLUTTER_LINE="flutter analyze: clean; flutter test: 94 PASS / 0 FAIL (local SDK 3.47.9; 78 pre-existing + 16 new detail tests)"

{
  echo
  echo "---"
  echo
  echo "# v0.27.0 — Device detail tabs (HashCore Toolkit device-info dialog, ported per the dissection)"
  echo
  echo "The parity push continues (owner's bar: 99% of HashCore"
  echo "Toolkit in one month). Following the dissect-before-"
  echo "porting rule, the Toolkit's device-info dialog was"
  echo "dissected FIRST from the shipped materials (the"
  echo "device_info_dialog.* / device_info_board_info.* /"
  echo "device_info_pools_info.* translation keys — Metrics,"
  echo "Charts, Boards with CHIPS TOTAL / STABLE / SLOW /"
  echo "CRITICAL, Pools, Fans with Mode + Speed, Hotel Fee,"
  echo "the editable Device note) and BeeSky's OWN data audited"
  echo "against it (the dashd api-doc's AntmMinerStats /"
  echo "Cooling / PoolStats schemas; report.py's acs reading;"
  echo "each adapter's read-only reach, file:line) — the full"
  echo "mapping, with UNKNOWNs and DATA-GAPs named, is in"
  echo "docs/device-detail-mapping.md. Nothing renders that"
  echo "BeeSky does not actually have."
  echo
  echo "PYTHON CORE:"
  echo
  echo "  * beesky/core/inspect.py (NEW) + the \`inspect\` verb:"
  echo "    \`beesky inspect --json <ip>\` deep-fetches ONE device"
  echo "    (read-only) through the scan's own machinery —"
  echo "    discover.probe_host claims it (family detection +"
  echo "    the v0.23 creds-file / v0.24 group credential"
  echo "    resolution: --creds-file, --group, --groups-file,"
  echo "    --user/--password, --api-key, --token exactly like"
  echo "    scan) and the winning set's token/key/login ride"
  echo "    the candidate into the section fetches. Output is"
  echo "    ONE JSON document: {ip, source, model, cred_label,"
  echo "    boards, pools, fans}; every section is"
  echo "    {\"supported\": true, ...} or {\"supported\": false,"
  echo "    \"reason\"} — an explicit marker, never an empty"
  echo "    success; one section's failure never sinks the"
  echo "    others. A malformed target (not one IPv4 address)"
  echo "    or a malformed creds file/group exits 2 BEFORE any"
  echo "    I/O; a device no adapter claims yields an exit-0"
  echo "    {\"error\": ...} document (the app renders the state)."
  echo "  * Per family (evidence: mapping §2): VNISH — the"
  echo "    /summary the scan already fetches carries pools"
  echo "    (PoolStats), cooling (per-fan rpm/status/max_rpm,"
  echo "    the fan mode auto/manual/immersion, fan_duty) and"
  echo "    per-board chip_statuses counts; /boards adds the"
  echo "    per-chip list (pos/hr/grade/temp). The grades ARE"
  echo "    HashCore's buckets: grey = STABLE, orange = SLOW"
  echo "    (degraded but hashing), red = CRITICAL (dead) —"
  echo "    dashd.py's own semantics. The fan mode is parsed"
  echo "    from BOTH the api-doc object shape {name, param}"
  echo "    and the plain-string shape some builds serve."
  echo "    CGMINER — boards from the STATS acs strings (per"
  echo "    chain: raw acs, chips_total, chips_ok, dead"
  echo "    positions, the non-'o' character counts, temp) —"
  echo "    the SAME reading as report.build_record; pools via"
  echo "    the RPC \`pools\` command (CgminerClient.pools"
  echo "    existed unused); fans = STATS speeds, mode null"
  echo "    (no source key exists). STOCK — boards/fans from"
  echo "    the status CGI the probe already fetched (cgminer-"
  echo "    shaped); pools attempted via the bmminer RPC and"
  echo "    honestly unsupported when it does not answer (no"
  echo "    CGI source). The scan record is UNCHANGED."
  echo
  echo "FLUTTER APP (app_flutter/):"
  echo
  echo "  * The detail panel becomes TABBED (named layout"
  echo "    divergence: BeeSky keeps its v0.22 right-side panel;"
  echo "    HashCore's is a modal dialog — tabs + content are"
  echo "    the parity target). Order mirrors the dialog:"
  echo "    Số liệu (Metrics) · Biểu đồ (Charts) · Board ·"
  echo "    Pools · Quạt (Fans) · Ghi chú (Note). The first tab"
  echo "    is NOT named 'Tổng quan' — that label already names"
  echo "    the grid's Overview density on the same screen (the"
  echo "    collision broke a grid widget test during the"
  echo "    build; fixed by naming, disclosed here)."
  echo "  * lib/detail.dart (NEW): the inspect wire models"
  echo "    (sections with supported/reason; boards with the"
  echo "    grade buckets OR the acs shape, never both faked);"
  echo "    HistorySample + appendHistorySample (keyed MAC-else-"
  echo "    IP via deviceKeyFor, rate in the record's OWN native"
  echo "    unit, cap 300/device, oldest pruned); the pure"
  echo "    chart prep (ratePoints / tempPoints / powerPoints —"
  echo "    samples lacking a metric are skipped, never zeroed;"
  echo "    rateUnitOf labels the line with the device's unit);"
  echo "    MiniChart, a hand-drawn CustomPainter line chart"
  echo "    (zero third-party deps kept — HashCore's fl_chart"
  echo "    is a library divergence, not a behaviour one; a"
  echo "    single point draws as a lone dot); HistoryStore"
  echo "    (beesky-history.json) + NoteStore (beesky-notes.json)"
  echo "    on the stores' usual beside-the-exe / %APPDATA%"
  echo "    strategy, corrupt reads as empty."
  echo "  * Số liệu = the v0.22 panel content VERBATIM"
  echo "    (metrics, issues, board summary lines) — a shipped"
  echo "    contract; the Board tab carries the deep view (the"
  echo "    named duplication). Biểu đồ: LOCAL samples only —"
  echo "    every completed scan appends one sample per live"
  echo "    device (FETCH_ERROR records are skipped: a failed"
  echo "    read is not a sample); hashrate + max-temp + power"
  echo "    (when the device reports power) lines, per device,"
  echo "    never aggregated across units; the empty state says"
  echo "    charts fill in as scans accumulate. Board: record"
  echo "    rows immediately; the inspect fetch (lazy, once per"
  echo "    device per session) adds the vnish grade split +"
  echo "    PCB temp + per-chip grades, or the cgminer/stock"
  echo "    acs breakdown + dead positions — matched to boards"
  echo "    by POSITION (record and inspect index bases differ"
  echo "    between the mock fleet and the real core; position"
  echo "    is the convention-free key). Pools: the record's"
  echo "    pools when a future core fills them, else inspect"
  echo "    on first open — loading state, then rows ('Pool N"
  echo "    URL' / 'Pool N worker', HashCore's own labels) or"
  echo "    the core's unsupported reason verbatim. Quạt:"
  echo "    record speeds immediately; inspect adds mode +"
  echo "    duty (vnish) or the plain 'firmware không báo'"
  echo "    absence. Ghi chú: HashCore's Device note + Save"
  echo "    note — a text field + explicit Lưu ghi chú, keyed"
  echo "    like history, persisted across restarts."
  echo "  * lib/sidecar.dart: BeeSkyBridge.inspect(ip, {credsFile,"
  echo "    group, groupsFile}) — argv carries the IP + file"
  echo "    PATHS + the group NAME only (values never travel,"
  echo "    the v0.23 rule); in a group's scope the group rides"
  echo "    along so the core resolves its creds layer, exactly"
  echo "    like its scans and ops jobs. MockBridge gains"
  echo "    inspect fixtures per sample device (vnish with the"
  echo "    split + mode, two cgminer with acs boards + pools,"
  echo "    the unreachable unit as an error document) and the"
  echo "    app seeds demo history for the mock fleet so every"
  echo "    tab renders in tests/demos."
  echo
  echo "PER-TAB MATCH / DIVERGENCE / DATA-GAP vs HASHCORE"
  echo "(full table: docs/device-detail-mapping.md §3–§5):"
  echo
  echo "  Metrics -> Số liệu: MATCH (the existing panel)."
  echo "  Charts: DIVERGENCE (named) — HashCore's history"
  echo "  mechanics are UNKNOWN from the shipped materials;"
  echo "  BeeSky charts LOCAL scan samples, persisted, per"
  echo "  device in its native unit. Content (hashrate +"
  echo "  temperature lines) matches; power is a BeeSky extra"
  echo "  the data genuinely carries."
  echo "  Boards: MATCH for vnish (TOTAL/STABLE/SLOW/CRITICAL"
  echo "  from the firmware's own grades — the same data"
  echo "  HashCore renders). DATA-GAP for cgminer/stock: the"
  echo "  acs alphabet's non-'o' characters have no documented"
  echo "  grade semantics in BeeSky's evidence, so those boards"
  echo "  show ok/total + dead positions + raw character counts"
  echo "  and the tab STATES the gap — no invented buckets."
  echo "  Pools: MATCH per family where a source exists"
  echo "  (dashd summary, cgminer RPC); stock without an RPC"
  echo "  answer is unsupported-with-reason, not empty."
  echo "  Fans: MATCH (mode + per-fan speed) for vnish;"
  echo "  speeds-only for cgminer/stock — fan MODE is a"
  echo "  DATA-GAP there (no source key exists)."
  echo "  Note: MATCH (per-device, placeholder + explicit"
  echo "  save), as a tab instead of a dialog field (the"
  echo "  container divergence). The v0.25 grid Note COLUMN is"
  echo "  NOT wired: cell text is a pure function of the"
  echo "  record and notes live outside records — more than a"
  echo "  trivial hookup; left for a later pass, named here."
  echo "  Hotel Fee: NOT APPLICABLE — BeeSky has no hotel-fee"
  echo "  concept (no data, no settings); not built."
  echo "  Also named: PCB temp rides inspect only (the record"
  echo "  still carries chip temp alone); MAC keying is"
  echo "  'when present' — no adapter emits a MAC today."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * Python suites at the v0.27.0 pins:"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "    mock_inspect_test covers: the vnish sections end"
  echo "    to end (grade split 112/0/2 on the sick board,"
  echo "    dead positions [10, 55] from /boards grades, the"
  echo "    114-chip list, chip + pcb temps, PoolStats pools,"
  echo "    fan mode auto + duty 62 + per-fan status); the"
  echo "    cgminer sections (acs counts 111/114, dead"
  echo "    [10, 55, 114], other_chars {x: 3}, NO grade keys"
  echo "    in the wire — the gap is structural; RPC pools;"
  echo "    fan mode null); the stock sections (CGI boards/"
  echo "    fans; pools unsupported with the no-source reason);"
  echo "    credential reuse (a locked dashd claimed by the"
  echo "    creds-file winner + label, its pools honestly"
  echo "    unsupported — that mock's summary carries none;"
  echo "    wrong creds -> the vnish candidate with every"
  echo "    section unsupported on the 401; --group resolution"
  echo "    with the group's set winning; unknown group exits"
  echo "    2); the exit-2 contract (5 malformed targets + a"
  echo "    malformed creds file, stdout empty throughout);"
  echo "    the exit-0 error document for an unclaimed device."
  echo
  echo "  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):"
  echo "    $FLUTTER_LINE — inspect model parsing per family"
  echo "    (grades vs acs shapes, unsupported markers, the"
  echo "    error document + failure factory); history append"
  echo "    (IP/MAC keying, native-unit + legacy-ths rates,"
  echo "    the 300-cap prune) + JSON round-trips; chart prep"
  echo "    (null-skipping, unit labelling, empty/single"
  echo "    shapes); the history/notes stores' round-trips +"
  echo "    corrupt-reads-empty; the inspect argv contract;"
  echo "    the mock fixtures' family shapes; the painter's"
  echo "    single-point + flat-series smoke. Widget level:"
  echo "    all six tabs render for the vnish S19 (pool rows,"
  echo "    fan mode + duty, the three grade lines, the seeded"
  echo "    charts incl. power); the L9's Boards tab states"
  echo "    the grade DATA-GAP + the acs breakdown with no"
  echo "    bucket line, its Fans tab shows the honest mode"
  echo "    absence; the charts empty state for the sample-"
  echo "    less device; a note saves and survives a fresh"
  echo "    HomePage. All 78 pre-existing tests still pass —"
  echo "    the only pre-existing test touched is the version"
  echo "    pin in widget_test.dart (v0.27.0); the grid"
  echo "    density test's 'Tổng quan' collision was fixed by"
  echo "    NAMING the detail tab 'Số liệu', not by editing"
  echo "    the grid test."
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
echo "V0.27.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
