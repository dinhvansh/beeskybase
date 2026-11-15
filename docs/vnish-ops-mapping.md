# VNish ops tail — dashd api-doc → BeeSky behaviour mapping (v0.29.0)

Written BEFORE the port, per the dissect-before-porting discipline.
This release's spec source is **VNish's own documented API**: the
OpenAPI document shipped inside the dissected firmware
(`research/vnish/rootfs/usr/share/dashd/ui/docs/api-doc.json`, 41
endpoints, base `/api/v1`). Presentation is ported from the
HashCore Toolkit 1.7.5 materials on disk (en.json keys quoted;
`docs/operations-mapping.md` §2 for the 27-type universe). BeeSky
side claims are graded against CODE (file:line in
`beesky/core/actions.py` / `ops.py`).

Grades: **VERIFIED** (in the doc/materials), **INFERRED** (strongly
implied by shape, not stated), **UNKNOWN** (not observable — never
invented).

## 1. Auth model (VERIFIED, api-doc `components.securitySchemes`)

Two schemes: `bearerAuth` (JWT from `POST /unlock {"pw": ...}`) and
`apikeyAuth` (`x-api-key` header). Every write endpoint below
declares `[{bearerAuth}, {apikeyAuth}]` unless noted. This is
exactly the auth `DashdClient.post_json` already performs (API key
header, held JWT, or a JWT minted lazily from the password) — the
same resolution the shipped reboot/switch_pool use, fed by the
v0.23/v0.24 credential layers through the ops runner.

## 2. Per-action verdicts

| # | Candidate (HashCore type) | api-doc contract (VERIFIED) | Verdict |
|---|---|---|---|
| 2.1 | pause mining (`pause`, "Mining pause") | `POST /mining/pause`, NO body, bearer/apikey, 200/401/500 | **SHIP** ops type `pause_mining`, dashd-only |
| 2.2 | resume mining (`resume`, "Resume mining") | `POST /mining/resume`, same shape | **SHIP** `resume_mining`, dashd-only |
| 2.3 | mining restart (`restart`, "Restart mining") | `POST /mining/restart`, same shape | **SHIP** `restart_mining`, dashd-only. This UN-merges the v0.26 divergence for dashd (reboot stays the device reboot; cgminer keeps only its `restart`-RPC reboot — no second action is faked for it) |
| 2.4 | start / stop mining (no enum entry; Dart file map shows internal tasks only) | `POST /mining/start`, `POST /mining/stop`, same shape | **NOT SHIPPED** — not user-facing in the original (INFERRED internal building blocks); pause/resume cover the user-facing row |
| 2.5 | find-miner (`findMiner`, "Locating miner") | `POST /find-miner`: bodyless, **deprecated: true**, NO security declared, reply `null \| FindMinerStatus{on: bool}`. Successor `POST /locate-miner`: bodyless, NO security declared, reply `LocateMinerStatus{is_enabled: bool}` | **SHIP** `find_miner` via **/locate-miner only** (the deprecated twin is not used). No duration/on-off parameter exists in either contract — the call is bodyless, so the port sends no parameters (HashCore shows none either: no duration key exists in en.json); the per-device result reports the state the DEVICE returned (`is_enabled`), verbatim |
| 2.6 | throttle (`throttle`, "Throttle mode") | `POST /mining/throttle`, body `ThrottleSettings{percent: int32, required, min 20, max 100}`, reply `SaveConfigResult{restart_required, reboot_required}`, bearer/apikey. HashCore dialog VERIFIED (`miners_list.dialogs.throttle.*`): "Power level", "AVAILABLE RANGE: 20-100%", "RESET TO DEFAULT: 100%", "Reduces all chip frequencies proportionally, decreasing power consumption while maintaining heat generation" | **SHIP** `throttle` {percent}; the dialog ports HashCore's (range + default + explainer); the reply's restart/reboot flags surface in the result message |
| 2.7 | preset set (no HashCore task type) | No dedicated route. `OverclockSettingsRaw.preset` ("Profile name") lives inside `MinerConfigRaw`; the write path is `GET /settings` (apikeyAuth ONLY) → `POST /settings` (`InputConfig`) — the exact read-modify-write the shipped switch_pool url-form already performs | **SHIP** `set_preset` {preset: name} on that proven path, api-key requirement and all. Labelled an api-doc-grounded addition, NOT a HashCore task port (HashCore switches presets via the device profile/clone, not a task) |
| 2.8 | reset autotune profiles (`resetAutotuneProfiles`, desc "Reset all autotune profiles") | `POST /autotune/reset-all`, body `AutotuneResetAll{restart: bool, required}`, bearer/apikey | **SHIP** `reset_autotune_all` {restart = true default} |
| 2.9 | reset current profile (`resetCurrentAutotuneProfile`, desc "Reset single autotune profile") | `POST /autotune/reset`, body `AutotuneReset{presets: [string], restart: bool}` (both required); the current preset's name comes from `GET /perf-summary` (NO security declared) → `PerfSummary.current_preset.name` (`AutotunePresetsItem{name, pretty, status}`) | **SHIP** `reset_autotune_current`: read perf-summary, reset `[current name]`; a device reporting no current preset fails honestly. A raw arbitrary-list reset form is NOT a separate type (no HashCore user-facing twin) |
| 2.10 | configure API key (`configureApiKey`, "Api key config") | `POST /apikeys`, body `ApiKeysJsonItem{key: string len 32, description: string}`, reply `AddApiKeyRes{status: inserted \| updated \| nochan
...[truncated 5269 chars]