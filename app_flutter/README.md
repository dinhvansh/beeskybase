# BeeSky App (Flutter)

The Flutter rewrite of the BeeSky desktop app, stage 1 of the programme
the owner approved on 2026-11-11 ("cú lớn"); the layout was redesigned
in v0.22 (see "Layout" below). The Tk app (`beesky/gui.py`) remains
shipped and supported as the fallback; nothing about it changed.

## Architecture: shell + sidecar

The Python core is the **only engine** — scanner, agent and cloud are
untouched. This app is a shell that drives the BeeSky CLI executable as a
sidecar through the JSON bridge added in v0.21.0:

| Need | Sidecar call |
| --- | --- |
| Version + pre-fill scan target | `beesky sysinfo --json` |
| Scan | `beesky scan <target> --json [--user ..] [--password ..]` |
| Repair tickets | `beesky scan <target> --tickets <dir>` (post-step flag) |
| Local web dashboard | `beesky serve <target> --port 8787` (detached) + OS browser |

Bridge mode contract: in `--json` mode stdout carries exactly one JSON
document — `{"records": [...], "scanned": N, "found": M, "elapsed_s": X}`
where each record is the same dict the agent/cloud path serialises
(native `rate_value`/`rate_unit` since v0.20). Human notes go to stderr.

Sidecar resolution order (`lib/sidecar.dart`): constructor override →
`BEESKY_EXE` env → `--dart-define=BEESKY_EXE=` → `beesky.exe` next to
this app's exe (the shipped layout) → `beesky` on PATH.

## Layout of the shipped bundle

The CI zip (`BeeSkyFlutter-<tag>-win64.zip`) contains the Flutter runner
folder. **Drop `beesky.exe` (from the main BeeSky release) beside
`beesky_app.exe`** — that is the layout the sidecar expects. No installer
in stage 1; the Tk installers keep shipping unchanged.

## Dev modes

- Mock fleet (no sidecar needed): run with `BEESKY_MOCK=1` in the
  environment or `--dart-define=BEESKY_MOCK=1`. The mock data includes
  an L9 at `14.54 MH/s` and a Z15 at `1101.00 ksol/s` (the v0.20 unit
  cases), one sick S19 and one unreachable unit.
- Tests: `flutter test` — model tests cover bridge parsing + grouped
  rate totals; the widget test drives splash → empty state → mock scan →
  auto-selected detail panel.

## Layout (v0.22 — table-first)

The v0.21 layout (header + scan card + 4 big stat tiles + table) was
rejected by the owner after one run: the tiles ate the screen —
"người ta muốn thấy máy đào" (people want to SEE THE MINERS). The
structure now mirrors the HashCore Toolkit, keeping BeeSky's palette:
a 228px left sidebar (logo, "BeeSky", "Quản lý máy đào", nav, version
+ sidecar status dot at the foot), a slim 52px header with the view
title and the fleet stats as compact chips in ONE row (total / OK /
check / error / grouped hashrate / max temp), one slim scan bar
(target pre-filled from sysinfo, Quét ngay, a "Tài khoản: N bộ"
button opening the credential-sets editor, Xuất phiếu sửa), and the
miners table filling all remaining space (~34px rows). Row detail is
a 300px right panel that only takes width while a row is selected
(close button returns the width to the table); the first row still
auto-selects after a scan. Sidebar entries for Bản đồ nhiệt / Điện
năng / Lịch sử sửa / Sự kiện are greyed with a "sau" tag — visible
roadmap, no fake functionality.

v0.23 changes: the scan bar's old single user/password fields and
the "Mở web local" button are gone (the CLI `serve` command itself
stays). Double-clicking a miner row opens that miner's own web
admin (`http://<ip>`) in the OS default browser, BTC Tools-style;
a single click still just selects the row. When a scan record was
authenticated by a saved credential set, the detail panel names it
("Đăng nhập: <label>").

## Credential sets (v0.23)

A farm runs several machine lines with different web logins, so the
app keeps MANY saved sets (the model follows the HashCore Toolkit:
unlock methods keyed by firmware vendor). The "Tài khoản: N bộ"
button opens the editor: one row per set — label, user, password
(obscured), a machine-type dropdown (Mọi loại máy / Antminer gốc /
VNish), delete; "Thêm bộ" adds a row; blank rows are dropped on
save. VNish rows additionally show an optional "API key (không bắt
buộc)" field: when filled, that set authenticates to VNish's dashd
with the `x-api-key` header INSTEAD of a user/password login.

Persistence: the sets live in `beesky-creds.json` NEXT TO the app
executable (the bundle folder, beside beesky.exe). When that folder
is not writable, saving falls back to
`%APPDATA%\BeeSky\beesky-creds.json`. Loading reads the primary file
when it exists, else the fallback, else starts empty. The file uses
EXACTLY the CLI's `--creds-file` schema — a bare JSON list:

```json
[{"label": "VNish trại A", "user": "root", "password": "...",
  "type": "vnish", "api_key": "..."},
 {"label": "Kho S19 gốc", "user": "root", "password": "...",
  "type": "stock"},
 {"label": "Dự phòng chung", "user": "root", "password": "...",
  "type": "any"}]
```

(`api_key` is optional and omitted when empty; a missing/unknown
`type` reads as `any`.) The app passes only the file's PATH to the
sidecar (`scan --creds-file <path>`) — passwords never appear on a
command line. With no sets saved, scans run without the flag and
the core's built-in defaults apply.

Try order per miner (the probe detects the family first): sets
tagged for that family, in saved order → `any` sets → all remaining
sets, so a wrong tag costs time but never locks a machine out. The
winning set's label lands on the record as `cred_label`.

## Stage-1 scope vs TODO

Covered: splash, sidebar + header chips, scan bar, miners table with
status chips, detail panel (issues + boards + winning cred label),
empty state, auto-select first row, export tickets, saved
credential sets (editor dialog + file persistence + `--creds-file`
hand-off), double-click a row to open that miner's web admin.

TODO (marked in code): a dedicated tickets verb so export doesn't need
a second scan pass; `url_launcher` instead of the OS-shell browser open;
heat map + cloud views (stage 2+); an installer bundling the sidecar
(stage 2); the Agent app rewrite (later stage).

## Scaffold note

This project's `windows/` scaffold was rendered from the Flutter
3.47.9 SDK's own `flutter create` templates (the sandbox used for
stage 1 cannot complete the tool's internal pub update through its
egress proxy, so `flutter create` itself could not run there). All
Dart sources pass the SDK parser/formatter; `flutter pub get` /
`flutter test` / `flutter build windows` are exercised by CI
(`.github/workflows/build-flutter.yml`) and on dev machines.
