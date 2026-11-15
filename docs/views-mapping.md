# v0.32.0 — The five remaining views + the sidecar fix: dissection & mapping

Written BEFORE the build, per the dissect-before-porting rule. The
"originals" here are BeeSky's OWN existing implementations (the
`beesky serve` web dashboard, the cloud dashboard/store, the core
event engine, the ticket writer) plus the owner's first
real-Windows test of v0.31.1 (2026-11-12), which is the ground
truth for Workstream B.

## Workstream B — the sidecar failure (owner's photos, 2026-11-12)

**Observed.** The owner's folder holds ONLY the BeeSkyFlutter zip's
contents (`beesky_app.exe` + `flutter_windows.dll` + `data/`) —
`beesky.exe` was never placed beside the app, and no Defender
involvement is evidenced. The app ran, but the sidebar foot read
"Ruột quét: không nối được", a scan failed with
`Lỗi quét: Không chạy được beesky (beesky): The system cannot find
the file specified`, and ticket export showed the RAW text
`ProcessException: … Command: beesky scan 192.168.1.0/24 --tickets .\tickets`.

**Root cause in code** (`app_flutter/lib/sidecar.dart`,
`SidecarBridge.resolveBeeSkyExe`): resolution steps 1–4 are sound
(explicit override → `BEESKY_EXE` env → `--dart-define` → sibling
`beesky.exe`), but step 5 falls back to the BARE NAME `'beesky'`
when no sibling exists. Every bridge call then spawns a name
Windows cannot find, and the failure surfaces as raw OS text:

- `_runJson` wraps it as `Không chạy được beesky (beesky): <OS text>`
  (scan / sysinfo / inspect / group scan);
- `exportTickets` had NO try/catch around `Process.run` at all, so
  the `ProcessException` escaped unwrapped — the owner's third photo;
- `startOps` wrapped it with the same raw text.

The sidebar already KNEW the truth — `_sidecarStatus()` checks
`exe.contains(separator) && !File(exe).existsSync()` — but with the
bare-name fallback the exe path contained no separator, so even
that check could not fire; the pill fell through to the generic
"không nối được".

**The port (fix).**

| # | Behaviour | Fix |
|---|-----------|-----|
| B1 | Resolution | On Windows, when no sibling `beesky.exe` exists, resolve to the EXPLICIT sibling path (`<app exe dir>\beesky.exe`) anyway — the two shipped layouts (installer, portable zip) always place it there, so a missing file is a knowable state, not an opaque spawn failure. POSIX keeps the bare-`beesky` PATH fallback (dev machines with the package installed — the core's own documented dev route). Env / dart-define overrides unchanged, and an override that names a missing file is treated as missing too. |
| B2 | One message | Every bridge entry point (sysinfo, scan, group scan, inspect, ops start, ticket export) checks `exeMissing` BEFORE spawning and throws `SidecarException(missingSidecarMessage)`; a `ProcessException` racing a deletion maps to the same text. `exportTickets` gains the missing try/catch. The message (owner-facing, verbatim): "Không tìm thấy beesky.exe cạnh app — hãy giải nén app vào cùng thư mục với beesky.exe (hoặc cài bằng BeeSkySetup), và kiểm tra Windows Defender > Protection history nếu file bị cách ly." |
| B3 | Status pill | The missing state reads "Chưa có ruột quét (thiếu beesky.exe)" (was: unreachable branch + generic "không nối được" fallthrough). |
| B4 | Packaging | From v0.32 the portable zips are SELF-CONTAINED (see §Packaging) — B1–B3 remain as the honest failure mode for partially-copied folders, PATH-only installs and quarantined files. |

## Workstream A — the five views

Sidebar state before: Nhóm mạng + Máy đào real; Bản đồ nhiệt /
Điện năng / Lịch sử sửa / Sự kiện / Cài đặt greyed with "SAU" tags.

### 1. Bản đồ nhiệt — original: `beesky serve` web dashboard (v0.8)

Source: `beesky/web/dashboard.html` (`heatColor`, `heatTile`,
`renderHeatmap`). The Tk GUI has NO heat map (checked: gui.py only
shows temps in the detail text) — the web dashboard is the
original. Data: the CURRENT scan records only (`/api/miners`
payload = latest pass); no history.

- Tiles sorted by numeric IP; tile shows last octet (big), temp
  at 0 dp, and `ip · rate` (0 dp) small.
- Band colours on `max_temp_c`, EXACT web hexes: `<60 #14532d` ·
  `60–70 #4a5d23` · `70–80 #7a5a12` · `80–90 #8a4512` ·
  `≥90 #8a1f1a` · `null #2c2c2c`.
- Offline (a `FETCH_ERROR` problem) → grey tile, "Offline" in
  place of the temp, no band colour.
- Problem miner (status ≠ OK, not offline) → red border
  (`.tile.problem`).
- Tooltip: `ip · model · <OK|Cần kiểm tra|Mất kết nối>` +
  ` · N vấn đề` when problems exist.
- Empty fleet → "Chưa phát hiện máy nào — kiểm tra lại mục tiêu quét."

Mapping to the port: a dedicated view over ALL current records
(the v0.25 Overview heat-grid is a different surface — it renders
the miners view's FILTERED pipeline with HashCore's S/M/L cells
and share-of-best hashrate mode; it stays as-is). Divergences,
named: (a) tile click selects the miner and jumps to Máy đào (the
web original is display-only; the click is a BeeSky addition);
(b) the band hexes render as tile BACKGROUNDS at reduced alpha
over the app's dark theme instead of flat fills, keeping the
app's text legible — band identity (which band, which colour
family) is unchanged; (c) before the first scan the view shows
the app's standard "Chưa quét" empty state, the web text is used
once a scan found nothing.

### 2. Điện năng — original: cloud energy report (v0.9/v0.12)

Source: `beesky/cloud/store.py::energy_report` over the
`energy_hours` table (integrated agent-side from pushed power
samples), price from cloud settings `electricity_price_vnd_kwh`,
**default 2000 VNĐ/kWh** (`electricity_price_vnd()`); the cloud
dashboard renders today / per-day / per-miner with estimated cost.
That history is CLOUD-ONLY (fed by farm agents) — no local store
integrates power over time today.

Local data that DOES exist, and the port's scope (stated in the
view itself + RESULTS.md):

- Current fleet: records carry `power_w` (dashd + some cgminer;
  classic bmminer reports none). Fleet kW now, estimated
  kWh/day = kW × 24, estimated cost/day at the configured price,
  plus the honest coverage count (N of M miners reporting power).
- Saved samples: `beesky-history.json` samples carry `power_w`
  per device (v0.27). The view integrates them over the last
  7 days: per interval, energy = earlier sample's power × Δt,
  intervals longer than 30 min are skipped (the miner/app state
  in between is unknown — named choice), each interval is
  attributed to its start sample's local day. Outputs: window
  total kWh + est. cost, per-day rows, per-device rows (top
  first) — the cloud report's three shapes, over local data.
- No power data anywhere → the cloud panel's honest empty state,
  adapted: "Chưa có dữ liệu điện — nguồn máy chưa báo công suất."

### 3. Lịch sử sửa — originals: ticket files (local) / cloud repairs

Local original: `beesky/core/report.py::write_tickets` — one
`ticket-<ip with . → _>.txt` per problem miner, plain-text
Vietnamese ticket (`make_ticket`: header, IP/Model/Hashrate/
uptime/chips, "Vấn đề phát hiện:" bullet lines, per-board detail,
suggestions). Written by `scan --tickets DIR`; the Flutter app's
export stages them into `<sidecar dir>/tickets`. The files carry
NO status and NO timestamp — the file's mtime is the only date.
(Cloud `repairs` rows DO carry status, but they live in the
cloud's SQLite — not reachable locally; inventing a local status
would be fabrication, so the port shows none. Named in RESULTS.)

Port: a new READ-ONLY bridge verb in the established style —
`beesky tickets --dir DIR --json` → one JSON document
`{"tickets": [{file, ip, modified, model, problems[], text}]}`,
newest first (mtime desc); a missing dir is `{"tickets": []}`,
exit 0. Parsing lives in `report.list_tickets` (the ticket
format's owner): ip from the filename, model from the `Model:`
line, problems = the bullet lines of the "Vấn đề phát hiện:"
section. The view lists tickets (IP · model · export date ·
problem count); a tap opens the full text. Empty state names
the export button that creates them.

### 4. Sự kiện — original: the core EventEngine (watch / serve)

Source: `beesky/core/events.py` — diffs successive scan passes
of ONE target: OFFLINE / BACK_ONLINE / HASHRATE_DROP / OVER_TEMP /
CHIPS_LOST / CHAIN_DOWN with the EMCD-style severity ladder
(info/warning/major/critical), anti-flap latches + cooldown.
`watch --state FILE` persists the engine between one-shot runs;
`serve` keeps a 200-event ring in memory. Event document:
`{ts, time, ip, model, source, type, severity, detail, data}`.
Vietnamese labels from the web dashboard (`TYPE_LABEL`,
`SEV_LABEL`) — neither original filters the list by type, so
the port doesn't either.

Port: `scan` bridge mode gains `--events-state FILE` (mirrors
`watch --state`, reuses `_load_state`/`_save_state`): after the
records are built, present = the non-error records, the engine
diffs, state is saved back, and the bridge payload gains
`"events": [...]` — ONLY when the flag is passed, so every
existing bridge consumer/test is byte-unaffected. The app
passes one state file PER TARGET STRING (ad-hoc target or the
group's targets — one engine per watched target, exactly like
separate `watch` invocations; switching targets must not fire
false OFFLINE storms), accumulates the returned events into
its own `beesky-events.json` log (newest first, cap 500), and
the view lists them: severity chip, type label, `ip · model`,
detail, time. First pass against a fresh state only seeds
baselines — no events — exactly like the original.

### 5. Cài đặt — only settings that persist and take effect

| Setting | Persists to | Takes effect |
|---------|-------------|--------------|
| Mục tiêu quét mặc định | `beesky-settings.json` (app store) | Prefills the scan target at launch INSTEAD of sysinfo's auto-detected subnet when set (sysinfo prefill keeps its untouched-field guard); clearing restores auto behaviour. |
| Giá điện (VNĐ/kWh) | same file | The Điện năng view's cost math; default 2000 (the cloud default). |
| Tài khoản máy đào | — (entry point) | Opens the EXISTING v0.23 creds dialog; shows the saved-set count. |
| Nhóm mạng | — (entry point) | Switches to the groups view. |
| Thư mục phiếu sửa | — (read-only info) | Shows the exact dir Lịch sử sửa reads, so the owner can find the .txt files in Explorer. |
| Giới thiệu | — | App version (build const) + core version from sysinfo when connected, or the missing-engine state. |

No decorative toggles: autoscan lives on groups, grid options
live on the miners view — they are NOT duplicated here.

## Packaging — self-contained portable zips (coordinator addendum)

Route chosen after inspecting both workflows: build-windows.yml
and build-flutter.yml are INDEPENDENT workflow runs on the same
tag (no shared artifacts; the flutter file's header states the
independence is deliberate). Cross-run artifact download would
couple them and race (the windows job is far slower). So each
flutter job now builds the PyInstaller spec itself (checkout +
Python are already available; ~2–3 min extra) and stages the
core exe(s) into the runner folder before zipping:

- BeeSkyFlutter zip: + `beesky.exe` beside `beesky_app.exe`
  (≈ +13.8 MB → ~26 MB total).
- BeeSkyAgentFlutter zip: + `beesky-agent.exe` AND
  `beesky-agentw.exe` beside `beesky_agent_app.exe`
  (≈ +27.8 MB → ~39 MB total). Symmetric bundling is trivial on
  this route, and agentw is REQUIRED for a standalone agent zip
  to be honest: the agent app's "install background task" verb
  registers the windowless twin as the scheduled-task target —
  without it that button would point at a missing file.

Each job then VERIFIES its zip (lists entries, fails unless the
app exe, the sidecar exe(s), `flutter_windows.dll` and `data/`
are present) — the check is CI-visible in the job log.

Named divergence: the zip-bundled exes are built from the same
tagged source but are NOT eSigner-signed inside build-flutter
(signing lives in build-windows; its signed beesky.exe remains
the standalone release asset and the installer's embedded copy).
The update manifest is unchanged (the zips were never part of
the self-update channel).

## UNKNOWN / not observed

- The cloud dashboard's repairs view shows status chips whose
  local analogue does not exist (see view 3) — not ported.
- Whether the owner ever used `watch`/`serve` event flows is
  unobserved; the port wires events to the scans he already runs.
