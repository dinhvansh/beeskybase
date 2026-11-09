#!/usr/bin/env bash
# v0.4 full mock suite: the whole v0.3 suite (v0.1 + v0.2 scans + watch),
# then the web dashboard test.
#   run_mock_test_v3.sh  regenerates tests/RESULTS.md (v0.1..v0.3 sections)
#   mock_web_test.py     beesky serve vs mock_watch_miner.py: dashboard
#                        HTML, /api/miners, /api/status, POST /api/scan,
#                        and a HASHRATE_DROP appearing in /api/events.
# The v0.4 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v3.sh

WEB_OUTPUT="$(python3 tests/mock_web_test.py)"
echo "$WEB_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.4 mock test — web dashboard (serve + JSON API)"
  echo
  echo "\`tests/mock_web_test.py\` runs the real server (\`beesky serve"
  echo "127.0.0.1 --port 18788 --interval 1\`) against the control-file"
  echo "fake S19 Pro on 127.0.0.1:14029 and asserts over plain HTTP:"
  echo "the dashboard page carries the BeeSky brand, /api/miners shows"
  echo "the miner at 110 TH/s, /api/status counts are sane, POST"
  echo "/api/scan answers 202, and flipping the miner to 66 TH/s makes"
  echo "a HASHRATE_DROP (major, ~40%) appear in /api/events."
  echo
  echo "## Assertions + captured event"
  echo
  echo '```'
  echo "$WEB_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.4 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
