#!/usr/bin/env bash
# v0.11 full mock suite: everything from v0.10 (v0.1..v0.10), then the
# firmware test.
#   run_mock_test_v10.sh   regenerates tests/RESULTS.md (v0.1..v0.10)
#   mock_firmware_test.py  hermetic firmware suite on loopback:
#                          mock_stock_fw.py (digest-auth stock miner;
#                          upgrade.cgi records uploads; update_first.bmu
#                          blocks until the race marker exists;
#                          patch_success.cgi flips only after both .bmu
#                          uploads + marker), mock_dashd.py with the
#                          documented POST /api/v1/firmware/update, and
#                          a fake ssh shim sharing one ordered event log.
#                          Assertions: identify verdicts (stock+SSH,
#                          no-ssh-binary, VNish); stock + dashd installs
#                          upload the exact bytes (sha256); unlock
#                          refuses with ZERO mock requests when any hard
#                          gate is missing (flag / env / typed IP /
#                          payload files); the fully-gated unlock runs
#                          identify -> first.bmu -> kill -> second.bmu
#                          -> patch marker in order.
# The v0.11 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v10.sh

FW_OUTPUT="$(python3 tests/mock_firmware_test.py)"
echo "$FW_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.11 mock test — firmware identify / install / gated unlock"
  echo
  echo "\`tests/mock_firmware_test.py\` is fully hermetic: a digest-auth"
  echo "stock miner mock on 127.0.0.5 (upgrade.cgi records every upload's"
  echo "sha256; its update_first.bmu handler blocks until the race-kill"
  echo "marker file exists, mimicking the signature-verification window;"
  echo "patch_success.cgi answers 200 only after both .bmu uploads AND"
  echo "the marker), the dashd mock on 127.0.0.6 implementing the"
  echo "api-doc's \`POST /api/v1/firmware/update\`, and a fake \`ssh\`"
  echo "shim on PATH that logs into the same ordered event log, answers"
  echo "compile_time and creates the marker on the kill command."
  echo "Assertions: identify verdicts for stock+SSH (\"stock cũ / đã mở"
  echo "SSH\"), stock without an ssh binary (\"không rõ\"), and VNish;"
  echo "stock and dashd installs deliver the exact file bytes; unlock"
  echo "refuses with ZERO requests reaching the mock when the"
  echo "--experimental-unlock flag, the BEESKY_ALLOW_UNLOCK=1 env, the"
  echo "typed-IP confirmation, or the payload files are missing; with"
  echo "all gates open the sequence lands in order — miner_type.cgi"
  echo "identify, update_first.bmu upload, the SSH kill of the openssl"
  echo "verify process (inside the first upload's window),"
  echo "update_second.bmu upload, patch_success marker."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$FW_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.11 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
