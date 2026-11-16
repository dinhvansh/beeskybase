# Agent 0.44.0 — whole-app updates and runtime fixes

Agent checks for a signed release one second after opening, every six hours
while open, and retries a failed check after fifteen minutes. A newer release
appears above the form and in **Phiên bản & cập nhật**. The user confirms one
update; the app downloads it with progress and verifies the signed manifest,
exact file size and SHA-256 before changing the running application.

A copied helper outside the installation acknowledges startup before the UI
exits. It waits for that UI process, verifies the staged installer again, stops
the authenticated worker, and runs the installer with progress. The installer
updates Flutter, assets and both engines together. The helper verifies the
installed engine version, reopens the UI, and resumes monitoring only when it
was running before the update. Saved configuration bytes and startup settings
are retained. Download failures never stop the worker; installation failures
are recorded and the original running state is restored where possible.

The first move from 0.43.0 requires installing 0.44.0 once. Later releases can
be downloaded and applied from the application. Background native agents still
announce signed releases in the Cloud event feed; they do not silently replace
just one engine and leave an old native UI behind. CLI-only opt-in self-updates
retain their existing behaviour.

Runtime fixes: uncertain/unresponsive local control no longer permits edits
or starting another worker; the UI offers refresh. Missing/refused control can
be distinguished from uncertainty. Runtime lookup supports config names without
an extension. Connection/test/control subprocesses are drained and reaped on
timeout. Opening Agent again focuses the existing window. Manual installers
also stop the worker before replacing its files.

The release verification key is public source. Its signing counterpart is in
the repository's Actions secret, with an owner-only DPAPI-encrypted local
backup; no private key is committed. CI checks the signed manifest against the
actual compiled public key before publishing it.

Tests cover malformed/tampered signed data, wrong downloaded hashes, worker
preservation, successful/failed installer handoff, resume policy, confirmation,
progress, cancellation before downloading, retries, and uncertain runtime.
`tools/verify_agent_update.py` is restricted to Windows Actions. It uses an
isolated install directory, a loopback signed release, the real frozen helper
and installer, an older-version comparison seam, preserved configuration and
real worker snapshots before/after the update. It verifies the full Flutter
bundle and Vietnamese fonts, then closes only its own UI and uninstalls.
It never installs on the user's desktop. The loopback fixture uses the current
installer; publication of a later public version is not required for this test.
