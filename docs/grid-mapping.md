# Data-grid miners list — HashCore Toolkit → BeeSky behaviour mapping (v0.25.0)

Written BEFORE the port, per the dissect-before-porting discipline.
Every HashCore claim below is graded:

- **VERIFIED** — seen in the shipped Toolkit 1.7.5 materials on disk:
  the full translation table (`toolkit-x64/data/flutter_assets/assets/
  translations/en.json`, keys quoted), the AOT string pools
  (`toolkit-x64/strings-libapp.txt`), the Dart file map
  (`toolkit-x64/package-paths.txt`), and the prior analysis
  `research/hashcore/UI-ANALYSIS.md` §2.2.
- **INFERRED** — strongly implied by structure/naming, not observed.
- **UNKNOWN** — not observable from the materials on disk. The port
  does NOT invent these; where BeeSky must choose, the choice is
  marked DIVERGENCE.

---

## 1. The two view axes (VERIFIED)

HashCore's miners list has TWO independent axes, both in
`dto/ui_dialog_constants/columns_configuration/`:

| Axis | Enum | Values (en.json) |
|---|---|---|
| View TYPE (density) | `enum.miner_list_view_type` | `normal` "Normal" · `compact` "Compact" · `overview` "Overview" |
| View MODE (data) | `enum.miner_list_view_mode` | `metric` "Metric" · `pools` "Pools" · `custom` "Custom" |

Each view type has its own builders, including GROUP containers
(`screens/miners_list_screen/builders/{standard,compact,overview}/…`),
so densities, grouping and the rest compose. Header labels:
`miners_list.header.view_mode` "View mode", `data_mode` "Data mode".

**BeeSky:** MATCH. View type = Thoải mái / Gọn / Tổng quan; view
mode = Số liệu / Pools / Tùy chỉnh. Both persisted in
`beesky-grid.json` (§8).

## 2. Overview (heat grid) — VERIFIED

- Overview is a grid of per-miner cells
  (`miner_list_overview_item.dart` + a tooltip-content extractor —
  cells carry a tooltip with the miner's details).
- Colour metric: `enum.miner_list_overview_mode` = `hashrate`
  "Hashrate" | `temperature` "Temperature / C°". Header label
  `miners_list.header.cell_size` "Cell size".
- Cell size: `enum.miner_list_overview_size` = `small` "Small" ·
  `medium` "Default" · `large` "Large".
- The exact colour SCALE (which value → which colour) is **UNKNOWN**
  — no scale constants are attributable in the string pools.

**BeeSky:** MATCH on structure (grid of cells, colour-metric toggle,
S/M/L sizes, tooltip per cell, click selects the miner and opens the
detail panel). DIVERGENCE (forced, scale unobservable): BeeSky's
temperature scale is absolute bands — < 70 °C ok-green, 70–80 muted
yellow, 80–85 orange, ≥ 85 °C red (the core's TEMP_LIMIT_C rule that
already governs the table's NHIỆT pills). Its hashrate scale is
relative within the fleet per native unit (a miner is tinted by its
share of the fleet's best rate IN THE SAME UNIT — mixed units never
share a scale, the v0.20 lesson). Records with no value render grey.

## 3. Columns — VERIFIED universe, BeeSky data audit

- The column universe is `enum.miner_field_enum_column` (~68 keys;
  several labelled "N/A" — `currentPreset`, `topPreset`,
  `pool1worker`, `pool1password`, pool 2/3 worker/password,
  `hotelFeeEnabled/Worker/Percent` — i.e. present as FIELDS but not
  offered as columns). Header actions: `header.columns` "Columns",
  `header.columns_order` "Columns order", `header.columns_reset`
  "Reset to defaults". Persistence is a device-columns-configuration
  DTO (`columns_configuration/device_columns_configuration.dart`,
  `column_configuration_item.dart`); its exact JSON keys are
  **UNKNOWN**.
- Per-board temperatures exist as FIELDS
  (`enum.miner_field_enum.chipTempBoard1..4` "Board N chip
  temperatures", `boardTempBoard1..4`) though the `_column` label map
  carries only the combined `chipTemp` / `boardTemp`. BeeSky offers
  the per-board CHIP temps as optional columns (the brief's call);
  its records carry ONE temp per chain, so per-board PCB temps are a
  data gap (§9).
- Fields are organised for the filter/column menus by
  `enum.miner_field_group_enum`: ungrouped · hashrate · presets ·
  pools · hotelFee · psu · board. (BeeSky's dialogs are flat lists —
  27 columns do not yet need the grouping; noted, not hidden.)

### 3.1 BeeSky record schema audit (VERIFIED from the core)

`beesky/core/report.py::_finalise_record` emits: `ip, model, source,
elapsed_s, ghs_5s, ghs_av, ths, rate_value, rate_unit, power_w,
chains[{index, chips_total, chips_alive, dead_positions, temp_c,
chips_missing}], fans_rpm, chips_alive, chips_total, max_temp_c,
problems[{code, detail, …}], status`; the scanner adds `cred_label`
(v0.23). The Dart model parsed only a subset — `elapsed_s`,
`ghs_5s`, `power_w` were ON THE WIRE but unparsed. Extending the
Dart parse is NOT a core change; NO core change is made in v0.25.

### 3.2 Column mapping (HashCore field → BeeSky column)

| HashCore field | BeeSky column | Source / verdict |
|---|---|---|
| ip | IP | `ip` ✓ |
| model | MODEL | `model` ✓ |
| firmware | NGUỒN | `source` family label (VNish / Bitmain gốc / cgminer RPC) — family only; version/build strings are a gap |
| hashrate "Average hashrate" | HASHRATE | `rate_value`+`rate_unit` (native unit) ✓ |
| chipTemp | NHIỆT | per-chain `temp_c` list, combined cell (v0.22 behaviour) ✓ |
| fanSpeed "Fans" | QUẠT | `fans_rpm` ✓ |
| minerStatus | TRẠNG THÁI | core `status` → OK / CHECK / ERROR chip ✓ (BeeSky 3-state; HashCore's 9-state `miner_status_enum` NOT ported — status semantics belong to the core) |
| — (no HC column) | CHIP | BeeSky's `chips_alive/chips_total` — a BeeSky column kept from v0.22; the owner's primary health signal |
| uptime | UPTIME | `elapsed_s` ✓ (wire, newly parsed) |
| power | ĐIỆN (W) | `power_w` ✓ (wire, newly parsed; null on classic Bitmain) |
| instantHashrate "Realtime" | HASHRATE RT | PARTIAL: `ghs_5s` exists but only in GH/s-family terms; shown (as TH/s) only for TH/s-family records. For MH/s / ksol/s records the wire carries no separate realtime value → "—" (§9) |
| efficiency | HIỆU SUẤT (J/TH) | DERIVED: `power_w / ths` when both exist (TH/s records), else "—". Arithmetic on real record fields, not a fabricated source |
| algorithm | THUẬT TOÁN | DERIVED from `rate_unit` (ksol/s → Equihash, MH/s → Scrypt, TH/s → SHA-256) — the same family conventions the core's `_native_rate` uses |
| chainStatus "Chains" | BOARD | `len(chains)` ✓ |
| badChainsCount | BOARD LỖI | DERIVED: chains with `chips_missing > 0` ✓ |
| errorCode | MÃ LỖI | `problems[].code` joined ✓ |
| chipTempBoard1..4 | BOARD 1..4 | `chains[i].temp_c` ✓ (red ≥ 85 °C like the combined cell) |
| pool1url / pool2url / pool3url | POOL 1 / 2 / 3 | **DATA-GAP**: scan records carry NO pool data at all (verified: `build_record` never attaches pools; the scanner never fetches POOLS). Columns exist and parse an optional wire `pools` list if a future core emits one; today they render "—" |
| pool1worker … (N/A as HC columns; fields exist) | POOL n WORKER | **DATA-GAP**, same as above |
| — (BeeSky v0.23) | ĐĂNG NHẬP | `cred_label` — which saved login authenticated ✓ |
| mac | MAC | **CLOSED in v0.35**: the core fills it from the host's local ARP table (`beesky/core/arp.py`, best-effort per scan); the column's `dataGap` flag is off. An IP with no ARP entry still renders "—". |
| serial | S/N | **DATA-GAP**: no serial in records |

### 3.3 HashCore columns NOT offered (all DATA-GAPs, §9)

`range` (records don't carry the range they were found in),
`lockState`, `hasPics`, `findMiner` (an action, not data),
`stockHashrate`, `throttling`, `minerPreset`, `chainSerials`,
`chainModels`, `chainChipBins`, `psuModel`, `psuSerial`,
`psuPfcTemp`, `psuLlcTemp`, `platform`, `installType`,
`firmwareBuildDate`, `firmwareBuildName`, `note` (HashCore notes
are per-device USER data edited in the device-info dialog — that
dialog is v0.27 scope), `boardTemp` + `boardTempBoard1..4` (PCB
temps — BeeSky has one temp per chain), `cooling`, `hotelFeeUrl`
(+ fee fields), `defFeeOnline`, `powerLimit`.

## 4. Sorting — VERIFIED

Header carries `header.sort_by` "Sort by", `header.sort_direction`
"Sort direction", `header.sort` "Sorting"; a sort-fields menu exists
(`miner_list_screen_sort_fields.dart`). Sorting is by a field with a
direction. **BeeSky:** MATCH — click a column header to sort by it,
click again to flip direction (asc/desc arrow in the header).
BeeSky sort keys: IPs compare octet-numerically (never
lexicographically); rates compare within native-unit families
(values normalised to each family's smallest unit, families ordered
by the canonical unit order — cross-unit numeric comparison would
repeat the v0.20 bug); nulls sort last in both directions.

## 5.
...[truncated 7370 chars]