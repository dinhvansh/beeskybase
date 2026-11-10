#!/usr/bin/env bash
# v0.8 full mock suite: everything from v0.7 (v0.1..v0.7), then the
# heat-map + repair-history test.
#   run_mock_test_v7.sh   regenerates tests/RESULTS.md (v0.1..v0.7)
#   mock_repairs_test.py  store-level auto-log rule (problem events ->
#                         auto_event rows, 1/hour dedupe) + the full
#                         cloud shape: repairs endpoints 401 logged
#                         out, heat-map section + colour thresholds in
#                         both dashboards, a CHIPS_LOST event landing
#                         in /api/repairs as an auto row, and a manual
#                         technician entry listed with cost + name.
# The v0.8 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v7.sh

REPAIRS_OUTPUT="$(python3 tests/mock_repairs_test.py)"
echo "$REPAIRS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.8 mock test — heat map + repair history"
  echo
  echo "\`tests/mock_repairs_test.py\` checks the repair-history rule"
  echo "in-process against \`CloudStore\` (problem events CHIPS_LOST /"
  echo "CHAIN_DOWN / OVER_TEMP / OFFLINE become \`auto_event\` rows,"
  echo "deduplicated to one identical (site, ip, title) row per hour;"
  echo "HASHRATE_DROP / BACK_ONLINE do not), then builds the v0.5 cloud"
  echo "shape on 127.0.0.1: \`beesky cloud\` (:18792, password set),"
  echo "the control-file fake S19 Pro (:14033) and \`beesky agent"
  echo "--interval 1\`. Assertions: GET/POST /api/repairs -> 401"
  echo "logged out; both dashboards carry the Bản đồ nhiệt section"
  echo "with the heatColor thresholds (<60 green-dark ... >=90 red);"
  echo "flipping the miner to dead chips makes CHIPS_LOST arrive at"
  echo "/api/events AND as an auto row in /api/repairs; a manual"
  echo "POST /api/repairs is listed back with cost_vnd + technician."
  echo
  echo "## Assertions + captured repair rows"
  echo
  echo '```'
  echo "$REPAIRS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.8 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
