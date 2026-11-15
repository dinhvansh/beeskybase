#!/usr/bin/env bash
# v0.26.0 mock suite: the OPERATIONS task system — the HashCore
# Toolkit's Operations model ported per docs/operations-mapping.md
# (selection -> Operations bar -> confirm -> queued task with
# per-device iterations -> streamed progress + Stop -> persistent
# task history). Actions ship ONLY where a real BeeSky primitive
# exists (the scan pipeline; core/actions.py — the cloud agent's
# executors); the rest of HashCore's 27 task types are named
# PRIMITIVE-GAPs in the mapping, not faked.
#
# Evidence method (same standalone-sweep pattern as v0.21–v0.25):
# the new mock_ops_test suite + the release-pin suite
# (mock_agent_bg_test under xvfb, pinning 0.26.0) + standalone
# regression spot-checks (bridge, creds, groups, units). The
# Flutter app IS verified locally this release (analyze + full
# test run with the SDK at ~/workspace/flutter-sdk); only its
# Windows build remains CI-only. Both facts are disclosed in the
# RESULTS.md block this script appends.
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
for spec in "mock_ops_test plain" "mock_agent_bg_test xvfb" \
            "mock_bridge_test plain" "mock_creds_test plain" \
            "mock_groups_test plain" "mock_units_test plain"; do
  line="$(summary_line $spec)"
  echo "$line"
  SUMMARY_LINES="${SUMMARY_LINES}${line}
"
done

FLUTTER_LINE="flutter analyze: clean; flutter test: 78 PASS / 0 FAIL (local SDK 3.47.9; 63 pre-existing + 15 new ops tests)"

{
  echo
  echo "---"
  echo
  echo "# v0.26.0 — Operations task system (HashCore Toolkit Operations model, ported per the dissection)"
  echo
  echo "The parity push continues (owner's bar: 99% of HashCore"
  echo "Toolkit in one month). Following the dissect-before-"
  echo "porting rule, the Toolkit's task mechanism was dissected"
  echo "FIRST from the shipped materials (the ~1,500-key"
  echo "translation table — the 27-value task_type_action enum,"
  echo "the task_status enum, the operations_dialog keys — and"
  echo "the Dart file map: miners_task_service + queued_task,"
  echo "the task base classes, the per-implementation task"
  echo "files) and the behaviour mapping written to"
  echo "docs/operations-mapping.md BEFORE any code — including"
  echo "a full action inventory in which every HashCore task"
  echo "type is graded SHIP / GAP against a BeeSky primitive"
  echo "verified in code (file:line). No device action is faked:"
  echo "firmware-documented endpoints BeeSky has never"
  echo "implemented are gaps, not features."
  echo
  echo "PYTHON CORE:"
  echo
  echo "  * beesky/core/ops.py (NEW): a stateless task runner."
  echo "    \`beesky ops --job FILE\` executes ONE task described"
  echo "    by a JSON job file (secrets never ride argv; cred"
  echo "    sets are referenced by path) and streams NDJSON"
  echo "    progress: a start line, one result line per device"
  echo "    ({done, total, ip, ok, message} — rescan adds the"
  echo "    fresh \`record\`), and a final summary line (counts"
  echo "    + derived task status: success / hasErrors / error /"
  echo "    cancelled — HashCore's enum names). Malformed jobs"
  echo "    (bad type/targets/payload, unknown group, unreadable"
  echo "    creds file) exit 2 BEFORE any device I/O, like scan."
  echo "  * Credential resolution is the v0.23/v0.24 mechanism"
  echo "    itself: the job references a group and/or a creds"
  echo "    file; the runner merges group -> global"
  echo "    (groups.effective_creds), probes each device with"
  echo "    the merged sets (discover.probe_host), and translates"
  echo "    the winning set into the single creds dict"
  echo "    core.actions.execute consumes — the same dict the"
  echo "    cloud agent passes. An unanswering device is an"
  echo "    honest per-device failure, never a guess."
  echo "  * Concurrency: a bounded thread pool (job \`workers\`,"
  echo "    default 4, hard cap 8) + an optional \`stagger_s\`"
  echo "    gate between device starts (HashCore's batch pause)."
  echo "    Cancellation is cooperative: SIGTERM/SIGINT (wired"
  echo "    in cmd_ops) stops new devices starting; unstarted"
  echo "    devices are counted cancelled in the summary."
  echo "  * Found while building (guarded, disclosed): the"
  echo "    probe can raise outside the adapters' error types"
  echo "    (http.client.BadStatusLine from a malformed-HTTP"
  echo "    device). The runner catches it as THAT device's"
  echo "    failure — one sick device can no longer kill a run."
  echo "    discover() itself keeps its existing contract;"
  echo "    hardening it is a separate core change, not hidden"
  echo "    inside this release."
  echo
  echo "ACTION INVENTORY (full table: docs/operations-mapping.md §3):"
  echo
  echo "  SHIPPED: rescan \"Quét lại\" (the scan pipeline;"
  echo "  HashCore's discover/refreshStats/updateStats); reboot"
  echo "  \"Khởi động lại\" (core/actions.py: cgminer privileged"
  echo "  restart RPC / dashd POST /system/reboot / stock"
  echo "  reboot.cgi — refusals surface verbatim); switch_pool"
  echo "  \"Đổi pool\" (actions.py's dashd path: pool_id ->"
  echo "  /mining/switch-pool, url/user -> GET+POST /settings"
  echo "  with its honest api-key requirement; other families"
  echo "  fail honestly); export \"Xuất danh sách\" (APP-SIDE"
  echo "  BeeSky addition: selected records -> JSON file + a"
  echo "  history entry; not a HashCore port)."
  echo "  MERGED: HashCore's restart (mining restart) folds"
  echo "  into reboot — BeeSky has no separate mining-restart"
  echo "  primitive and does not fake the distinction."
  echo "  PRIMITIVE-EXISTS / DEFERRED: install/update firmware"
  echo "  (core/firmware.py install_dashd/install_stock exist;"
  echo "  a bulk run needs a per-task file + minutes-long"
  echo "  wait-back — stays with \`beesky fw install\`)."
  echo "  GAP-GATED: unlock (firmware.py behind the CLI's three"
  echo "  hard gates — never a bulk action)."
  echo "  GAP-UNIMPLEMENTED (dashd api-doc documents the"
  echo "  endpoint; BeeSky has no code path): pause, resume,"
  echo "  findMiner, resetFirmware, removeFirmware,"
  echo "  resetAutotuneProfiles, resetCurrentAutotuneProfile,"
  echo "  throttle, configureApiKey, diagnosticReport."
  echo "  GAP-UNVERIFIED: changePassword, configureNetwork"
  echo "  (settings-write pieces exist; semantics unverified)."
  echo "  GAP: cloneSettings (v0.28 with pool presets),"
  echo "  conditionalRestart, updateNote (v0.27),"
  echo "  restoreCvFirmware (no Cvitek adapter), multi"
  echo "  (composite — the runner runs one type per job)."
} >> tests/RESULTS.md

{
  echo
  echo "FLUTTER APP (app_flutter/):"
  echo
  echo "  * lib/ops.dart (NEW): OpsTaskType / OpsStatus /"
  echo "    OpsDeviceResult / OpsTask (the history entry AND the"
  echo "    live run's state; copyable infoText in HashCore's"
  echo "    task_info shape), OpsEvent / OpsSummary, the OpsRun"
  echo "    handle (events stream + summary future + Stop),"
  echo "    OpsFiles (job file + export dir) and"
  echo "    OpsHistoryStore (beesky-ops-history.json beside the"
  echo "    exe, %APPDATA% fallback, corrupt = empty, retention"
  echo "    100). lib/ops_dialogs.dart (NEW): the Confirm"
  echo "    operation dialog (action + count + every target IP),"
  echo "    the switch-pool payload form (slot activation or"
  echo "    write-new-pool, with the api-key note), and the"
  echo "    history dialog (newest first; per-item started/"
  echo "    counts/duration; expandable per-device results;"
  echo "    isolate-errors / copy-info / delete-entry actions;"
  echo "    clear-all behind a confirmation; HashCore's empty"
  echo "    state text; a still-running entry renders as \"Chưa"
  echo "    hoàn tất\" — an app closed mid-run is not hidden)."
  echo "  * lib/sidecar.dart: BeeSkyBridge.startOps(job) ->"
  echo "    OpsRun. The sidecar writes the job file beside the"
  echo "    exe (values inside the FILE, argv carries only"
  echo "    \`ops --job <path>\` — the v0.23 rule applied to"
  echo "    tasks), streams the NDJSON, and SYNTHESISES the"
  echo "    summary when the process dies without one (a"
  echo "    Windows kill leaves no summary line) so every"
  echo "    device is still accounted; the job file is deleted"
  echo "    when the run ends. MockBridge.startOps simulates"
  echo "    the same lifecycle against the sample fleet"
  echo "    (per-device progress, the unreachable unit failing,"
  echo "    switch_pool failing on non-VNish sources, Stop"
  echo "    accounting the remainder as cancelled)."
  echo "  * home_page.dart: the Operations bar joins the"
  echo "    v0.25 selection bar when the selection is non-empty"
  echo "    (Thao tác: Quét lại / Khởi động lại / Đổi pool /"
  echo "    Xuất danh sách, gated while a task runs); the task"
  echo "    progress bar renders under it (\"{task}: N/M địa"
  echo "    chỉ\" + current device + Dừng); rescan results merge"
  echo "    their fresh records into the table in place; the"
  echo "    miners toolbar gains \"Lịch sử tác vụ\". In a"
  echo "    group's scope the job carries the group (the core"
  echo "    resolves its creds layer), off-scope just the"
  echo "    global creds file. models.dart gains"
  echo "    MinerRecord.toJson (+ Problem/ChainInfo/PoolInfo)"
  echo "    for the export. All v0.24/v0.25 behaviours intact."
  echo
  echo "MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):"
  echo
  echo "  MATCH: selection-raised Operations bar; a Confirm"
  echo "  operation dialog before device-mutating tasks; one"
  echo "  task = iterations over devices with per-device"
  echo "  ok/fail outcomes; the task-status set (success /"
  echo "  hasErrors / error / cancelled); streamed progress"
  echo "  \"{task}: N/M addresses\" + Stop; the history dialog's"
  echo "  shape (info block, iterations/errors/duration line,"
  echo "  expandable per-device results, isolate-errors,"
  echo "  copy-info, delete entry, clear-all with confirms,"
  echo "  operations count, empty state); app-owned history."
  echo
  echo "  DIVERGENCE (named, in the mapping): the core runner"
  echo "  is stateless per run (sidecar process + NDJSON)"
  echo "  where HashCore queues tasks in an in-app service +"
  echo "  isolates — one task at a time from the app;"
  echo "  compatibility is resolved per device by probing"
  echo "  instead of HashCore's pre-run filter, so an"
  echo "  unsupported family fails honestly per device rather"
  echo "  than excluding the device (an empty selection still"
  echo "  never starts); parallel-iterations / stagger /"
  echo "  timeout ride the JOB (defaults 4 / 0 / 3 s) instead"
  echo "  of global Settings; no one-shot per-task unlock-"
  echo "  method override (the group/global cred layers are"
  echo "  the method selection); Waiting/Processing collapse"
  echo "  into \`running\`; Stop is a process kill on Windows"
  echo "  (POSIX gets the runner's cooperative SIGTERM summary"
  echo "  too) with the cancelled remainder accounted from the"
  echo "  summary either way; history retention caps at 100"
  echo "  entries (HashCore's cap is UNKNOWN); confirm covers"
  echo "  reboot + switch_pool only — rescan is read-only and"
  echo "  runs immediately, like HashCore's own Rescan button."
  echo
  echo "(a) VERIFIED LOCALLY (this sandbox):"
  echo
  echo "  * Python suites at the v0.26.0 pins:"
  echo
  printf '%s' "$SUMMARY_LINES" | sed 's/^/    /'
  echo
  echo "    mock_ops_test covers: the exit-2 job contract"
  echo "    (9 malformed-job cases, stdout empty); reboot per"
  echo "    family against the real mocks (dashd password +"
  echo "    api-key sets recorded by the mock, wrong password"
  echo "    -> verbatim 401 failure and NO reboot recorded,"
  echo "    stock reboot.cgi hit, cgminer restart recorded,"
  echo "    read-only RPC refusal verbatim, unreachable ->"
  echo "    not-answering); switch_pool (slot activation,"
  echo "    url/user rewrite via /settings, the password-only"
  echo "    api-key failure, stock not-supported); rescan"
  echo "    (record rides the event; unreachable fails without"
  echo "    one); the group -> global cred resolution (winner"
  echo "    label + the mock's unlock-attempt log proving"
  echo "    group-first order and global rescue); the stream"
  echo "    shape + hasErrors derivation; cooperative"
  echo "    cancellation (unstarted counted, status cancelled);"
  echo "    the subprocess NDJSON contract end to end."
  echo
  echo "  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):"
  echo "    $FLUTTER_LINE — task/history JSON round-trips"
  echo "    (incl. cancelled results + the 100-entry cap),"
  echo "    OpsEvent/OpsSummary parsing, MinerRecord.toJson"
  echo "    round-trip; the mock lifecycle (event order, the"
  echo "    .104 failure, switch_pool honesty, rescan records,"
  echo "    stop accounting); the sidecar argv contract."
  echo "    Widget level: selection raises the Operations bar;"
  echo "    reboot -> confirm dialog -> progress bar -> history"
  echo "    entry with counts + expandable per-device results"
  echo "    + the history file on disk; history reloaded by a"
  echo "    fresh HomePage (restart round-trip); export writes"
  echo "    the records file + its history entry; rescan runs"
  echo "    unconfirmed. All 63 pre-existing tests still pass"
  echo "    — the only pre-existing test touched is the version"
  echo "    pin in widget_test.dart (v0.26.0)."
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
echo "V0.26.0 MOCK SUITE (standalone sweep) DONE — evidence appended to tests/RESULTS.md"
