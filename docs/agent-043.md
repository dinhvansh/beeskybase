# Agent 0.43.0

The standalone Agent now places connection/scan settings beside monitoring and
Windows startup settings. The footer has three actions: start/stop, save, and
one test cycle. Diagnostic paths are disclosed on demand. The official logo,
bundled Vietnamese fonts and Material icons remain local assets. The native
window opens at 1120×760 and the content stacks on narrower windows.

Configuration is readonly while the worker runs; stop remains available without
a Cloud connection. Async actions disable conflicting submissions and restore
controls after failure. Token pairing no longer depends on the scan interval.
Invalid/reversed IPv4 ranges, more than 4096 unique target addresses, and
non-finite/non-positive intervals are rejected before starting. The new read-only
`network` verb suggests the computer's /24 so an Agent-only install can prefill
its target without Scanner. Operators can edit this suggestion for their LAN.

Runtime control returns its start timestamp. The UI distinguishes the first
cycle of the current worker from saved results, warns when cycles stop arriving,
and distinguishes a delivered empty scan from responding miners. Reported miner
counts exclude FETCH_ERROR records. Test cycles also update the status file.
HTTP error responses are closed on failure, and timed-out test/startup subprocesses
are terminated and reaped instead of continuing unseen.

Verification: widget tests cover valid/invalid pairing, start/stop, readonly
running configuration, failed test recovery, duplicate startup submissions and
1366×768, 1024×640, 640×720 at 130% text scaling. Pure tests cover freshness,
restart/empty-scan states and range validation. Real subprocess tests verify
timeout termination and simultaneous UTF-8 output/error draining. The Python
suite runs an isolated fake miner/Cloud, rejects the first upload and verifies
automatic recovery, current-session status, launch/reopen/stop and stale-PID
protection. Tagged Windows CI tests the frozen worker and isolated install/
uninstall, including uninstall while the worker is active.

This release retains startup at the current user's Windows login. It does not
enable an automatic updater or introduce a system service/tray controller.
No real miner command, user configuration, or scheduled task is modified by the
local tests.
