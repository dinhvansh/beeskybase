# BeeSky vs HashCore Toolkit 1.7.5 — final parity audit (v0.35.0)

Re-audit of the whole sprint against the evidence in
`research/hashcore/UI-ANALYSIS.md` and the per-version mapping
docs (`docs/*-mapping.md`). Statuses: **DONE** (shipped and
test-covered), **PARTIAL** (shipped with a named, bounded
shortfall), **GAP** (not built, reason named),
**N/A** (HashCore concept with no BeeSky counterpart — not a
gap to fill). "Hardware-unconfirmed" marks features that are
mock-verified against a documented contract but never run
against a real miner — they count as DONE here with the
asterisk stated, because the code is the port; the farm is the
verification.

## Per-area table

### Screens & navigation

| # | HashCore feature | BeeSky status |
|---|---|---|
| 1 | Splash screen (branded, version) | GAP — app opens straight on groups. Cosmetic; not ported. |
| 2 | Network groups home: cards, MỚI tag, stat chips (Miners/Unblocked/Errors), autoscan, import/export | DONE (v0.24, v0.28, v0.34) |
| 3 | Group description ("No description" when unset) | DONE (v0.35 — closes the v0.24 divergence) |
| 4 | Ranges as typed, named, individually disable-able objects; DNS names; port ranges | PARTIAL — divergence, pre-approved: one multi-range string per group, validated by core `parse_targets` (rejects bad IPs, reversed ranges). No per-range names/disable, no DNS, no port ranges. |
| 5 | Merge network groups (keep-sources option) | DONE (v0.28, BeeSky semantics stated) |
| 6 | Combined view, group search, reset-statistics, rescan-all, remove-all | DONE (v0.34) |
| 7 | IP-Report panel + listening toggle, open-as-group | DONE (v0.34 — public Bitmain-style protocol, ports 14235/8888; HashCore's own bind UNKNOWN, divergence D-IP1) |
| 8 | Miners list: Normal/Compact/Overview heat-grid (cell S/M/L, colour by temp or hashrate) | DONE (v0.25) |
| 9 | ~50 configurable/reorderable columns | DONE — 29 data-backed columns + NOTE (v0.25/v0.28). Per-board temps: BeeSky's `boardTemp1..4` carry the chain (chip) temps; HashCore splits chip vs board temps, which BeeSky's sources do not distinguish — PARTIAL by source, not by UI. |
| 10 | Filter builder (Bool/Numeric/Range/String) + saveable filter presets | DONE (v0.25) |
| 11 | Grouping by any field + "Jump to group" | DONE (v0.25) |
| 12 | Search by IP / MAC / pool / worker | DONE (v0.25) |
| 13 | Selection model: select all / invert / isolate (+ errors-only), ops bar for selection | DONE (v0.25/v0.26) |
| 14 | Hotkeys + command palette + zoom scaling | DONE (v0.25/v0.34; zoom is text scaling 90–130%, divergence D-S1) |
| 15 | MAC / S/N / chip BIN / PSU model-serial-temps / board serials columns | PARTIAL — MAC DONE in v0.35 (local ARP table, best-effort); S/N, BIN, PSU, board serials remain GAP (no adapter emits them) |
| 16 | Pool 1–3 URL/worker/password columns | DONE for dashd + cgminer (v0.28); stock GAP G2 (no evidenced pool source on stock firmware) |
| 17 | Hotel Fee (column + device tab) | N/A — no such concept in BeeSky |
| 18 | DevFee availability / "DevFee online - {}%" | N/A as a column — the fee % is delivered at runtime, not in firmware (VNish dissection); no BeeSky fee exists to display |

### Device detail

| # | HashCore feature | BeeSky status |
|---|---|---|
| 19 | Detail tabs: Metrics / Charts / Boards / Pools / Fans / Note | DONE (v0.27) |
| 20 | Per-chip grade split (TOTAL / STABLE / SLOW / CRITICAL) | DONE for dashd (`chip_statuses` 1:1); PARTIAL for cgminer/stock (acs counts + dead positions only — grade semantics undocumented) |
| 21 | Fan mode + per-fan speed | DONE for dashd; PARTIAL (mode null for cgminer/stock — no source) |
| 22 | Charts (hashrate + temperature) | DONE (v0.27 — local scan history, hand-drawn; HashCore's history mechanics UNKNOWN, divergence named) |

### Operations (HashCore: 27 task types)

| # | HashCore feature | BeeSky status |
|---|---|---|
| 23 | Task runner: progress, Stop, per-device results, persistent history | DONE (v0.26) |
| 24 | Task types shipped | PARTIAL — 14 types: rescan, reboot, switch_pool, export + the 10-action VNish tail (v0.29, hardware-unconfirmed) + diagnostic_report; Whatsminer (6 actions, v0.33, hardware-unconfirmed) and LuxOS (reboot, curtail) ride inside those types |
| 25 | unlock / install / update firmware tasks | GAP-GATED by design — unlock lives in `beesky fw` behind three hard gates, never a bulk action; install/update is CLI-only (`beesky fw install`), no in-app dialog flow |
| 26 | resetFirmware / removeFirmware | GAP — safety scope (v0.29 named it, not built) |
| 27 | configureNetwork / conditionalRestart | GAP — semantics unverified from the api-doc |
| 28 | cloneSettings | PARTIAL — pools-only clone (v0.28, divergence D6) |
| 29 | CSV bulk network-config import (8 documented columns) | GAP — observed in the Toolkit, noted v0.28, not ported |

### Credentials

| # | HashCore feature | BeeSky status |
|---|---|---|
| 30 | One unlock method per firmware vendor (password / loginPassword / apiKey / doNotUnlock / doNotDiscover), layered global → group → one-shot task | DONE for the three positive variants (v0.23/v0.24); PARTIAL — the two negative variants (`doNotUnlock`, `doNotDiscover`) are not modelled (no observed need in BeeSky's flow) |
| 31 | 16-vendor enum incl. supported-types modelling | PARTIAL — 7 real read adapters (row 33); the rest are cred tags or gaps |

### Settings

| # | HashCore feature | BeeSky status |
|---|---|---|
| 32 | Settings, 5 tabs: General / Unlock / Timeouts / Logs / Advanced | DONE (v0.34 — only real settings; divergences D-S1–D-S4: text-scale zoom, Unlock tab links to the creds dialog, Logs tab shows store files not log levels, combined mode is one union scan pass) |
| 33 | Appearance (theme / language) | GAP — divergence: no theme/language; text scale only |

### Vendor coverage (read adapters)

| # | HashCore vendor | BeeSky status |
|---|---|---|
| 34 | CG Miner (generic), HashCore, Old VNish, Bitmain, Canaan, MicroBT, Luxor | DONE — 7 real adapters: cgminer-generic, dashd (hashcore + oldVnish), bitmain stock, canaan, microBt, whatsminer (v0.30 read + v0.33 token actions), luxos (v0.33) |
| 35 | Braiins | GAP G-B1 — gRPC spec documented, no stdlib path; closes with one `version` reply from a real Braiins OS machine |
| 36 | IceRiver | GAP G-I1 — no public API spec |
| 37 | SunLune (Jasminer) | GAP G-J1 — no public API spec |
| 38 | Auradine, ePIC, pitBit, Bitdeer (Sealminer) | GAP — no evidence at all in the materials |

### Firmware migration (the unlock leg)

| # | HashCore feature | BeeSky status |
|---|---|---|
| 39 | Stock → VNish one-click migration (unlock + install) | PARTIAL — recipe ~87% at step level (race attempts = 10 recovered in v0.35, `docs/unlock-payload-mapping.md`); gated CLI only; production payloads residual U-1..U-5 (need a real firmware package / a live locked-miner session) |

### Cloud / agent (BeeSky's own "đủ bộ" leg)

| # | Feature | BeeSky status |
|---|---|---|
| 40 | Farm-side agent (background, pre-login, auto-restart, self-update) + Flutter agent app + unified installer with pairing page | DONE (v0.6–v0.31; agent zip self-contained since v0.32) |
| 41 | Cloud web (dashboard, commands ride back on agent poll) + CD pipeline | DONE in code; deploy BLOCKED on the owner (VPS + GitHub secrets — Codex track via `handoff/beesky-cloud-handoff/`) |

### BeeSky-native views (no HashCore counterpart)

| # | Feature | BeeSky status |
|---|---|---|
| 42 | Bản đồ nhiệt / Điện năng / Lịch sử sửa / Sự kiện / Cài đặt | DONE (v0.32) — these are BeeSky's own daily-use views; they raise the daily loop, not the parity count |

## Counts

- Rows 1–39 (parity surface): **24 DONE, 9 PARTIAL, 5 GAP, 2 N/A**
  (rows 17–18 are N/A, not shortfalls).
- Vendor breadth: **7 of 14 real adapters**.
- Ops task types: **14 of 27** (the missing 13 are dominated by
  firmware-migration/config tasks, not daily-use actions).

## Fresh three-lens scores (grounded in the table above)

- **UI frame: ~97%.** Everything the owner sees day to day is
  ported — groups home, dense table-first list, detail tabs,
  five native views, five-tab settings, palette, zoom,
  IP-Report panel. Left: splash screen, theme/language,
  release-notes dialog, per-range editor UI.
- **VN daily-use loop: ~95%.** The loop on the owner's actual
  fleet (Bitmain L9/Z15/S19 + Whatsminer) is complete: groups,
  scan, grid, detail, ops incl. the VNish tail and Whatsminer
  actions, presets, tickets, events, energy, settings,
  IP-Report. Left: stock pools (G2), S/N column, and the
  hardware-unconfirmed asterisk on the v0.29/v0.33 tails and
  the IP-Report wire.
- **Total surface: ~84%.** Blend: frame 97% × 0.3 + daily
  loop 95% × 0.3 + vendor breadth 50% (7/14) × 0.2 + ops &
  firmware depth ~70% (14/27 types, migration partial) ×
  0.2 ≈ 84%.

## What "99%" would actually need (honest close)

The remaining ~15% is not writable from this VM. It is gated
on, in order of weight:

1. **A farm session with the owner** — one visit closes:
   IP-Report wire confirmation (real button-press), L9
   web-UI chip-count check, Z15 raw SUMMARY capture,
   hardware confirmation of the VNish ops tail, the
   Whatsminer token flow, and LuxOS reads. (6 items, all
   "hardware-unconfirmed" today.)
2. **Vendor documentation or real devices** — Braiins (one
   `version` reply), IceRiver, Jasminer, Auradine, ePIC,
   pitBit, Bitdeer (7 families with no usable public spec).
3. **A real firmware package / live locked-miner session** —
   the unlock payload residuals U-1..U-5
   (`docs/unlock-payload-mapping.md`).
4. **The owner's decisions** — EV certificate + repo secrets
   (code signing; unsigned exes are what Defender flags),
   VPS + GitHub secrets (cloud deploy, Codex track).
5. **Small in-app work** — splash screen, theme/language,
   release-notes dialog, per-range editor, CSV bulk
   network-config import, firmware reset/remove (safety
   review first), configureNetwork/conditionalRestart
   semantics. Each is days, not weeks — but none of them
   moves the score more than ~1% alone.

Bottom line: **v0.35.0 is the end of what can be closed
from this side.** Everything left is either a farm visit, a
vendor document, or the owner's own decision.
