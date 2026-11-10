#!/usr/bin/env bash
# v0.12 full mock suite: everything from v0.11.2 (v0.1..v0.11.2), then
# the history-sampling test for the cloud dashboard redesign.
#   run_mock_test_v11_2.sh  regenerates tests/RESULTS.md (v0.1..v0.11.2)
#   mock_history_test.py    store-level throttle/prune checks for the
#                           new history_samples table + HTTP checks of
#                           GET /api/history (401 logged out; ingests
#                           with explicit timestamps produce exactly
#                           the throttled points) + dashboard content
#                           assertions for the v0.12 redesign (sidebar
#                           nav, views, chart container, settings form
#                           ids) with every legacy marker intact.
# The v0.12 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v11_2.sh

HISTORY_OUTPUT="$(python3 tests/mock_history_test.py)"
echo "$HISTORY_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.12 mock test — cloud dashboard redesign (sidebar, history chart, settings forms)"
  echo
  echo "\`tests/mock_history_test.py\` covers the redesign's backend and"
  echo "content wiring. Store level: \`CloudStore.add_snapshot\` samples"
  echo "the new \`history_samples\` table at most once per site per"
  echo "60 s (snapshots at +0 s/+10 s -> one row, +70 s -> a second),"
  echo "row totals mirror the snapshot (summed TH/s, miner/problem"
  echo "counts, max temp), rows filter per site, and samples older"
  echo "than 30 days are pruned on the write path. HTTP level (real"
  echo "\`beesky cloud\`, password set): \`GET /api/history\` is 401"
  echo "logged out; after login, ingests carrying explicit timestamps"
  echo "yield exactly the throttled points and the \`?site=\` filter"
  echo "works; the served dashboard carries the sidebar nav (Tổng"
  echo "quan / Máy đào / Bản đồ nhiệt / Điện năng / Lịch sử sửa / Sự"
  echo "kiện / Cài đặt), the seven view containers, the history chart"
  echo "container, the topbar (site filter, last-update, logout) and"
  echo "the Cài đặt forms (pool config -> POST /api/pool-config with"
  echo "header-secrecy notes, electricity price -> POST /api/settings,"
  echo "current configs rendered header-names only), while every"
  echo "pre-v0.12 dashboard marker asserted by the older suites (heat"
  echo "map + heatColor thresholds, pool/energy panel ids, POOL_GAP,"
  echo "commands panel, official logo SVG) is still present. The"
  echo "cloud dashboard itself was rebuilt as a fixed-sidebar layout"
  echo "(230 px, icon/top-bar collapse under 900 px) over a new token"
  echo "set (bg #0B0B0D, panels #15151A, borders #232329, status"
  echo "#34D399/#FBBF24/#FB923C/#F87171, accent #F5D800); the local"
  echo "web dashboard received the same token palette as a CSS-only"
  echo "polish (no layout or JS changes)."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$HISTORY_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.12 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
