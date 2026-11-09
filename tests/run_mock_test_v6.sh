#!/usr/bin/env bash
# v0.6 full mock suite: everything from v0.5 (v0.1 + v0.2 scans, v0.3
# watch, v0.4 web dashboard, v0.5 cloud), then the remote-actions test.
#   run_mock_test_v5.sh   regenerates tests/RESULTS.md (v0.1..v0.5 sections)
#   mock_actions_test.py  viewer -> cloud -> agent -> miner command
#                         path for all three sources: cgminer restart
#                         RPC (incl. the read-only "Access denied"
#                         refusal), dashd /system/reboot +
#                         /mining/switch-pool + /settings pool rewrite,
#                         stock reboot.cgi; plus agent-key 401s,
#                         viewer-login gating and cross-agent ownership
#                         (403 + no cross-claim).
# The v0.6 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v5.sh

ACTIONS_OUTPUT="$(python3 tests/mock_actions_test.py)"
echo "$ACTIONS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.6 mock test — remote actions via cloud (command queue)"
  echo
  echo "\`tests/mock_actions_test.py\` builds the full command path on"
  echo "127.0.0.1: one \`beesky cloud\` (:18791, password set) with"
  echo "three minted agents — site \"Xưởng 1\" runs the control-file"
  echo "cgminer miner (:14032), site \"Xưởng 2\" the api-doc dashd mock"
  echo "(:18082, x-api-key auth), site \"Xưởng 3\" the digest-auth stock"
  echo "mock (:18083). Assertions: agent poll no/wrong key -> 401;"
  echo "viewer POST /api/commands without login -> 401; agent A can"
  echo "neither claim nor finish agent B's command (403, stays"
  echo "pending); cgminer reboot finishes done with the restart RPC"
  echo "recorded by the mock, and fails honestly with the miner's own"
  echo "\"Access denied\" when its API is read-only; switch_pool to a"
  echo "cgminer miner fails \"not supported\"; dashd reboot lands on"
  echo "POST /system/reboot, switch_pool {pool_id} activates slot 1,"
  echo "switch_pool {url,user} rewrites slot 0 via GET/POST /settings"
  echo "and activates it; stock reboot hits /cgi-bin/reboot.cgi; the"
  echo "dashboard carries the action UI; /api/commands shows history."
  echo
  echo "## Assertions + captured commands"
  echo
  echo '```'
  echo "$ACTIONS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.6 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
