# BeeSky Agent App (Flutter)

The Flutter face of the standalone farm-agent config app — stage 2
of the Flutter programme (v0.31.0). It is a 1:1 port of the Tk
config window (`beesky/agent_gui.py`), which remains shipped as
the fallback; the dissection + behaviour mapping (incl. every
divergence) lives in `docs/agent-app-mapping.md`.

## Architecture: shell + the core's own verbs

The Python core is the **only engine** and is untouched. Unlike the
main app (which drives `beesky.exe`'s JSON bridge), this app is a
config editor + status viewer around files and verbs that already
exist:

| Need | Channel |
| --- | --- |
| Load / save config | The `agent-config.json` file itself, in the core's exact format (`lib/agent_config.dart` mirrors `beesky/agent_config.py`) |
| Background status | Reads `agent-status.json` next to the config file |
| Chạy thử | `beesky-agent test --config <path>` + the core's overlay flags |
| Bật/Tắt tự khởi động | `beesky-agent install-task --config <path>` / `beesky-agent remove-task` |
| Task state | `schtasks /Query /TN "BeeSky Agent"` (the core's own probe) |
| First-run target pre-fill | `beesky sysinfo --json` when a `beesky.exe` is resolvable (absent on agent-only installs — the field then starts blank) |

Exe resolution (`lib/agent_bridge.dart`): constructor override →
`BEESKY_AGENT_EXE` / `BEESKY_EXE` env → `--dart-define` → the exe
next to this app → the exe in the **parent** folder (the unified
installer's `{app}\agent\` layout) → bare name on PATH.

One honest limitation, named in the mapping (D2): the core's
Windows save DPAPI-protects the agent key; Dart cannot. A stored
DPAPI key therefore shows as an empty field with a keep-or-replace
hint — saving untouched keeps the blob verbatim, and a newly typed
key is written in the core's legacy plain-text form (which the
core migrates to DPAPI on its next save).

## Layout of the shipped bundle

CI produces `BeeSkyAgentFlutter-<tag>-win64.zip` (the runner
folder: `beesky_agent_app.exe` + `flutter_windows.dll` + `data/`).
The installers embed the same folder: the unified `BeeSkySetup`
puts it in `{app}\agent\` next to `beesky-agent.exe`; the
standalone `BeeSkyAgentSetup` puts it in `{app}` next to the agent
exes. Either way the bridge finds its engine beside (or one level
above) the app.

## Dev modes

- Mock fixtures (no sidecar needed): run with `BEESKY_MOCK=1` in
  the environment or `--dart-define=BEESKY_MOCK=1` — a demo farm
  config + an OK status cycle, canned verb outcomes.
- Tests: `flutter test` (config model, argv contracts, the full
  window against the mock runtime).
