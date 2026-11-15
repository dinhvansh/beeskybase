# v0.34.0 mapping — Settings completion + UI smalls

HashCore surface dissected from `research/hashcore/UI-ANALYSIS.md`
§2 + `assets/translations/en.json` (`settings_dialog.*`,
`network_groups.commands`, hot-key layer). Only settings BeeSky
actually has are ported; everything else is named as not-ported.

## 1. HashCore's Settings dialog (VERIFIED keys)

Tabs: **General/Appearance, Unlock, Timeouts, Logs, Advanced**.

- **General** (`appearance`): theme, language, **scale** ("Interface
  scale" — "Resize all interface elements"), exit confirmation,
  display status time, automatic operations (auto-open first group,
  autoscan), squash (combine consecutive addresses on import),
  **IP Report listening** ("Enables IP-Reports listening in the
  network"), hashrate in presets, reset.
- **Unlock** (`unlock`): per-vendor method list — already ported
  faithfully in BeeSky v0.23 (vendor-keyed sets, layered
  global → group → task).
- **Timeouts** (`timeouts`): custom network timeout, miner
  detection, connection, send data, receive response, send file,
  rescan count, stats update; batch operations ("Adds a pause to
  batch operations to prevent devices from executing a task
  simultaneously" — devices per batch + pause duration).
- **Logs** (`logs`): log directory, file/memory logging level,
  memory buffer limit, diagnostic report (current/previous
  session), export/import app data.
- **Advanced** (`advanced`): thread count, parallel task
  iterations, task timeout.

Groups-screen commands (VERIFIED, `network_groups.commands`):
Autoscan groups · Import range groups · Export selected (JSON) ·
**View groups in combined mode** · Merge network groups ·
**Reset statistics** · Remove selected; global "Rescan all groups",
"Reset statistics", "Remove all groups"; search "by IP, name or
description".

Hot keys (VERIFIED, `package:toolkit/hot_keys/`): select_all,
invert_selection, isolate, unlock, rescan, search, clear_filter,
set_view_mode/type, **command_palette** ("Type a command...",
`miners_list.dialogs.commands_dialog`), **zoom in/out/reset**
(`settings scale`).

## 2. BeeSky's 5 tabs (only real settings)

`AppSettings` in `beesky-settings.json` gains the fields below.
Every field takes effect somewhere real; nothing decorative.

| Tab | Setting | Default | Takes effect |
|---|---|---|---|
| Chung | Mục tiêu quét mặc định (`default_target`) | '' (= sysinfo auto-subnet) | scan-field prefill (v0.32) |
| Chung | Giá điện (`price_vnd_kwh`) | 2000 | Điện năng view (v0.32) |
| Chung | Tỉ lệ giao diện (`scale`) | 1.0 (90–130%, step 5%) | `MediaQuery.textScaler` app-wide + Ctrl+= / Ctrl+- / Ctrl+0 |
| Chung | Nghe IP Report (`ip_report_enabled`) | false | starts/stops the IP-Report listener (docs/ipreport-mapping.md) |
| Tài khoản | (link to creds editor) | — | opens the v0.23 creds dialog; shows saved-set count |
| Thời gian chờ | Probe timeout (`probe_timeout_s`) | 1.5 | `scan --timeout` via sidecar (core `discover()`/`probe_host()`) |
| Thời gian chờ | Request timeout (`request_timeout_s`) | 3.0 | `inspect --timeout` + ops job `timeout` (core `ops.validate_job`) |
| Thời gian chờ | Dừng giữa các máy (`ops_stagger_s`) | 0.0 | ops job `stagger_s` (core `ops.run_job` onset gate, v0.26) |
| Nhật ký | Thư mục dữ liệu (readout) | — | shows the primary data dir + store files with sizes |
| Nhật ký | Xóa lịch sử thao tác | — | deletes `beesky-ops-history.json` (real file) |
| Nhật ký | Xóa nhật ký sự kiện | — | deletes `beesky-events.json` (real file) |
| Nâng cao | Số luồng quét (`scan_workers`) | 64 | `scan --workers` via sidecar |
| Nâng cao | Song song thao tác (`ops_workers`) | 4 | ops job `workers` (core `ops.validate_job`) |

Not ported (named): theme / language (BeeSky is one theme, one
language — Vietnamese); exit confirmation (no such flow exists);
auto-open (BeeSky already opens on groups); squash (no import
flow in BeeSky); hashrate-in-presets (BeeSky presets show power
only — no such toggle exists); log levels / memory limit (BeeSky
writes no log files — the Logs tab shows the real store files
instead); export/import app data (no such flow; groups export
exists separately); per-device "devices per batch" bucketing
(BeeSky's `stagger_s` is the onset-spacing equivalent, v0.26
mapping §4.5).

## 3. UI smalls

| HashCore | BeeSky | Notes |
|---|---|---|
| Command palette ("Type a command...") | **Ctrl+K** dialog: filter-as-you-type list of real commands (Quét, Quét nhóm…, Quét tất cả nhóm, Mở các view, Cài đặt, Tài khoản, Xuất phiếu, Quét lại) | Top-level shortcut so it works from every view (v0.25 hotkeys only lived in the miners column) |
| Zoom in/out/reset (`settings scale`) | Ctrl+= / Ctrl+- / Ctrl+0 + scale stepper in Cài đặt (Chung) | Text-scale divergence D-S1 |
| View groups in combined mode | "Xem gộp" toggle on the groups screen: one combined card (union of all groups' targets, merged last-scan stats); Quét on it runs ONE scan over the union spec and shows the merged fleet | BeeSky's combined mode is a virtual group, not a separate table |
| Rescan all groups | "Quét tất cả nhóm" — runs each group's scan in turn, merges records into the miners view (each record decorated with its group name, like the v0.28 note decoration) | — |
| Reset statistics (per group + global) | Per-group "Đặt lại thống kê" (card action) + header "Đặt lại tất cả"; core `groups reset-stats <name>` / `groups reset-stats --all` clears `last_scan` | Core verb added so the CLI and app share the operation |
| Group search | Search box on the groups screen filtering by name + targets (HashCore also searches description; BeeSky groups have no description) | — |

## 4. Divergences register

| # | Item | Status |
|---|---|---|
| D-S1 | Scale is text scaling (`MediaQuery.textScaler`, 90–130%): table fonts and labels grow; fixed-pixel chrome (sidebar width, row heights) does not. HashCore scales all interface elements. | divergence (Flutter textScaler is the honest one-place mechanism; full layout scaling would reflow the dense table) |
| D-S2 | Unlock tab is a link to the existing creds dialog, not an inline per-vendor editor (HashCore's tab IS the editor). | divergence (BeeSky's editor already exists as a dialog; duplicating it inline adds a second source of truth) |
| D-S3 | Combined mode = one virtual group over the union target spec (one scan pass); HashCore's combined rendering internals are UNKNOWN. | named choice |
| D-S4 | Logs tab shows store files + clear actions instead of log levels (BeeSky writes no log files). | divergence (scope: only real files) |
