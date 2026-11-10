
## v0.15.1 — main-window layout fix (post-screenshot review)
The v0.15 live screenshot showed the results Treeview (default 10 rows) consuming the whole
1080x680 window and squeezing the "Chi tiết máy đã chọn" detail card out of view. Fix: Treeview
height=7 visible rows, window 1120x730 (minsize 940x620). Verified by re-running the GUI smoke +
theme suite (green) and a fresh live screenshot with a scanned miner selected — detail card
(dead-chip positions, fan speeds) now visible under the table.

## v0.15.2 — main-window balance fix (supersedes v0.15.1)
v0.15.1's screenshot still showed the detail card crushed (root request 943px vs 730px window;
pack starves the last widgets). v0.15.2 converts the main window's section layout from pack to
grid with the table row weighted (minsize 150): the table now absorbs any shortfall and the
detail pane always keeps full height. Card padding trimmed (16->12), detail text 5 lines,
default window 1120x880. Measured on the live window: header 67 / toolbar 153 / stats 110 /
table 253 (of 270) / detail 191 full / footer 24 — everything visible, GUI + theme suites green.

## v0.16.0 — agent background service + install security
The agent now runs truly in the background and the install is hardened:
- NEW windowless twin `beesky-agentw.exe` (same PyInstaller Analysis as beesky-agent.exe,
  console=False), shipped by BeeSkyAgentSetup and listed in the signed update manifest.
  A frozen agentw — or `run --background` — never opens the config GUI (a bare agentw
  launch IS a background run), sends all output to `agent.log` next to the config
  (~1 MB rotation, one .old), and rewrites `agent-status.json` after EVERY cycle via a
  new AgentService status hook (atomic temp+replace: ts/ok/miners/error/cloud_url/site).
  Console runs mirror the same output to console + log.
- install-task v2 registers via generated Task Scheduler XML (schtasks /Create /XML):
  SYSTEM (S-1-5-18) + HighestAvailable, BootTrigger (PT30S) + LogonTrigger, Hidden,
  ExecutionTimeLimit PT0S, RestartOnFailure PT1M x5, no battery stops, action =
  beesky-agentw with the config path baked in. `install-task --console` is the
  farm-debugging escape hatch.
- Key protection: on Windows the agent key is stored DPAPI-protected
  (CRYPTPROTECT_LOCAL_MACHINE so the SYSTEM task can decrypt; `key` written empty,
  `key_protected` base64) — protects against the file being copied off the machine,
  not against local admins. Elsewhere the config is chmod 0600 after every save
  (Windows also gets a best-effort owner+SYSTEM icacls). A protect failure degrades
  to plain text rather than losing the config; legacy plain-text configs migrate on
  next save; an undecryptable foreign blob loads as an empty key.
- Log hygiene: the agent key is scrubbed at every failure print (beesky.agent.redact)
  and across the whole run stream (key + Bearer value). A non-local http:// cloud URL
  logs a one-time-per-run warning and shows the same hint under the config window's
  Cloud URL field — advisory only, never a hard block.
- Config window gains a "Trạng thái chạy ngầm" card (status pill + last-cycle detail +
  Xem log button) fed by agent-status.json.
- Tests: new tests/mock_agent_bg_test.py — 52/52 PASS standalone (DPAPI branch forced
  via the _dpapi_available probe with a reversible fake for the OS crypto; task XML
  assertions; run --once/--background e2e vs real cloud + mock dashd incl. status/log
  contents and key-free logs on success AND wrong-key cycles; GUI status card + http
  hint under xvfb). Full chain: v0.1–v0.10 regenerated green in-chain (156 PASS), then
  stopped at the KNOWN v0.11 firmware race-order assertion (kill idx 3 vs first.bmu
  idx 5) — control-verified PRE-EXISTING: the pristine v0.15.2 tree (dc4b0e3, changes
  stashed) fails it with byte-identical indices, and this release touches no
  firmware-path code. Every later suite was re-verified standalone against the v0.16
  tree (logo, history, agents-ui, agent-app 41, theme 25, GUI, cloud — all green), so
  the ship-time v0.11–v0.15 evidence blocks in tests/RESULTS.md are kept verbatim,
  exactly as v0.12–v0.15 handled the same flake. tests/RESULTS.md: 364 PASS lines.
