# Scanner / Agent 0.42.0

Scanner and Agent are separate applications. Scanner no longer imports, displays
or installs Agent. Both apps bundle licensed Noto Sans faces at 400/500/600/700,
including Vietnamese glyphs; labels and buttons use the same explicit family.

Agent now exposes `start`, `status`, and `stop` around the existing scan engine.
`start` verifies the server-owned token destination, saves configuration, launches
an independent worker with detached stdio, and waits for that worker's control
server. Closing/reopening the UI does not own or lose the worker. Its loopback
control uses a per-instance credential in the config's owner-scoped runtime file;
a stale PID is never sufficient to terminate a process. Stop wakes the loop and
only terminates a still-authenticated matching worker if a scan cannot finish.

The UI shows connection progress and the result beside the token, has a 25-second
timeout, and keeps action feedback visible above the bottom actions. Runtime
state is observed after opening the UI and every two seconds. A saved successful
scan alone no longer makes a stopped worker look active. Default Windows startup
is a current-user logon task; the legacy pre-logon SYSTEM task is explicitly
opted into with `--system`.

A real public-Mine probe found the desktop clock ahead of the VPS by more than
the accepted 60-second future limit. Connection responses now carry `serverTime`.
Agent estimates its offset and timestamps deliveries using server time, retaining
the backend's existing freshness validation. JSON delivery errors are surfaced
with the token redacted.

Native UI mutexes let installers detect open UIs before replacing Flutter DLLs.
Agent uninstall stops its runtime and removes startup only when the task's
executable belongs to that installation. Scanner stores new data in user AppData;
legacy generated files/tickets are preserved outside the installation folder on
uninstall. Token pairing is handled in the Agent UI, not an installer name field.

Cloud's Agent dialogs use a numbered flow inside the shared modal: installer,
readonly token with inline copy feedback, then verification/start instructions.
The bound workshop remains visible. The token-completion action is **Xong**.
Setup text consistently points at the separate Agent.

Verification includes the Scanner/Agent widget suites, visible failure/timeout
and reopening tests, real detached subprocess scanning and POSTing to an isolated
local server, stale-PID protection, clock-offset and redaction regressions, and
headless image checks of Vietnamese text at desktop/laptop sizes. An isolated
production token resolved and delivered one synthetic miner/two snapshots to
public Mine; the temporary account, workshop, Agent, telemetry and audit records
were removed afterward. The release CI additionally tests the frozen engine and
silent install/uninstall in isolated build folders. No real miner commands or
user configuration are used by those tests.
