# Operations task system — HashCore Toolkit → BeeSky behaviour mapping (v0.26.0)

Written BEFORE the port, per the dissect-before-porting discipline.
Every HashCore claim below is graded:

- **VERIFIED** — seen in the shipped Toolkit 1.7.5 materials on disk:
  the full translation table (`toolkit-x64/data/flutter_assets/assets/
  translations/en.json`, keys quoted), the Dart file map
  (`toolkit-x64/package-paths.txt`), and prior analysis
  (`research/hashcore/UI-ANALYSIS.md` §2.2).
- **INFERRED** — strongly implied by structure/naming, not observed.
- **UNKNOWN** — not observable from the materials on disk. The port
  does NOT invent these; where BeeSky must choose, the choice is
  marked DIVERGENCE.

Every BeeSky action claim is graded against CODE: an action ships
only when a real primitive exists in this repository (file:line
cited). Firmware-documented endpoints BeeSky has never implemented
are GAPs, not features.

---

## 1. The HashCore task model

| # | HashCore behaviour | Grade |
|---|---|---|
| 1.1 | Tasks are launched from the miners list: selecting devices raises an **Operations bar** (`miners_list.action_control.operations_bar` = "Operations bar", `selected` = "{count} selected") with quick actions (Rescan, Clone, Unlock…) and an **"All commands"** menu (`action_control.commands`); tasks also hang off the per-device context menu (`menu/miner_list_item_commands_menu/tasks_menu.dart`). | VERIFIED |
| 1.2 | A **"Confirm operation"** dialog precedes execution (`miners_list.dialogs.confirm_task`, `dialogs/task_confirmation_dialog/task_confirmation_dialog.dart`). | VERIFIED |
| 1.3 | Execution is queued and serviced by a dedicated service: `toolkit_services/services/miners_task_service/miners_task_service.dart` + `queued_task.dart`; tasks run inside isolates (`services/isolate_service/isolated_task.dart`). | VERIFIED (file map) |
| 1.4 | A task's unit of work over one device is an **iteration**; per-device control flow uses exceptions `TaskAbortException` / `TaskSkipException` (`toolkit_services/exceptions/`). Task states live in `models/tasks/base/task_state.dart`; base classes `Task` / `MinersTask` / `NotifiableTask` / `VoidResultMinersTask`. | VERIFIED (file map) |
| 1.5 | Task statuses (`enum.task_status`): `notStarted` "Waiting", `processing`, `success`, `hasErrors`, `error`, `cancelled`. | VERIFIED |
| 1.6 | Progress shows in the app-screen header (`app_task_progress.dart`, `task_progress_details.dart`): `miners_list.progress_bar.progress` = "{task} progress: ", `addresses` = "{count} address(es)", a **Stop** button; after completion `progress_bar.result` = "{task} result: " plus a **Rescan** button. | VERIFIED |
| 1.7 | Notifications (`notifications.*`): "{task} started", "{task} successfully completed", "{task} was completed with errors", and a NOT-STARTED notice: "{task} not started: No compatible devices selected" — i.e. **tasks pre-filter the selection by device compatibility** before running. | VERIFIED |
| 1.8 | Concurrency/throttling are user Settings: `settings_dialog.advanced.task_iterations` = "Parallel task iterations" ("Limits network load"); `settings_dialog.timeouts.group_operation_timeout_*` = "Batch operations — Adds a pause to batch operations to prevent devices from executing a task simultaneously" (a stagger); `task_timeout` = "Task timeout — Limits single miner command timeout", with the invariant "Task timeout can't be less than any other timeout". | VERIFIED |
| 1.9 | One-shot per-task unlock methods exist (`settings_dialog.unlock.task_methods_title` = "Unlock method for selected device") — a task may override the vendor method for that run, the third layer over global → group (§3 of the v0.23 mapping). | VERIFIED |
| 1.10 | **Task history** is the Operations dialog (`operations_dialog.title` = "Operations", subtitle "Task history"). A history item shows: task name; `task_info` = "{task}\n\nstarted: {start}; finished: {end}; duration: {duration}\ntotal iterations: {total}, completed: {completed}, errors: {errors}\n{error_info}"; list lines "Iterations: N / Errors: M / Duration: D"; status summaries Success / "Contains errors" / Error / "Waiting: {count}" / "Completed: {count}" / "Task queued. Waiting" / "Iteration: {nr}"; per-item outcomes "Success" / "Not completed" / "No details available". Item actions (tooltips): **isolate devices with errors**, **copy task information**, **delete from task history**, **stop task**; header: **clear history**, totals "{count} operation(s)". Deletion/clear/stop all ask first (`remove_confirmation.*`). Empty state: "Task history is empty — Run any command from the list action bar to add a history item". | VERIFIED |
| 1.11 | Whether history persists across app restarts, its storage medium and any retention cap. | UNKNOWN — no history repository/store file appears in the Dart file map; the dialog is app-side. |

## 2. The HashCore task-type universe

`miners_list.dialogs.enum.task_type_action` carries **27 user-facing
types**, grouped by `enum.task_category` (Operations / Firmware /
Power actions / Security / System / CLI / Uncategorized):

changePools, resetAutotuneProfiles, resetCurrentAutotuneProfile,
diagnosticReport, throttle, installFirmware, updateStockFirmware,
updateFirmware, resetFirmware, removeFirmware, pause, resume,
restart, reboot, changePassword, configureApiKey, findMiner,
cloneSettings, unlock, discover, refreshStats, updateStats,
conditionalRestart, restoreCvFirmware, multi, configureNetwork,
updateNote.

The Dart file map shows additional implementation-only tasks with no
enum entry (start, stop, switchPool, getMetrics, getPoolDetails,
add/removeApiKey) — internal building blocks, INFERRED.

## 3. BeeSky action inventory — primitive or GAP (verified in code)

| HashCore type | BeeSky evidence | Verdict |
|---|---|---|
| discover / refreshStats / updateStats | The scan pipeline itself: `core/discover.py:184 probe_host` + the cli fetch stage (DashdClient/BitmainClient.fetch_record, cgminer summary+stats → `core/report.py:234 build_record`). | **SHIP** as ops type `rescan` — "Quét lại". The runner re-probes + re-fetches each target; the fresh record rides the progress event so the app updates the row. |
| reboot | `core/actions.py:191 execute()` → cgminer privileged `restart` RPC (actions.py:65), dashd `POST /api/v1/system/reboot` (actions.py:87), stock `GET /cgi-bin/reboot.cgi` (actions.py:100). Already exercised end-to-end by the cloud agent path (agent.py:268 `_run_commands`). | **SHIP** as `reboot` — "Khởi động lại", all three families, honest refusals (e.g. read-only cgminer API) surfaced verbatim. |
| restart (mining restart, distinct from reboot) | dashd's api-doc documents `POST /mining/restart`, but NO BeeSky code path calls it; the cgminer `restart` RPC is already BeeSky's reboot for that family. | **MERGED into reboot** — DIVERGENCE: BeeSky does not distinguish mining-restart from device reboot; no separate action is offered rather than faking one. |
| changePools | `core/actions.py:118 _switch_pool_dashd`: payload `{"pool_id": N}` → `POST /mining/switch-pool`; payload `{"url","user","password"}` → GET + POST `/settings` then switch (the GET is api-key-only per the api-doc, enforced at actions.py:144). dashd ONLY; cgminer/stock return the honest "not supported for this source yet". | **SHIP** as `switch_pool` — "Đổi pool", dashd-scoped with truthful per-device failures on other families. Pool PRESETS stay v0.28; the payload form is this release's input. |
| installFirmware / updateFirmware / updateStockFirmware | Primitives EXIST: `core/firmware.py:256 install_dashd` (POST /api/v1/firmware/update), `firmware.py:280 install_stock` (upgrade.cgi), plus `firmware.py:301 wait_back`. | **NOT SHIPPED — PRIMITIVE-EXISTS / DEFERRED**: a bulk run needs a per-task firmware file and a minutes-long wait-back per device; firmware install stays with the deliberate one-device `beesky fw install` flow. Named here so the omission is a decision, not an oversight. |
| unlock | `core/firmware.py:351 unlock()` exists behind the CLI's three hard gates (owner-supplied .bmu payloads, `--experimental-unlock` + env `BEESKY_ALLOW_UNLOCK=1` + typed-IP confirmation). | **GAP-GATED**: never a bulk Operations action. |
| pause / resume (+ internal start/stop) | api-doc documents `POST /mining/pause`, `/mining/resume`, `/mining/start`, `/mining/stop`; no BeeSky code path calls any of them. | **GAP-UNIMPLEMENTED** (documented endpoint ≠ primitive). |
| findMiner | api-doc documents `POST /find-miner` and `/locate-miner`; no BeeSky code. | **GAP-UNIMPLEMENTED**. |
| resetFirmware | api-doc documents `POST /settings/factory-reset`; no BeeSky code. | **GAP-UNIMPLEMENTED**. |
| removeFirmware | api-doc documents `POST /firmware/remove`; no BeeSky code. | **GAP-UNIMPLEMENTED**. |
| resetAutotuneProfiles / resetCurrentAutotuneProfile | api-doc documents `POST /autotune/reset-all`, `/autotune/reset`; no BeeSky code. | **GAP-UNIMPLEMENTED**. |
| throttle | api-doc documents `POST /mining/throttle`; no BeeSky code. | **GAP-UNIMPLEMENTED**. |
| configureApiKey | api-doc documents `/apikeys` GET/POST/delete; BeeSky only ever SENDS an api key, never provisions one. | **GAP-UNIMPLEMENTED**. |
| diagnosticReport | api-doc documents `/logs/{type}` + `/settings/backup`; BeeSky's `core/report.py` tickets are LOCAL repair tickets, not device diagnostic downloads. | **GAP-UNIMPLEMENTED** (the local tickets flow already exists separately in the app). |
| changePassword | The settings write schema carries a "password" section (passed through at actions.py:153), but no BeeSky code performs a device password change and the section's semantics are unverified. | **GAP-UNVERIFIED**. |
| configureNetwork | Same settings-write mechanism, no implementation, semantics unverified. | **GAP-UNVERIFIED**. |
| cloneSettings | Settings GET/POST exist only inside the switch_pool path; no read-from-A/write-to-B clone exists. | **GAP** — clone + pool presets are v0.28 scope. |
| conditionalRestart | No stats-evaluation → restart logic exists in the codebase. | **GAP-NO-PRIMITIVE**. |
| multi | HashCore's composite task. The BeeSky runner executes ONE type per job; the app can chain jobs. | **NOT A TYPE** — DIVERGENCE, named. |
| updateNote | BeeSky records carry no per-device note (device-detail scope). | **GAP-DEFERRED** to v0.27. |
| restoreCvFirmware | Cvitek-only; BeeSky has no Cvitek adapter at all. | **GAP-NO-ADAPTER**. |
| — (no HashCore counterpart) | "Xuất danh sách": the app serialises the SELECTED records to a JSON file locally and records a history entry. HashCore's nearest is the device-side diagnosticReport export — a different thing. | **SHIP app-side** (coordinator-scoped), labelled as a BeeSky addition, not a port. |

## 4. The port — behaviour mapping

| # | HashCore | BeeSky v0.26 |
|---|---|---|
| 4.1 | Task object: type + device set + state + per-iteration outcomes (§1.4). | MATCH in shape: job = `{type, targets[], payload?, group?, creds_file?, groups_file?}`; task record = `{id, type, created_at, finished_at, status, targets, results[{ip, ok, message}]}` (docs §5). |
| 4.2 | Statuses Waiting/Processing/Success/Has errors/Error/Cancelled (§1.5). | MATCH: task status derives as `running` → `success` / `hasErrors` / `error` / `cancelled` from per-device results (failed==0 → success; 0<failed<completed → hasErrors; completed==0 with failures → error; stop requested → cancelled). The enum's Waiting/Processing collapse into `running` (the bridge streams progress; no queue-wait state is observable). |
| 4.3 | Queued service + isolates (§1.3). | DIVERGENCE (architecture): the CORE runner (`beesky/core/ops.py`) is stateless per run — the app spawns `beesky ops --job FILE` as a sidecar process and consumes its NDJSON event stream; a bounded thread pool (≤8) replaces isolates. One task at a time from the app (the bridge refuses a second while one runs). |
| 4.4 | Compatibility pre-filter; a task over only-incompatible devices never starts (§1.7). | DIVERGENCE: BeeSky resolves each device's family by probing it (the v0.23/v0.24 cred resolution), so compatibility is known only per device at run time; an unsupported family yields an honest per-device failure from `actions.execute` instead of pre-exclusion. An EMPTY selection still never starts a task (app-side guard, matching the notice's intent). |
| 4.5 | Parallel iterations + optional stagger pause + per-command timeout are global Settings (§1.8). | ADAPTED: they ride the JOB — `workers` (default 4, hard cap 8), `stagger_s` (default 0), `timeout` (default 3.0 s). The app uses the defaults in v0.26; no Settings UI yet. The stagger keeps its HashCore purpose: devices don't all execute at the same instant. |
| 4.6 | Cred resolution per task: global → group → one-shot task method (§1.
...[truncated 2085 chars]
## 6. Status update — v0.29.0 (the VNish ops tail)

The §3 gap list above is updated by v0.29.0, whose own
mapping (docs/vnish-ops-mapping.md) dissects dashd's
api-doc directly. In short: pause / resume **SHIPPED**
(`pause_mining` / `resume_mining`); restart **UN-merged**
and shipped for dashd (`restart_mining`);
findMiner **SHIPPED** (`find_miner` via /locate-miner);
throttle **SHIPPED**; resetAutotuneProfiles /
resetCurrentAutotuneProfile **SHIPPED**
(`reset_autotune_all` / `reset_autotune_current`);
configureApiKey **SHIPPED**; diagnosticReport **SHIPPED
as a labelled BeeSky variant** (record + inspect bundle;
no dashd diagnostics endpoint exists); changePassword
**SHIPPED** (PasswordChange contract verified in the
doc; partial-write semantics INFERRED, hardware-
unconfirmed). Still gaps: conditionalRestart (no
documented condition source), resetFirmware /
removeFirmware (this release's safety scope —
firmware-family actions stay deliberate), configureNetwork
(GAP-UNVERIFIED, unchanged), install/update firmware
(DEFERRED to `beesky fw`, unchanged), unlock (GAP-GATED,
unchanged), restoreCvFirmware (no adapter), cloneSettings
(pool-scoped clone shipped in v0.28; full-profile clone
still has no write primitive for the non-pool sections).
The full per-action table with endpoints and auth lives
in tests/RESULTS.md (v0.29.0 section).
