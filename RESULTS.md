
## v0.15.1 — main-window layout fix (post-screenshot review)
The v0.15 live screenshot showed the results Treeview (default 10 rows) consuming the whole
1080x680 window and squeezing the "Chi tiết máy đã chọn" detail card out of view. Fix: Treeview
height=7 visible rows, window 1120x730 (minsize 940x620). Verified by re-running the GUI smoke +
theme suite (green) and a fresh live screenshot with a scanned miner selected — detail card
(dead-chip positions, fan speeds) now visible under the table.

## v0.15.2 — main-window balance fix (supersedes v0.15.1)
v0.15.1's screenshot still showed the detail card crushed (root request 943px vs 730px window;
pack starves the last widgets). v0.15.2 converts the main window's section layout from pack to
grid with the table row weighted (minsize 150): the table now absorbs any shortfall and the
detail pane always keeps full height. Card padding trimmed (16->12), detail text 5 lines,
default window 1120x880. Measured on the live window: header 67 / toolbar 153 / stats 110 /
table 253 (of 270) / detail 191 full / footer 24 — everything visible, GUI + theme suites green.

## v0.16.0 — agent background service + install security
The agent now runs truly in the background and the install is hardened:
- NEW windowless twin `beesky-agentw.exe` (same PyInstaller Analysis as beesky-agent.exe,
  console=False), shipped by BeeSkyAgentSetup and listed in the signed update manifest.
  A frozen agentw — or `run --background` — never opens the config GUI (a bare agentw
  launch IS a background run), sends all output to `agent.log` next to the config
  (~1 MB rotation, one .old), and rewrites `agent-status.json` after EVERY cycle via a
  new AgentService status hook (atomic temp+replace: ts/ok/miners/error/cloud_url/site).
  Console runs mirror the same output to console + log.
- install-task v2 registers via generated Task Scheduler XML (schtasks /Create /XML):
  SYSTEM (S-1-5-18) + HighestAvailable, BootTrigger (PT30S) + LogonTrigger, Hidden,
  ExecutionTimeLimit PT0S, RestartOnFailure PT1M x5, no battery stops, action =
  beesky-agentw with the config path baked in. `install-task --console` is the
  farm-debugging escape hatch.
- Key protection: on Windows the agent key is stored DPAPI-protected
  (CRYPTPROTECT_LOCAL_MACHINE so the SYSTEM task can decrypt; `key` written empty,
  `key_protected` base64) — protects against the file being copied off the machine,
  not against local admins. Elsewhere the config is chmod 0600 after every save
  (Windows also gets a best-effort owner+SYSTEM icacls). A protect failure degrades
  to plain text rather than losing the config; legacy plain-text configs migrate on
  next save; an undecryptable foreign blob loads as an empty key.
- Log hygiene: the agent key is scrubbed at every failure print (beesky.agent.redact)
  and across the whole run stream (key + Bearer value). A non-local http:// cloud URL
  logs a one-time-per-run warning and shows the same hint under the config window's
  Cloud URL field — advisory only, never a hard block.
- Config window gains a "Trạng thái chạy ngầm" card (status pill + last-cycle detail +
  Xem log button) fed by agent-status.json.
- Tests: new tests/mock_agent_bg_test.py — 52/52 PASS standalone (DPAPI branch forced
  via the _dpapi_available probe with a reversible fake for the OS crypto; task XML
  assertions; run --once/--background e2e vs real cloud + mock dashd incl. status/log
  contents and key-free logs on success AND wrong-key cycles; GUI status card + http
  hint under xvfb). Full chain: v0.1–v0.10 regenerated green in-chain (156 PASS), then
  stopped at the KNOWN v0.11 firmware race-order assertion (kill idx 3 vs first.bmu
  idx 5) — control-verified PRE-EXISTING: the pristine v0.15.2 tree (dc4b0e3, changes
  stashed) fails it with byte-identical indices, and this release touches no
  firmware-path code. Every later suite was re-verified standalone against the v0.16
  tree (logo, history, agents-ui, agent-app 41, theme 25, GUI, cloud — all green), so
  the ship-time v0.11–v0.15 evidence blocks in tests/RESULTS.md are kept verbatim,
  exactly as v0.12–v0.15 handled the same flake. tests/RESULTS.md: 364 PASS lines.

## v0.17 — rounded-corner overhaul (UI/UX Pro Max tokens)
New beesky/rounded.py: Canvas-drawn RoundedCard (r=16), RoundedButton (r=12; hover lighten /
press darken / focus ring / >=36px tall / keyboard activation), RoundedEntry (accent outline
on focus), RoundedPill (full-round) — ttk cannot do border-radius, so the shapes are drawn.
Applied to every card, button, form entry and pill in both desktop apps; ttk kept for the
Treeview/scrollbars (data surfaces). ui_theme.card/status_pill signatures unchanged (delegate
to the rounded widgets); no behaviour assertion weakened (one release-pin moved 0.16.0->0.17.0).
Web dashboards: radius tokens unified (--radius-card 16px / --radius-widget 12px /
--radius-pill 999px). Design tokens + provenance: docs/design-tokens.md.
Evidence: chain regenerated v0.1-v0.10 in-chain (156 PASS) then was halted externally with no
FAIL line; tests/RESULTS.md restored to the committed ship-time blocks and the v0.11-v0.17
suites re-verified standalone (all green; the known v0.11 unlock-order assertion reproduced
FAIL/PASS/FAIL back-to-back on the identical tree — timing flake, disclosed as before).
tests/RESULTS.md: 397 PASS lines.

## v0.18 — Liquid Glass (real glass web, simulated glass desktop)
Owner approved chasing the 2026 trend (Apple iOS 26 Liquid Glass). Brand palette unchanged.
- Web (beesky/cloud/dashboard.html + beesky/web/dashboard.html) — REAL glass: ambient layered
  body backdrop (radial glows rgba(245,216,0,.07) + rgba(70,100,180,.06) over #0B0B0D,
  background-attachment: fixed); glass tokens --glass rgba(255,255,255,.045) /
  --glass-line rgba(255,255,255,.09) / --glass-soft .05 / --glass-line-soft .10 /
  --glass-chrome (sidebar, top bars) / --glass-head (table headers, rgba .03) /
  --glass-hover; backdrop-filter blur(16px) saturate(150%) (soft tier blur(10px)) on cards,
  panels, stat tiles, sidebar, topbar/header, settings panels, table containers;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 8px 32px rgba(0,0,0,.35). Inputs +
  ghost buttons (.btn-action/.btn-danger) + icon chips get the soft tier; the accent CTA
  stays solid #F5D800; table rows stay transparent so dense data remains readable.
  Fallbacks: @supports not (backdrop-filter) AND @media (prefers-reduced-transparency:
  reduce) re-point every glass token at the pre-v0.18 solids and set the blur tokens to
  none — zero layout/DOM change. No class/id/JS changes anywhere.
- Desktop — SIMULATED glass (Tk cannot blur; docs say so plainly): new ui_theme tokens
  PANEL_GLASS #191920 (card fill), GLASS_BORDER #34343E, RIM_LIGHT #3D3D4A, GHOST_FILL
  #22222B, ENTRY_FILL #1E1E26, ENTRY_BORDER #30303C. RoundedCard + ghost RoundedButtons
  draw a real 1px rim-light line (top arc + straight, inset 1px, canvas tag "rim") on every
  redraw — resizes never double it; disabled ghosts drop the rim. Card-hosted ttk styles
  (Card.TFrame/TLabel/Section/Sub/Hint, StatTitle/Stat, Card.TCheckbutton) and every
  in-card widget backdrop moved PANEL -> PANEL_GLASS so labels blend with the drawn
  surface; the stat value label in gui.py likewise. Pills + accent button stay solid;
  Treeview keeps solid PANEL inside its glass card.
- Changed test expectations (every one still an EXACT pin):
  * tests/mock_theme_test.py — "Card.TFrame background" expected ui_theme.PANEL (#15151A)
    -> ui_theme.PANEL_GLASS (#191920) [the style genuinely renders on glass now];
    ADDED an exact pin of the six glass tokens (#191920/#34343E/#3D3D4A/#22222B/#1E1E26/
    #30303C). No other theme assertion touched (PANEL/PANEL2/BORDER constants unchanged).
  * tests/mock_agent_bg_test.py — release version pin 0.17.0 -> 0.18.0 (the routine
    per-release pin: docstring + __version__/installer.iss/agent.iss comparisons).
  * Derived shade (code, not a test pin): RoundedButton ghost hover #26262E -> #2B2B36
    so hover stays perceptible on the lighter GHOST_FILL.
  * No dashboard-CSS assertions existed in the web/cloud/agents suites (they pin brand
    #F5D800 + DOM markers) — none needed changing; the radius-token assertions in
    mock_rounded_test pass unchanged.
- Tests: new tests/mock_glass_test.py — 26/26 PASS (per-dashboard: glass tokens,
  backdrop-filter, ambient backdrop, both fallbacks, shadow token, solid CTA; desktop:
  card fill/outline pins, exactly-one-rim incl. after resize, ghost rim + colour triple,
  disabled-ghost behaviour, entry fill/border pins). Chain: v0.1–v0.10 regenerated green
  in-chain, then stopped at the KNOWN v0.11 firmware race-order assertion (kill idx 3 vs
  first.bmu idx 5) — control-verified PRE-EXISTING: pristine v0.17 tree (b5fdd90, changes
  stashed) fails it standalone with byte-identical indices (ident=0 first=5 kill=3
  second=8 marker=11) and this diff touches no firmware-path code. tests/RESULTS.md
  restored to ship-time blocks; v0.11–v0.18 suites re-verified standalone, all green
  (logo, history, agents-ui, agent-app 41, agent-bg 52, theme, rounded, glass 26, GUI,
  cloud, web). tests/RESULTS.md: 423 PASS lines.
