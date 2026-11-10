
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

## v0.19.6 — default scan target = the machine's own subnet + multi-range targets
Field test on the owner's laptop: BeeSky's hard-coded default 192.168.1.0/24 found 0 miners
(his fleet is on 192.168.2.0/24; BTC Tools found all 63 there) and read as "méo quét đc".
New discover.default_scan_target(): primary LAN IPv4 via the UDP-connect trick (no packet
sent) → its /24; any failure, loopback, link-local or unspecified → 192.168.1.0/24; never
raises. It pre-fills the main GUI target, the agent config window on first run (a saved
config still wins), the GUI's empty-field fallback, and `gui --target` (default None →
helper). Fields stay editable — pre-fill only. AgentConfig's "" default is untouched
(empty = unconfigured is the config contract). Also multi-range: parse_targets() now
builds the comma-separated union explicitly — per-item parsing unchanged, de-duplicated
preserving first-seen order (single spec ⇒ byte-identical list to before), MAX_HOSTS cap
on the union, one bad item still rejects the whole spec; CLI/agent help texts now say
comma mixes scan several ranges at once. New suite tests/mock_targets_test.py (35 checks,
socket layer + per-app helper seams stubbed — no real subnet in any assertion);
mock_agent_bg release pin 0.19.5 → 0.19.6. Chain (tests/run_mock_test_v19_6.sh): targets,
GUI, agent-app, agent-bg, theme, rounded, glass all green (229 PASS lines), plus watch and
web suites re-run green since they feed targets through the same parser.

## v0.19.7 — first-run view fixes: auto-select first miner + window fits the screen
Field reports from the owner's first real fleet scan (63 miners on 192.168.2.0/24): (1) after
the scan nothing was selected, so the detail pane kept its placeholder "Chọn một máy trong
bảng..." and he concluded details could not be viewed; (2) the fixed 1120x880 window was
taller than his laptop's usable screen (Windows scaling) — the bottom sank under the
taskbar and the flexible table row collapsed to about one visible row. Both fixed in
beesky/gui.py only. The scan-completion handler (_poll_queue's records branch) now calls
_land_on_first after show_records: with ≥1 row it selects + focuses the first row, scrolls
it into view and fills the detail pane through the same _on_select path a click uses (rows
are rebuilt each scan, so the selection can never point at a dead row); with 0 rows it
restores the placeholder instead of leaving a previous scan's detail. show_records itself
is unchanged — the theme test calls it directly, where no landing is wanted. _fit_window
replaces the fixed center_window call: size = min(1120, screen_w − 32) × min(880,
screen_h − 72), centred; minsize (940, 720) now tracks the cap so it can't fight it on a
small screen. On a large screen the window is exactly 1120x880 as before, now centred
(verified: 1280x1024 → +80+72; 1500x1100 → +190+110). gui --smoke additionally prints the
post-scan selection, detail first line and fitted geometry; mock_gui_test gains an
empty-scan phase (127.0.0.2: selection "-", placeholder intact) and asserts selection =
first row, detail = first miner, geometry = the fitted formula centred and fully on
screen. Chain (tests/run_mock_test_v19_7.sh): GUI, theme, rounded, glass, agent-app,
agent-bg, targets all green (236 PASS lines).

## v0.20.0 — unit-correct hashrate for L9/Z15 fleets + diagnosis calibration
Field evidence (owner's photos, same 63-miner fleet, same laptop): BTC Tools reports the
Antminer L9 at 14.54 MH/s RT (avg 16.1) and the Antminer Z15 at ~1101 ksol/s RT; BeeSky
v0.19.7 (source "cgminer RPC") showed the L9 row as "0.01" in its TH/s column, a fleet
total of 12153.83, chip count 330/369 for the L9, and 51 of 63 machines flagged CHECK.

WHERE THE UNIT ASSUMPTION LIVED. beesky/core/report.py::build_record read the cgminer
SUMMARY's "GHS 5s"/"GHS av" (fallback "MHS av"/1000) into GH/s, and _finalise_record set
ths = gh/1000 — every rate was squeezed into TH/s regardless of what the field actually
measured, and every surface then summed record["ths"] blindly (GUI stat card, both
dashboards' total cards, cloud sites_summary/farm_ths/history sampler). The cgminer field
NAME encodes the unit family, but for two fleet models the fields lie by omission: an
L9's bmminer reports the Scrypt rate in the MHS pair (MHS av = 14540 for a 14.54 MH/s
machine; its GHS av twin, 14.54, is the same figure ÷1000 and meaningless), while a Z15
reports its sol rate in raw sol/s inside the GHS fields (GHS av ≈ 1,101,000 for a
1101 ksol/s machine — the only reading under which the photo's garbage fleet total
decomposes: ~11 Z15s × ~1101 ≈ 12153.83).

THE FIX. Records now carry rate_value + rate_unit (native unit) next to the untouched
legacy fields. _native_rate(summary, model) resolves them in order: (1) explicit
"KSol/s 5s/av" → ksol/s, "Sol/s 5s/av" → ksol/s if ≥1000 else sol/s; (2) Z-series model
(regex \bZ\d{1,2}\b) + GHS fields → value = GHS_main/1000, unit ksol/s; (3) L-series
model + MHS pair present → value = MHS_main/1000, unit MH/s (fires only when BOTH GHS
and MHS exist, so an MHS-only reply keeps the pre-existing gh fallback and is labelled
by rule 4); (4) field family: GHS → TH/s (gh/1000), MHS-only → MH/s (mhs/1000); 5s
preferred over av, mirroring ths. Legacy fields (ths, ghs_5s, ghs_av) are computed
byte-identically — the S19 record is pinned field-by-field against tests/mock_scan.json.
Displays render the native value+unit: GUI table + detail pane, CLI table (header
"TH/s" → "Hashrate"), both dashboards' miner tables and heat tiles, repair tickets.
Fleet totals aggregate ONLY within a unit (report.fleet_rate_totals /
format_rate_totals, canonical order TH/s · GH/s · MH/s · ksol/s · sol/s, thousands
separators on grouped figures): a single TH/s group renders exactly as before (the
desktop stat card keeps its bare number; a single non-TH/s group shows value+unit;
mixed shows the grouped string). Records without rate fields (old agents, stored
snapshots) read back as (ths, "TH/s") everywhere via report.record_rate.

DIAGNOSIS AUDIT — THE L9's 330/369. "369" is NOT from a BeeSky model table: BeeSky has
no model/chip table anywhere (grep-verified). build_record counts the machine's OWN
stats reply: chips_total = Σ len(chain_acsN), alive = count of 'o'. 369 = 3 chains ×
123 chars from the L9's own cgminer stats; 330 = its 'o' count. The CHECK flag is
MISSING_CHIPS ×3 (13 dead positions per chain) — the machine reporting fewer live
chips than its own chain strings claim. NO diagnosis rule was changed: that
self-contradiction is a genuine finding BY DESIGN and stays flagged. Two honest
caveats: (a) the flagged L9 simultaneously reported its full rated hashrate, which is
inconsistent with 39/369 truly dead chips under SHA256 acs semantics; (b) whether
bmminer's chain_acs maps 1 char = 1 ASIC chip on Scrypt/Equihash firmware is NOT
verifiable from here (see open questions) — the counts may be an enumeration artifact
of a different per-board layout. The other rules are unit-safe as-is: NO_HASHRATE is a
zero check, OVER_TEMP is absolute °C. The 51/63 CHECK count cannot be decomposed from
the photo alone; BTC Tools' all-"success" is weak counter-evidence (it does no chip
diagnosis), and per-machine photos would be needed to attribute the rest.

EVENTS. HASHRATE_DROP was verified unit-safe in structure (a drop % against the
miner's OWN rolling baseline) but tracked the ths series and hard-coded "TH/s" in its
prose; it now tracks the native rate series (legacy ths fallback for old records) and
names the native unit; payload keys (baseline_ths/current_ths) are unchanged — for
non-SHA256 miners they carry the tracked native-scale values. Transition note: an
agent upgrading mid-watch mixes scales in one 12-sample window for a non-SHA miner,
which can fire at most one spurious drop/gain cycle until the window flushes.

CLOUD / ENERGY. Energy math was audited end to end: _integrate_energy integrates
power_w samples only and never consumed the mixed total — unchanged. The surfaces that
DID consume it are fixed: farm_ths, the history sampler and sites_summary.total_ths
now sum report.ths_equivalent() (H/s family only: TH/s → v, GH/s → v/1000,
MH/s-display → v/1000; sol units → excluded). An Equihash-only site now yields
farm_ths = None and the pool poller skips it instead of comparing the pool against a
raw sol sum; sites_summary gains grouped rate_totals, which the cloud dashboard
renders (per-site line + fleet card). History rows written BEFORE this fix keep their
poisoned totals (stored data is not rewritten); new samples are clean.

TESTS. New suite tests/mock_units_test.py (50 assertions): L9 fixtures (av-only →
"14.54 MH/s"; 5s+av → 5s wins; MHS-only → fallback intact) with the photo's stats
(330/369, MISSING_CHIPS ×3, CHECK), Z15 fixtures (→ "1101.00 ksol/s", healthy → OK),
explicit Sol/s/KSol/s conventions, S19 regression vs mock_scan.json, grouped totals,
GUI row values, CLI table, tickets, cloud-store aggregations (mixed site total_ths
102.91 + 3 rate groups; Z15-only site farm_ths None; legacy snapshot unchanged), and
event drops in native units. Chain note: the nested historical chain halted mid-run
repeatedly in this sandbox (different server suite each attempt, no FAIL echoed — the
v0.17/v0.19 pattern), so the release evidence in tests/RESULTS.md is a standalone
sweep: all 18 suites green at the v0.20.0 code (493 PASS lines across the sweep),
with the known v0.11 firmware `unlock order` timing flake disclosed there (fired
repeatedly, reproduced identically on the pristine v0.19.7 tree via git-stash
control; passed standalone under nice and inside a nice'd v11 script run). No test
expectation was weakened. Version pins: __init__ + both .iss + mock_agent_bg_test
0.19.7 → 0.20.0.

OPEN QUESTIONS FOR A LIVE-FLEET CHECK (kept, not guessed): (1) chain_acs semantics on
Scrypt/Equihash bmminer — capture ONE L9's raw cgminer stats reply and its web-UI
chip counts and compare against BeeSky's 330/369 before trusting MISSING_CHIPS on
these models; if acs proves not to be 1 char = 1 chip there, the follow-up fix is to
suppress chip counting for non-SHA256 models. (2) The Z15 GHS-field = raw sol/s
reading rests on the fleet-total decomposition + BTC Tools' display, not a raw
capture — capture one Z15 SUMMARY reply to confirm the field set (and whether real
"Sol/s"/"KSol/s" fields exist, which rule (1) already prefers). (3) Equihash/Scrypt
models behind the dashd API are out of scope (that catalogue is SHA256; the boards
path takes TH/s inputs by contract). (4) A pre-v0.20 AGENT at a mixed site still
sends ths-only records for its L9/Z15 miners — those display as TH/s (legacy
fallback) until the agent is upgraded to v0.20.0.
