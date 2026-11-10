#!/usr/bin/env bash
# v0.13 full mock suite: everything from v0.12 (v0.1..v0.12), then
# the agent-management + icons test for the cloud dashboard.
#   run_mock_test_v12.sh     regenerates tests/RESULTS.md (v0.1..v0.12)
#   mock_agents_ui_test.py   store-level checks (agent_views carries
#                            no key material; revoke flips auth via
#                            agent_by_key; a pre-v0.13 database is
#                            migrated — agents table gains the
#                            revoked column) + HTTP checks (agent
#                            endpoints 401 logged out; POST
#                            /api/agents mints a key returned exactly
#                            once; GET /api/agents lists it without
#                            the key or its SHA-256 anywhere; a real
#                            snapshot ingest with the minted key
#                            succeeds and shows the agent online;
#                            after POST /api/agents/revoke the same
#                            ingest is 401) + dashboard content
#                            assertions for the v0.13 additions
#                            (Agent & trại section ids + one-time-key
#                            panel, seven inline sidebar nav icons,
#                            four stat-card icon chips, logout icon)
#                            with every legacy marker intact.
# The v0.13 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v12.sh

AGENTS_OUTPUT="$(python3 tests/mock_agents_ui_test.py)"
echo "$AGENTS_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.13 mock test — dashboard icons + agent management UI"
  echo
  echo "\`tests/mock_agents_ui_test.py\` covers the v0.13 additions."
  echo "Store level: \`CloudStore.agent_views\` never carries key"
  echo "material (neither the plaintext key — never stored — nor its"
  echo "SHA-256 hash); \`revoke_agent\` flips the new \`agents.revoked\`"
  echo "flag and the revoked key immediately fails \`agent_by_key\`,"
  echo "the single lookup behind every agent-facing endpoint (ingest,"
  echo "command claim/result), while its history rows stay put; a"
  echo "pre-v0.13 database is migrated on open (ALTER TABLE adds the"
  echo "column) and its legacy agents keep authenticating until"
  echo "revoked. HTTP level (real \`beesky cloud\`, password set):"
  echo "all three agent endpoints are 401 logged out; POST"
  echo "/api/agents mints through the same store path as"
  echo "\`cloud-add-agent\` (\`secrets.token_urlsafe(32)\` ->"
  echo "\`create_agent\`) and returns the raw key exactly once; GET"
  echo "/api/agents lists id/site/created/last-seen/online/revoked"
  echo "with the key and its hash absent from the payload; a real"
  echo "snapshot ingest with the web-minted key succeeds and flips"
  echo "the agent online; revoke validates its input (400 non-integer"
  echo "id, 404 unknown id) and afterwards the same ingest is 401."
  echo "Dashboard: the Cài đặt view gains an \"Agent & trại\" panel"
  echo "(create form, one-time key panel with copy buttons and a"
  echo "ready-to-run \`beesky agent\` command prefilled with the"
  echo "page origin, registered-agents table with Thu hồi buttons)"
  echo "above the pool form, and the whole cloud UI gains inline"
  echo "Lucide-style stroke icons — seven sidebar nav icons"
  echo "(layout-grid / server / thermometer / zap / wrench / bell /"
  echo "gear), four stat-card icon chips (building / cpu / activity /"
  echo "alert-triangle) and a log-out icon, all currentColor so the"
  echo "active nav state colours its icon with the accent; the local"
  echo "web dashboard received the same stat-card chips (server /"
  echo "activity / alert-triangle / thermometer) as a pure HTML/CSS"
  echo "addition. Every pre-v0.13 dashboard marker asserted by the"
  echo "older suites is still present."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$AGENTS_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.13 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
