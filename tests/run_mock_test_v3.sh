#!/usr/bin/env bash
# v0.3 full mock suite: v0.1 + v0.2 scans, then the watch-mode story.
#   run_mock_test.sh     regenerates tests/RESULTS.md (v0.1 section)
#   run_mock_test_v2.sh  appends the three-adapter section
#   mock_watch_test.py   scripted miner: healthy -> hashrate -40% ->
#                        killed (OFFLINE) -> back (BACK_ONLINE); a local
#                        receiver captures webhook + Telegram calls.
# The v0.3 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test.sh
bash tests/run_mock_test_v2.sh

WATCH_OUTPUT="$(python3 tests/mock_watch_test.py)"
echo "$WATCH_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.3 mock test — watch mode, event engine, notifications"
  echo
  echo "\`tests/mock_watch_test.py\` drives the real CLI (\`beesky watch"
  echo "--once --state … --notify …\`) against \`tests/mock_watch_miner.py\`,"
  echo "a control-file-driven fake cgminer S19 Pro on 127.0.0.1:14028."
  echo "Healthy passes build the rolling baseline; a drop to 66 TH/s is a"
  echo "40% HASHRATE_DROP (severity major on the 15/30/50 scale); killing"
  echo "the miner fires OFFLINE (critical); restarting it fires"
  echo "BACK_ONLINE. A local receiver on 127.0.0.1:18777 captures the"
  echo "webhook POSTs (/hook) and the Telegram Bot API calls (api_base"
  echo "overridden to the same receiver); the logfile channel is checked"
  echo "on disk. Anti-flap passes assert no duplicate events."
  echo
  echo "## Assertions + captured webhook payloads"
  echo
  echo '```'
  echo "$WATCH_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.3 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
