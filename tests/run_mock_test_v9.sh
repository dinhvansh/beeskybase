#!/usr/bin/env bash
# v0.9 full mock suite: everything from v0.8 (v0.1..v0.8), then the
# farm-vs-pool + energy test.
#   run_mock_test_v8.sh      regenerates tests/RESULTS.md (v0.1..v0.8)
#   mock_energy_pool_test.py store level: pool-config secret redaction
#                            (names only, kept on header-less re-POST),
#                            POOL_GAP rule (2 consecutive breaches,
#                            1/hour dedupe), energy integration with
#                            the 3x-interval dt cap; adapter level:
#                            dot-path extraction, GH/s conversion,
#                            worker_filter sums. HTTP level: cloud
#                            (:18793, BEESKY_POOL_POLL_S=1) + mock
#                            dashd S19 Pro (power_consumption 3210 W)
#                            + mock pool JSON server + agent — config
#                            round-trip without echoing the secret, a
#                            ~5% gap sampling quietly, the pool at
#                            40% of farm raising POOL_GAP, energy
#                            accumulating and the price being settable.
# The v0.9 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v8.sh

ENERGY_OUTPUT="$(python3 tests/mock_energy_pool_test.py)"
echo "$ENERGY_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.9 mock test — farm-vs-pool comparison + energy reports"
  echo
  echo "\`tests/mock_energy_pool_test.py\` checks the pool-config"
  echo "redaction + POOL_GAP rule + energy integration in-process"
  echo "against \`CloudStore\` (gap fires only on the second"
  echo "consecutive over-threshold sample, deduped to 1/hour; energy"
  echo "= power_w x dt with dt capped at 3x the agent interval),"
  echo "the generic pool adapter against an in-process mock pool"
  echo "(dot-path, GH/s -> TH/s, worker_filter), then builds the"
  echo "v0.5 cloud shape on 127.0.0.1: \`beesky cloud\` (:18793,"
  echo "password set, poll interval 1 s), the mock dashd S19 Pro"
  echo "(:18098, power_consumption 3210 W), a mock pool JSON server"
  echo "(:18123) and \`beesky agent --interval 1\`. Assertions: new"
  echo "endpoints -> 401 logged out; the miner record carries"
  echo "power_w 3210; the pool config round-trips with its secret"
  echo "header sent to the pool but never echoed by the cloud; a"
  echo "~5% gap samples quietly while the pool at 40% of farm"
  echo "raises a major POOL_GAP event; energy accumulates > 0 kWh"
  echo "and cost estimates follow the settable electricity price."
  echo
  echo "## Assertions + captured samples"
  echo
  echo '```'
  echo "$ENERGY_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.9 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
