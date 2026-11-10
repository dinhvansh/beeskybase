# BeeSky App (Flutter) — stage 1

The Flutter rewrite of the BeeSky desktop app, stage 1 of the programme
the owner approved on 2026-11-11 ("cú lớn"). The Tk app
(`beesky/gui.py`) remains shipped and supported as the fallback; nothing
about it changed.

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

## Stage-1 scope vs TODO

Covered: splash, header/version, scan card (target pre-filled from
sysinfo, user/password), 4 stat tiles (totals grouped by native unit),
miners table with status chips, detail panel (issues + boards), empty
state, auto-select first row, export tickets, open local web.

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
