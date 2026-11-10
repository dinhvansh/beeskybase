#!/usr/bin/env bash
# v0.10 full mock suite: everything from v0.9 (v0.1..v0.9), then the
# signed self-update test.
#   run_mock_test_v9.sh    regenerates tests/RESULTS.md (v0.1..v0.9)
#   mock_update_test.py    hermetic update channel: throwaway RSA
#                          keypair via the shipped owner tool
#                          (tools/make_update_key.py, outputs in a
#                          temp dir), a local 127.0.0.1 "release
#                          server" serving manifest + signature + a
#                          fake new binary — valid signature verifies
#                          and --check reports the newer version; a
#                          flipped manifest byte is refused; a
#                          correctly signed manifest pinning a wrong
#                          file hash is refused; apply onto a dummy
#                          exe copy (POSIX swap) installs it, keeps
#                          the .old backup and the exec bit; a
#                          same-version manifest is a no-op; no
#                          compiled-in key -> "not configured"; CLI
#                          exit codes wired.
# The v0.10 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v9.sh

UPDATE_OUTPUT="$(python3 tests/mock_update_test.py)"
echo "$UPDATE_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.10 mock test — signed self-update channel"
  echo
  echo "\`tests/mock_update_test.py\` is fully hermetic: openssl"
  echo "makes a throwaway RSA-2048 keypair via the shipped owner"
  echo "tool (outputs redirected to a temp dir — the repo's"
  echo "\`beesky/core/update_key.py\` keeps its shipped N=None),"
  echo "the updater under test is pointed at that public key via"
  echo "its module variables, and a 127.0.0.1 HTTP server plays"
  echo "the GitHub release. Assertions: the pure-Python RSA verify"
  echo "accepts the genuine signature and rejects a one-byte"
  echo "tamper; check() reports the next minor version > the running one;"
  echo "a tampered served manifest is refused whole; a signed"
  echo "manifest pinning a wrong file hash still cannot install"
  echo "(SHA-256 gate); the happy-path apply replaces a dummy"
  echo "exe, keeps \`beesky.old\` and the executable bit; a"
  echo "same-version manifest is a no-op; an unreachable server"
  echo "and the unconfigured (keyless) build both fail cleanly;"
  echo "the CLI reports/refuses with the right exit codes."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$UPDATE_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.10 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
