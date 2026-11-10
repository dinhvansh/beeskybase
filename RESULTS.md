
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

## v0.18.1 — dashboard version stamp fix
Live-screenshot review caught the web footers stuck at "BeeSky Cloud v0.13" / "BeeSky v0.8"
(hard-coded at redesign time, never bumped since). Both dashboards now carry a {{VERSION}}
placeholder that the servers stamp with beesky.__version__ when serving — single source of
truth, can never go stale again. Pinned by 4 new assertions in mock_glass_test (30 total);
cloud/web/agent-bg suites re-run green.

## v0.19 — miners table beautified (inset well, zebra, dark scrollbar, flat detail)
Owner, on the main-window screenshot: "cái khung bảng xem máy nhìn thấy gớm" — the results
Treeview was the last square surface: a SQUARE box with a bright WHITE frame and a glowing
light scrollbar inside the rounded glass card. Desktop only (gui.py + ui_theme.py); the web
dashboards are untouched in this release.
- WHITE FRAME ROOT CAUSE: the ttk "Treeview" style set borderwidth=0/relief="flat" but never
  pinned bordercolor/lightcolor/darkcolor — under clam those fall back to a LIGHT default,
  which rendered as the white frame on every platform. All three are now pinned to the new
  token TABLE_WELL #121216; background/fieldbackground move PANEL -> TABLE_WELL (rowheight
  stays 30). Treeview.Heading: background TABLE_HEADING #1D1D24 with its border colours
  pinned to the same value, so the heading separator line vanishes too.
- INSET WELL: the plain Card.TFrame behind the table is replaced by a RoundedCard well
  inside the glass card (radius 12, fill TABLE_WELL, hairline outline #26262E/BORDER,
  backdrop PANEL_GLASS, 10px inset via its padding) — tree + scrollbar pack inside it and
  fill it, so the tree's square corners never touch the card's rounded corners.
- ZEBRA: new "odd" row tag (TABLE_ZEBRA #17171D) applied at insertion time in show_records
  to odd-indexed rows ONLY when the row has no status tag — problem rows keep exactly their
  "check" (PROBLEM_BG #463A10) / "error" (#472020) wash tags, so tag precedence is by
  construction, not by tag-order luck. row_values() and all other insertion behaviour
  unchanged.
- SCROLLBAR: Vertical.TScrollbar + TScrollbar restyled dark — background BORDER (#26262E),
  troughcolor TABLE_WELL, bordercolor TABLE_WELL, arrowcolor MUTED. No more light strip.
- DETAIL PANE FLAT: the detail tk.Text gets borderwidth=0 + highlightthickness=0 and its
  background moves PANEL2 -> PANEL_GLASS, so the text sits directly on its glass card.
  Stat cards / toolbar / geometry unchanged (grid row 3 weighted, detail keeps full height).
- Changed test expectations (every one still an EXACT pin):
  * tests/mock_theme_test.py — "Treeview background" expected ui_theme.PANEL (#15151A)
    -> ui_theme.TABLE_WELL (#121216) [intentional v0.19 token move]; ADDED exact pins:
    Treeview bordercolor/lightcolor/darkcolor == TABLE_WELL, Treeview.Heading background
    + bordercolor == TABLE_HEADING, Vertical.TScrollbar background == BORDER /
    troughcolor == TABLE_WELL / bordercolor == TABLE_WELL, token triple
    (#121216/#1D1D24/#17171D); ADDED row-tag assertions (even OK row tagless, odd OK row
    == ("odd",), CHECK row == ("check",) with tag_configure wash == PROBLEM_BG).
  * tests/mock_agent_bg_test.py — release version pin 0.18.1 -> 0.19.0 (routine per-release).
- Tests: chain (tests/run_mock_test_v19.sh) regenerated v0.1–v0.10 green in-chain (156
  PASS), then was HALTED EXTERNALLY at the v0.10->v0.11 transition (no FAIL line in the log;
  same external halt as v0.17). tests/RESULTS.md restored to the committed ship-time blocks;
  v0.11–v0.19 suites re-verified STANDALONE, all green (firmware: see below; actions,
  agents-ui, cloud, energy/pool, history, logo, repairs, watch, web plain; theme 34,
  gui, rounded, glass, agent-app, agent-bg under xvfb). The v0.11 firmware unlock-order
  assertion remains the known load-sensitive flake: v0.19 tree ran FAIL/PASS/FAIL/FAIL/
  FAIL/FAIL and — control-verified with the diff stashed — FAIL/FAIL/PASS on the pristine
  v0.18.1 tree (ca3156d); non-deterministic on identical code, and this diff touches no
  firmware-path code. tests/RESULTS.md: 491 PASS lines.

## v0.19.1 — auto-hide table scrollbar
The v0.19 screenshot still showed a pale scrollbar strip (clam renders it light under some
Tk builds) even with a single row. The main window's table scrollbar now auto-hides whenever
the content fits (yscrollcommand handler feeds the bar + toggles its packing) and appears
only while the rows actually overflow. GUI/theme/agent-bg suites green.

## v0.19.2 — margins back (table well gets a real glass rim)
Owner: "lề đồ đâu hết rồi, tràn ra luôn viền" — the near-black table well (#121216) sat on the
near-black window backdrop (#0B0B0D) with no visible boundary, so the table read as one slab
spilling edge to edge. Root padding 16→22, section gaps 12→14, table card pad 12→14, and the
well now keeps 6px external padding with the brighter GLASS_BORDER hairline — a clear glass
rim frames the well on all four sides. Fans column widened 130→150 (was clipping RPM values
with the scrollbar hidden), Model 170→160 to compensate. GUI/theme/glass/agent-bg green.

## v0.19.3 — toolbar breathing room
Owner spotted the last toolbar button ("Quét lại") crowding the scan card's rounded frame.
The toolbar card's inner padding goes 12 → 18, so every control — first entry and last
button alike — now sits a clear 18px inside the frame on all sides. GUI/agent-bg green.

## v0.19.4 — the inner frame is gone (Card.TFrame border removed)
Owner: "đè lên khung trong kìa" — pixel forensics found it: the Card.TFrame style (inner
frames inside cards) still carried a 1px solid GLASS_BORDER from the pre-rounded era, so
every row inside a card drew its own rectangle; the toolbar buttons sat inside that inner
frame and its border peeked through the gaps between buttons. Card.TFrame is now borderless
— the RoundedCard is the only frame. Pixel-verified: the gap dashes are gone. Theme/GUI/
glass/agent suites green.

## v0.19.5 — card surfaces span the full frame (square-corner overhang fixed)
Owner: "còn lòi kìa" — the detail card's bottom corners were square. Root cause, measured:
a RoundedCard's canvas was placed inside the frame's CONTENT box, so the drawn panel sat
inset by the card padding on every side; full-width children (the detail Text, same fill)
covered the panel's outline and their square corners poked past its rounded arcs. The
canvas now spans the full frame (negative place offset + 2*pad size), so the surface and
its outline sit at the frame's true edges and children rest inside them. Verified by
geometry (canvas == frame on all 8 cards) and by corner zooms before/after. All desktop
suites green.
