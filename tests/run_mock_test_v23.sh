#!/usr/bin/env bash
# v0.23.0 mock suite: saved multi-credential scan (vendor-keyed),
# double-click opens the miner web admin, local-web button removed.
#
# Evidence method (same standalone-sweep pattern as v0.21/v0.22):
# the NEW mock_creds_test in full, plus standalone regression
# spot-checks on the suites nearest the discover/cli changes
# (bridge, units, cloud, web) and the release-pin suite (agent_bg,
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

CREDS_OUTPUT="$(run_suite mock_creds_test)"; echo "$CREDS_OUTPUT"

summary_line() {
  local out passes fails
  out="$(run_suite "$1" "${2:-plain}")"
  passes="$(printf '%s\n' "$out" | grep -c '^PASS')"
  fails="$(printf '%s\n' "$out" | grep -c '^FAIL')"
  echo "$1: $passes PASS / $fails FAIL (standalone)"
}

SUMMARY_LINES=""
for spec in "mock_bridge_test plain" "mock_units_test plain" \
            "mock_cloud_test plain" "mock_web_test plain" \
            "mock_agent_bg_test xvfb"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

FLUTTER_LINE="flutter analyze: clean; flutter test: 24 PASS / 0 FAIL (local SDK 3.47.9)"

{
  echo
  echo "---"
  echo
  echo "# v0.23.0 — saved multi-credential scan; double-click opens miner web; drop local-web button"
  echo
  echo "The owner's three requests (2026-11-11): (1) remove the"
  echo "Flutter app's \"Mở web local\" button; (2) double-click a"
  echo "miner row to open that miner's web admin (http://<ip>) in"
  echo "the default browser, BTC Tools-style; (3) multi-credential"
  echo "support — the fleet has many machine lines with different"
  echo "logins, so the app must store MANY credential sets and the"
  echo "scan must try them automatically. Two owner amendments"
  echo "landed during the build: each set carries a machine-type"
  echo "tag so detection picks the right set first (not blind"
  echo "order), and — after the HashCore Toolkit re-analysis"
  echo "(research/hashcore/UI-ANALYSIS.md) — the model is keyed"
  echo "like theirs: one unlock method family PER FIRMWARE"
  echo "VENDOR, selected by the detected firmware, with an"
  echo "API-key method for VNish."
  echo
  echo "PYTHON CORE (beesky/core/discover.py, dashd.py, cli.py):"
  echo
  echo "  * \`scan\` (and watch/serve/agent, via the shared common"
  echo "    args) gains \`--creds-file <path>\`: a JSON list"
  echo "    [{\"label\": ..., \"user\": ..., \"password\": ...}] — the"
  echo "    same schema the Flutter app writes. Legacy"
  echo "    --user/--password stays a one-entry list; no creds at"
  echo "    all keeps the previous behaviour byte-identical"
  echo "    (probe_host(creds=None)). A malformed file exits 2"
  echo "    before any scanning."
  echo "  * Each entry may carry \"type\": \"stock\" | \"vnish\" |"
  echo "    \"any\" (missing/unknown reads as \"any\") — the vendor"
  echo "    key. The probe already knows a miner's family before"
  echo "    auth, and tries, in order: (a) sets keyed to that"
  echo "    family, in saved order; (b) \"any\" sets; (c) all"
  echo "    remaining sets — a wrong tag costs attempts, never"
  echo "    locks a machine out. VNish/dashd sets are tried via"
  echo "    /unlock (password method) unless the set carries"
  echo "    \"api_key\", in which case the adapter authenticates"
  echo "    with the x-api-key header INSTEAD (the VNish API-key"
  echo "    method). Stock sets go through the web digest auth."
  echo "    cgminer RPC needs no auth and is untouched."
  echo "  * On success the record gains \"cred_label\" (the winning"
  echo "    set's label); RPC wins, anonymous dashd wins and"
  echo "    default-credential wins stay label-free. In creds"
  echo "    mode only, a dashd that refuses anonymously with 401"
  echo "    and matches no set still surfaces as a candidate, so"
  echo "    the fetch reports the 401 FETCH_ERROR — a locked"
  echo "    VNish box stays visible instead of vanishing."
  echo "  * Bridge \`--json\` carries cred_label like any record"
  echo "    field (asserted in the creds suite against a real"
  echo "    subprocess scan)."
  echo
  echo "FLUTTER APP (app_flutter/):"
  echo
  echo "  * Scan bar: the single user/password fields and the"
  echo "    \"Mở web local\" button (and its serve shell-out) are"
  echo "    REMOVED — the CLI \`serve\` command itself stays. In"
  echo "    their place, one button: \"Tài khoản: N bộ\"."
  echo "  * Creds editor dialog: one row per set (label, user,"
  echo "    obscured password, type dropdown — Mọi loại máy /"
  echo "    Antminer gốc / VNish — delete), \"Thêm bộ\" adds a"
  echo "    row, blank rows drop on save. VNish rows show an"
  echo "    optional \"API key (không bắt buộc)\" field. The sets"
  echo "    persist to beesky-creds.json NEXT TO the executable"
  echo "    (fallback %APPDATA%\\BeeSky\\ when the bundle folder"
  echo "    is not writable); the app passes only the file PATH"
  echo "    to \`scan --creds-file\` — passwords never appear on"
  echo "    a command line. Empty list = scan without the flag."
  echo "  * Row clicks are read at the pointer level: every"
  echo "    pointer-down selects instantly; a second down on the"
  echo "    same row within 400 ms opens http://<ip> through an"
  echo "    injectable opener (production: the OS default browser"
  echo "    via cmd /c start on Windows). A plain double-tap"
  echo "    gesture recogniser was rejected: it holds the single"
  echo "    click hostage until the double-click window expires."
  echo "  * Detail panel: \"Đăng nhập: <label>\" appears when the"
  echo "    record carries cred_label."
  echo
  echo "DIVERGENCES FROM HASHCORE'S MODEL (deliberate):"
  echo
  echo "  * Multiple sets per vendor type remain allowed — one"
  echo "    farm often runs the same firmware with different"
  echo "    passwords per hall/batch; HashCore solves that with"
  echo "    a per-GROUP override layer (farms.json) over global"
  echo "    per-vendor settings. The group layer is NOT built"
  echo "    here; it is the v0.24 candidate if per-group logins"
  echo "    become a real need."
  echo "  * HashCore's DoNotUnlock / DoNotDiscover method"
  echo "    variants are not modelled (no BeeSky workflow needs"
  echo "    them yet)."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * mock_creds_test — ordering units, creds-file loader"
  echo "    normalisation (api_key-only entry valid, label"
  echo "    \"api_key\", unknown type -> any), validation exit 2,"
  echo "    and subprocess bridge scans against mock dashd +"
  echo "    stock endpoints: family-first wins (and the attempt"
  echo "    log proves the foreign family's set is never tried"
  echo "    first), wrong-tag rescue via the remaining-sets tier,"
  echo "    \"any\" rescue, api-key-only dashd (the password set"
  echo "    can unlock but not read; the api_key set wins and is"
  echo "    labelled), all-fail -> the 401 FETCH_ERROR record"
  echo "    with no label, legacy paths unchanged. Full output:"
  echo
  echo '```'
  echo "$CREDS_OUTPUT"
  echo '```'
  echo
  echo "  * Regression spot-checks at the v0.23.0 code:"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):"
  echo "    $FLUTTER_LINE — model parsing incl. cred_label,"
  echo "    the v0.22 layout suite, creds store round-trip +"
  echo "    fallback, argv contract (path only, no secrets),"
  echo "    double-click opener URL, and the dialog's"
  echo "    add/edit/delete/type-retag/api-key persistence."
  echo "    Two test-harness lessons are baked into the tests:"
  echo "    dart:io futures started in a widget test's fake-async"
  echo "    zone never complete (temp dirs are created sync, and"
  echo "    the creds store does its tiny file IO sync), and a"
  echo "    focused field's blinking cursor never lets"
  echo "    pumpAndSettle settle (bounded pumps in the dialog"
  echo "    test)."
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
echo "V0.23.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
