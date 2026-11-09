#!/usr/bin/env bash
# v0.5 full mock suite: everything from v0.4 (v0.1 + v0.2 scans, v0.3
# watch, v0.4 web dashboard), then the cloud test.
#   run_mock_test_v4.sh  regenerates tests/RESULTS.md (v0.1..v0.4 sections)
#   mock_cloud_test.py   cloud-add-agent -> cloud (password set) + farm
#                        agent + mock miner: ingest key auth (401s),
#                        viewer login flow, /api/sites totals, and a
#                        HASHRATE_DROP travelling agent -> cloud.
# The v0.5 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v4.sh

CLOUD_OUTPUT="$(python3 tests/mock_cloud_test.py)"
echo "$CLOUD_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.5 mock test — farm agent + cloud backend + multi-site web"
  echo
  echo "\`tests/mock_cloud_test.py\` builds the full cloud shape on"
  echo "127.0.0.1: \`beesky cloud-add-agent\` mints a key for site"
  echo "\"Xưởng 1\", \`beesky cloud\` runs on :18790 with"
  echo "BEESKY_CLOUD_PASSWORD set, the control-file fake S19 Pro sits"
  echo "on :14031, and \`beesky agent --interval 1\` pushes to the"
  echo "cloud. Assertions: wrong/no agent key -> 401 on ingest;"
  echo "viewer /api/sites locked (401) until POST /login with the"
  echo "right password sets a session cookie (wrong password -> 401);"
  echo "GET / serves the branded cloud dashboard; /api/sites shows"
  echo "the site at ~110 TH/s; flipping the miner to 66 TH/s makes a"
  echo "HASHRATE_DROP (major, ~40%) arrive at the cloud /api/events"
  echo "tagged with the site; /api/miners?site= shows ~66 TH/s."
  echo
  echo "## Assertions + captured cloud event"
  echo
  echo '```'
  echo "$CLOUD_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.5 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
