#!/usr/bin/env bash
# v0.16 full mock suite: everything from v0.15 (v0.1..v0.15), then
# the agent background-service test.
#   run_mock_test_v15.sh       regenerates tests/RESULTS.md (v0.1..v0.15)
#   mock_agent_bg_test.py      key protection (DPAPI branch forced
#                              via the _dpapi_available probe with a
#                              reversible fake for the OS crypto:
#                              protected save carries no plain key,
#                              protect failure degrades to plain
#                              text, POSIX save chmods 0600, legacy
#                              plain-text configs migrate on save,
#                              foreign blobs load as an empty key)
#                              + log redaction + the v2 task XML
#                              (SYSTEM S-1-5-18, HighestAvailable,
#                              BootTrigger PT30S + LogonTrigger,
#                              Hidden, PT0S, RestartOnFailure
#                              PT1M x5, beesky-agentw action, the
#                              --console escape hatch) + packaging
#                              (spec's fourth exe beesky-agentw
#                              console=False, agent.iss ships it,
#                              workflow artifact/Release/manifest)
#                              + end-to-end (real cloud + mock
#                              dashd; `run --once` writes
#                              agent-status.json ok/1 miner and a
#                              key-free agent.log; a wrong key
#                              records ok=false and still leaks no
#                              key; --background keeps stdout
#                              silent; a non-local http:// cloud
#                              warns but is not blocked) + the
#                              config-GUI status card and http
#                              hint under xvfb-run.
# The v0.16 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v15.sh

BG_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_bg_test.py)"
echo "$BG_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.16 mock test — agent background service + install security"
  echo
  echo "\`tests/mock_agent_bg_test.py\` covers the v0.16 changes."
  echo "BACKGROUND: the spec gains a windowless twin \`beesky-agentw\`"
  echo "(console=False, same Analysis as \`beesky-agent\`); a frozen"
  echo "agentw — or \`run --background\` — never opens the config GUI,"
  echo "routes all output through a redacting stream into \`agent.log\`"
  echo "next to the config (rotated at ~1 MB, one .old), and rewrites"
  echo "\`agent-status.json\` after EVERY cycle via the AgentService"
  echo "status hook (ok / miners / error / cloud_url / site, atomic"
  echo "temp+replace). \`install-task\` now registers the task from"
  echo "generated XML (\`schtasks /Create /XML\`): SYSTEM principal"
  echo "(S-1-5-18) at HighestAvailable, BootTrigger (PT30S delay) +"
  echo "LogonTrigger, Hidden=true, ExecutionTimeLimit PT0S,"
  echo "RestartOnFailure PT1M x5, battery-proof, action = the"
  echo "windowless exe with the config path baked in;"
  echo "\`install-task --console\` is the debugging escape hatch."
  echo "SECURITY: on Windows the agent key is DPAPI-protected in the"
  echo "config (CRYPTPROTECT_LOCAL_MACHINE so the SYSTEM task can"
  echo "decrypt; \`key\` written empty, \`key_protected\` base64) —"
  echo "off Windows the file is chmod 0600 after every save (Windows"
  echo "also gets a best-effort owner+SYSTEM icacls); a protect"
  echo "failure degrades to plain text rather than losing the"
  echo "config, and legacy plain-text configs migrate on next save."
  echo "The agent key is scrubbed from every failure print"
  echo "(\`beesky.agent.redact\`) and from the whole run stream; a"
  echo "non-local http:// cloud URL logs a one-time warning and"
  echo "shows the same hint in the config window (never a hard"
  echo "block). The window gains a 'Trạng thái chạy ngầm' card"
  echo "(status pill + last cycle detail + Xem log) fed by"
  echo "agent-status.json. All v0.14/v0.15 assertions run green"
  echo "inside the full chain above; the new suite adds:"
  echo
  echo '```'
  echo "$BG_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.16 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
