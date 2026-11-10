#!/usr/bin/env bash
# v0.14 full mock suite: everything from v0.13 (v0.1..v0.13), then
# the standalone agent-app test.
#   run_mock_test_v13.sh       regenerates tests/RESULTS.md (v0.1..v0.13)
#   mock_agent_app_test.py     config-model checks (save/load
#                              round-trip; default-path resolution:
#                              env override, fake APPDATA on a
#                              simulated win32 platform, ~/.beesky
#                              fallback; tolerant from_dict) +
#                              packaging assertions (spec's third exe
#                              beesky-agent with the official icon;
#                              packaging/agent.iss ->
#                              BeeSkyAgentSetup-<version>.exe, both
#                              .iss version defines in sync with the
#                              package; CI builds the agent installer
#                              and ships exe + setup in artifact,
#                              Release and the update-manifest list) +
#                              updater basename match for
#                              beesky-agent.exe against a signed local
#                              manifest + end-to-end (real cloud +
#                              mock dashd; the agent app driven FROM
#                              A CONFIG FILE: `test` exits 0 / TEST
#                              OK and the snapshot lands in /api/sites
#                              + /api/miners, `run --once` exits 0, a
#                              wrong key makes `test` exit 1) + the
#                              config-GUI smoke under xvfb-run
#                              (fields, key mask toggle, save writes
#                              the JSON, auto-start button disabled
#                              off Windows).
# The v0.14 evidence block is appended to tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

bash tests/run_mock_test_v13.sh

AGENT_APP_OUTPUT="$(xvfb-run -a python3 tests/mock_agent_app_test.py)"
echo "$AGENT_APP_OUTPUT"

{
  echo
  echo "---"
  echo
  echo "# v0.14 mock test — standalone BeeSky Agent app"
  echo
  echo "\`tests/mock_agent_app_test.py\` covers the agent app."
  echo "Config model (\`beesky/agent_config.py\`): save/load is"
  echo "lossless, parent dirs are created on first save, unknown"
  echo "keys and a non-dict \`notify_config\` are tolerated, and"
  echo "\`default_config_path\` resolves \$BEESKY_AGENT_CONFIG first,"
  echo "then %APPDATA%\\BeeSky\\agent-config.json on Windows"
  echo "(simulated platform + fake APPDATA), then"
  echo "~/.beesky/agent-config.json. Packaging: the PyInstaller spec"
  echo "gains a third Analysis/EXE \`beesky-agent\` (console build,"
  echo "official icon, GUI datas for the config window's logo);"
  echo "\`packaging/agent.iss\` installs it as"
  echo "BeeSkyAgentSetup-<version>.exe with Start Menu/desktop"
  echo "shortcuts that open the config window; both installers'"
  echo "version defines match the package version; the Windows"
  echo "workflow builds agent.iss and ships beesky-agent.exe +"
  echo "BeeSkyAgentSetup-*.exe in the build artifact, the GitHub"
  echo "Release and the signed update-manifest file list — the"
  echo "updater assertion proves a signed manifest entry named"
  echo "beesky-agent.exe is matched by basename and applied (with"
  echo ".old backup), so the agent app self-updates through the"
  echo "v0.10 channel unchanged. End-to-end: against a real"
  echo "\`beesky cloud\` and tests/mock_dashd.py, the app is driven"
  echo "purely by a config file — \`beesky-agent test\` exits 0 with"
  echo "TEST OK and the snapshot is visible in /api/sites and"
  echo "/api/miners (VNish S19 Pro), \`run --once\` exits 0, and a"
  echo "config with a wrong key fails \`test\` with exit 1; off"
  echo "Windows, install-task prints systemd/cron guidance. The"
  echo "config GUI smoke runs under \`xvfb-run\`: window + five"
  echo "fields construct, the key entry masks/unmasks via the"
  echo "'Hiện key' toggle, Lưu cấu hình writes JSON that loads back"
  echo "identically, and the auto-start button is disabled off"
  echo "Windows."
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$AGENT_APP_OUTPUT"
  echo '```'
} >> tests/RESULTS.md

echo
echo "V0.14 MOCK SUITE PASSED — evidence appended to tests/RESULTS.md"
