# v0.28.0 mapping — Pool presets · Clone config · Scan-record pools · IP-Report

Dissected FIRST (the dissect-before-porting rule), from the shipped
HashCore Toolkit 1.7.5 materials on disk
(`~/workspace/asic-os-s19pro/research/hashcore/`): the complete UI
string table (`toolkit-x64/data/flutter_assets/assets/translations/
en.json`, read in full), the Dart file map (`package-paths.txt`),
and the AOT string pools (`strings-libapp.txt`,
`deep/strings-libapp-off.txt`, `strings-toolkit_cli.txt`). BeeSky's
own side was audited against its code at the v0.27.0 tree
(file:line references below). Grades: **VERIFIED** = the literal
string/key/class is quoted from the materials; **INFERRED** =
strongly implied, not directly observed; **UNKNOWN** = not
observable from the shipped materials — never guessed.

This is the final leg of the parity sprint (v0.24 groups →
v0.25 grid → v0.26 operations → v0.27 device detail → v0.28
presets / clone / IP-Report).

---

## 1. Pool presets — the HashCore mechanism

### 1.1 Where presets live

- A dedicated service: `package:toolkit_services/services/
  presets_service/` — `presets/preset.dart` (base),
  `presets/pool_preset.dart` (`PoolPreset`, JSON-serialised:
  `PoolPreset.fromJson`, `_$PoolPresetFromJson` in the pools),
  `presets/filter_preset.dart`, `presets_service.dart`,
  `presets_storage_dto.dart` + `filters_storage_dto.dart`
  (VERIFIED, file map + AOT pools).
- The **Presets center** is one dialog with two tabs
  (VERIFIED, `presets_center_dialog`): `"title": "Presets
  center"`, `"pools": "Pools"`, `"filters": "Filters"`,
  `"new_preset": "New preset"`, `"duplicate_preset":
  "Duplicate"`, `"delete_selected"`, and the empty state
  `"presets_empty_title": "No presets created"` /
  `"presets_empty_description": "Create preset from
  corresponding dialog"` — i.e. presets are AUTHORED inside
  the pool-change / filter dialogs and MANAGED (edit /
  duplicate / delete) in the center; the center's own
  "New preset" routes back to those dialogs.
- A preset's identity is its **name** plus an **optional
  description** (VERIFIED, `edit_preset_dialog`:
  `"name_label": "Preset name"`, `"description_label":
  "Preset description - optional"`). Saving over an existing
  name asks first: `"override_prompt_title": "Override the
  existing preset?"`, `"Preset with this name already
  exists.\nDo you want to replace it with the current preset
  set?"`. Success toast: `"saved": "Preset saved"`.
- The exact JSON key names inside HashCore's storage DTOs are
  **UNKNOWN** (they do not survive in the string pools in an
  attributable form; recovering them would need full AOT
  disassembly). BeeSky's storage shape is therefore its own
  (§3) — a storage-internal divergence only; the behaviour
  surface matches.

### 1.2 Pool preset shape

- A pool preset holds up to **3 pool slots** (VERIFIED by
  structure: `EditPoolPresetView` renders `PoolPresetRow`s,
  one `EditPresetSinglePoolController` per slot; miners have
  exactly 3 pool slots everywhere else in the Toolkit —
  `device_info_pools_info`: `"Pool {} URL"`, `"Pool {}
  worker"`).
- Slot fields: **URL + worker** (VERIFIED labels above);
  **password** per slot is INFERRED (every pool DTO in the
  file map — `miner_pool.dart`, `antminer_pool_dto.dart`,
  `vnish_pool_dto.dart` — models url/user/pass triples, and
  the pool-change dialog edits full pool configs). BeeSky
  slots are `{url, worker, password}` (§3).
- In the pool-change dialog each slot additionally carries a
  per-slot **marker** (VERIFIED, `enum.pool_marker`):
  `"skip": "Don't change"`, `"edit": "Edit"`, `"empty":
  "Delete"` — a dialog-apply concept (which slots to touch),
  not part of the stored preset. BeeSky does not store
  markers: a preset slot left empty in the editor is simply
  absent from the stored list (§3 divergence, named).

### 1.3 The pool-change dialog (where presets are applied + saved)

VERIFIED (`miners_list.dialogs.pool_change` + pool literals):

- `"pool_presets": "Pool presets"`,
  `"pool_preset_placeholder": "Select pool preset to apply"`,
  `"edit_preset": "Edit pool preset: {}"`,
  `"new_preset": "New preset"`.
- `"data_info": "In group editing, the data of the first
  selected device is displayed"` — a multi-device edit shows
  the FIRST selected device's current pools as the working
  data.
- `"worker": "Worker"`, `"worker_variables": ": see available
  variables under \"+\""`, `"show_patterns": "Show available
  patterns"`, `"preview": "Preview: {}"` — the worker field
  offers pattern variables and a LIVE preview.
- `"save": "Save pools config"` — applying runs as a task
  (`models/tasks/implementations/change_pools_task.dart`,
  `switch_pool_task.dart`, `models/tasks/types/
  pool_change.dart` — the v0.26 task system BeeSky already
  ported).
- `"preset_unavailable_tooltip": "Preset saving unavailable:
  make sure there are no errors in the dialog and the first
  pool has non-empty values"` — a preset can only be saved
  when slot 1 is fully filled.

### 1.4 Worker pattern tokens — the exact set (VERIFIED twice)

Source A — the AOT help text (strings-libapp.txt, verbatim):

```
You can use patterns for changing pools for worker field:
 - {account} use current account (pool user/worker before first "." charter)
 - {worker} use current worker (pool user/worker after first "." charter)
 - {ip:.} IP with "." as octets divider
 - {ip1}, {ip4}, {ip3}, {ip4} patterns to insert octets from miner IP
 - {host} or {h} from hostname (Anthill only)
 - {mac} for MAC address (Anthill only)
 - {n:1:1} number start 1 with step 1
 - {nn:1:1} number with 1 leading zero
 - {nnn:1:1} number with 2 leading zeros
```

(The `{ip1}, {ip4}, {ip3}, {ip4}` line repeats ip4 — a typo in
the original help text; source B resolves the set.)

Source B — `enum.change_pool_pattern` (en.json, VERIFIED):
`account` "Current account" · `worker` "Current worker" ·
`ip` "IP (with \".\" as octets divider)" · `ip1`..`ip4`
"IP: First..Fourth octet" · `mac` "MAC-address (without
divider)" · `host` "Hostname" · `n` "Number (start 1 with
step 1)" · `nn` "Number with 1 leading zero" · `nnn`
"Number with 2 leading zeros" · `proto-str` "Stratum
protocol" · `pool-host` "Current pool address" · `port`
"Current pool port". The enum also lives at
`screens/miners_list_screen/dto/change_pool_pattern_enum.dart`.

So the token universe is: `{account}` `{worker}` `{ip:.}`
`{ip1}` `{ip2}` `{ip3}` `{ip4}` `{mac}` `{host}` `{h}`
`{n[:start[:step]]}` `{nn[:…]}` `{nnn[:…]}` `{proto-str}`
`{pool-host}` `{port}`. Patterns apply to the **worker field**
(help text's own scope). Semantics fixed by the sources:

- `{account}` / `{worker}`: the device's CURRENT pool user
  split at its first "." (before / after). "Anthill" in the
  help text is the HashCore/VNish firmware brand — its
  `{host}` / `{mac}` caveat means those two resolve only
  where the firmware reports hostname / MAC.
- `{n…}`: a per-device sequential number parameterised
  `start:step` (the evidenced literal is `{n:1:1}`); `nn` /
  `nnn` zero-pad to 2 / 3 digits (1 / 2 leading zeros).
- `{proto-str}` / `{pool-host}` / `{port}`: parsed from the
  device's CURRENT pool URL (enum labels; the brace literal
  form is INFERRED from the enum keys by the same convention
  as the evidenced tokens).
- **UNKNOWN**: what `{n}` counts (selection order? sorted
  order? a per-task counter in completion order?) and what
  an unavailable token expands to in HashCore (empty string?
  literal? task error?) — neither is observable from the
  shipped materials.

### 1.5 BeeSky token support (the port)

`beesky/core/patterns.py` (core) and the mirrored Dart
expander in `app_flutter/lib/presets.dart` (used for the
editor preview) implement the SAME table:

| Token | BeeSky source | When the source is absent |
|---|---|---|
| `{ip:.}` / `{ip:<div>}` | target IP | never (target IP always known) |
| `{ip1}`..`{ip4}` | target IP octets | never |
| `{n[:s[:k]]}` `{nn}` `{nnn}` | device index in the job's target list (see below) | never |
| `{account}` / `{worker}` | current pool-1 user from the enriched scan record | **PatternError → per-device failure** (named divergence from HashCore's UNKNOWN behaviour: failing loudly beats writing a guessed worker) |
| `{pool-host}` / `{port}` / `{proto-str}` | current pool-1 URL from the enriched record | PatternError → per-device failure |
| `{mac}` | record MAC — **no adapter emits one** (§4) | PatternError → per-device failure, reason says the data is not carried (mirrors HashCore's own "Anthill only" gating, with a different gate) |
| `{host}` / `{h}` | record hostname — not carried | PatternError → per-device failure |
| unknown / malformed `{…}` | — | PatternError → per-device failure (never silently passed through) |

`{n}` semantics — BeeSky choice (the original's is UNKNOWN,
§1.4): the device's 1-based position in the **job's target
list**, in listed order: value = start + (position − 1) ×
step. Deterministic under parallel workers because it keys
off the list, never completion order. `{account}` with no
"." in the current user = the whole string, `{worker}` =
"" (the faithful reading of "before / after first '.'").

---

## 2. Clone settings — HashCore vs the BeeSky port

HashCore's Clone settings dialog (VERIFIED, `clone_settings`
keys) mirrors a source miner's **whole firmware settings
profile**: sections General / Theme / Timezone / Language /
Cooling (mode, fan duties, water temp) / Performance
(preset, autoswitcher, global voltage/freq) / Advanced
(ASIC Boost, throttling, power limit, checks…) / Fees
(DevFee region, HotelFee) / **Pools** (`"pool_nr": "Pool
{}"`). Cloning = writing that profile to other miners.

**BeeSky port (named scope divergence)**: pools-only clone.
The full profile is not portable honestly — BeeSky has no
write primitive for cooling/performance/fee settings on any
family (v0.26 audited exactly one config write: dashd
`/settings`, used by switch_pool). v0.28 clones the pool
configuration: the source is the detailed (or first
selected) miner, its pools are read through the v0.27
`inspect` path, and the slots are applied to the other
selected miners through the same pools-payload task (§3).
Consequences, all stated in the app's confirm step:

- dashd inspect pools carry url + user but **no password**
  (the summary's PoolStats has no pass field) — a cloned
  slot therefore sends no password, and the target keeps
  **its own** existing per-slot password (the
  `_switch_pool_dashd` fallback to the old slot's `pass`).
- The source miner itself is excluded from the targets
  (writing its own pools back is a no-op with side
  effects); cloning with only the source selected is
  refused in the UI with the reason.
- Non-dashd targets fail per device via the existing
  executor, exactly like a preset apply.

---

## 3. BeeSky build — presets + apply + storage

- **Storage**: `GridConfig` (the v0.25 store,
  `beesky-grid.json`) gains a `pool_presets` list next to
  `filter_presets`. A pool preset is
  `{name, description?, slots: [{url, worker, password}]}`
  — up to 3 slots; empty editor slots are dropped, so slot
  position = pool_id. (HashCore's own storage keys are
  UNKNOWN, §1.1 — this shape is BeeSky's, matching the
  field set the dissection verified.)
- **Presets center**: a "Trung tâm mẫu" dialog (toolbar,
  next to Bộ lọc / Cột) with the two HashCore tabs —
  **Bộ lọc** (the existing filter presets: list, apply-
  free management = delete / duplicate) and **Pools**
  (create / edit / duplicate / delete). Creating a pool
  preset happens in its editor (name, description, 3 slot
  rows, the pattern help — HashCore's "Show available
  patterns" — and a live worker Preview against the first
  selected device, mirroring §1.3's first-device rule);
  saving requires slot 1 filled (the §1.3 tooltip rule)
  and a same-name save replaces after the editor says so
  (BeeSky's filter presets already replace-by-name; the
  center keeps one behaviour for both kinds).
- **Apply**: Operations bar → "Áp mẫu pool" → pick a
  preset → ONE `switch_pool` ops job whose payload is
  `{"pools": [{url, user, password?}, …]}` (worker strings
  ride RAW — patterns expand core-side per device, since
  `{n}` / `{ip…}` / current-pool tokens differ per device
  and only the runner knows the target list). The runner
  validates the pools payload before any I/O (1–3 slots,
  url+user non-empty per slot, mutually exclusive with the
  legacy single-slot payload) and executes slots in order
  per device via the existing `actions.execute`
  (pool_id = slot position), stopping at the first failed
  slot; the history entry is a normal v0.26 switch_pool
  task. Legacy single-slot jobs are byte-compatible.
- **Clone**: Operations bar → "Chép cấu hình pool" builds
  the same pools payload from the source's inspect doc
  (slots without url/user are skipped) plus
  `"clone_from": <source ip>` (informational; the runner
  ignores it) and runs it over the selection minus the
  source.

---

## 4. Scan-record pool enrichment — the BeeSky-side audit

v0.25 left the grid's Pools columns a named DATA-GAP
(docs/grid-mapping.md §3.2: "scan records carry NO pool
data at all"); v0.27 fetched pools only on demand via
`inspect`. v0.28 fills the RECORD where a normal scan
genuinely exposes the data:

| Family | Source during a normal scan | Cost | v0.28 |
|---|---|---|---|
| vnish (dashd) | the `/summary` the fetch already downloads carries `miner.pools` (PoolStats) — `inspect.py:213-228` reads exactly this list from exactly this payload | **zero** extra I/O | record gains `pools` in `DashdClient.fetch_record` (dashd.py) |
| cgminer | the RPC `pools` command — `CgminerClient.pools()` (cgminer.py:130) existed unused by scans; inspect §2 proved it answers on this family | **+1 RPC call** per cgminer miner, same client + fetch timeout as the summary/stats calls the fetch already makes; failure/ refusal → field omitted, record unaffected | `pools` attached in the cgminer branch of `cli._fetch_record` and `ops._fetch_record` |
| stock | **no source**: the status CGI carries no pool list (inspect.py:34-39); inspect's RPC attempt is opportunistic — and a stock candidate exists precisely because the RPC summary did not claim the host (discover.py probe order), so a scan-time RPC pools call would re-ask a channel that already failed | n/a | **omitted during scan** (named); inspect remains the deep path |

Record shape (one shape for every family that has data):
`pools: [{url, worker, status}]` — `worker` is dashd's
`user` / cgminer's `User` normalised to the key the app's
`PoolInfo` already parses (models.dart:91-105, which also
accepts `user`); `status` passes through **verbatim**
(dashd "alive", cgminer "Alive" — no case folding, no
mapping). Records without pool data OMIT the key entirely
(the v0.25 parse tolerates both). This lights up, with no
app-side fetch: the grid's Pool 1–3 URL/Worker columns +
Pools view mode (their `dataGap` flags come off — the data
now exists for 2 of 3 families; stock rows render "—"),
grid search (url + worker were already in the haystack),
and the detail Pools tab, whose first branch already
prefers `rec.pools` (home_page.dart `_poolsTab`).

---

## 5. IP-Report — RESEARCH-GAP (not built)

### 5.1 What the evidence DOES verify

- The feature exists: `package:toolkit_services/services/
  ip_report_service/ip_report_service.dart` — class
  `IpReportService` with `_ipReportListener`,
  `_onIpReportReceived`, `_onIpReportStatusChanged`
  (AOT pools, VERIFIED).
- A settings toggle: `ipReportListenerEnabled`;
  `settings_dialog.appearance.ip_report` = "IP Report
  listening", `…_desc` = "Enables IP-Reports listening in
  the network" (VERIFIED).
- The panel lives on the Network groups screen
  (`screens/common/components/app_screen/app_screen_
  content/ip_report_action_panel.dart`): `"IP Report
  listening started"`, `"Failed to start IP Report
  listening"`, `"Received IP Report: {}"`; a received
  address can be **opened as a network group**
  (`ip_report_panel.tooltip`), and modifier keys
  select / isolate the reported devices in the current
  group (VERIFIED strings).
- The only IP-report DTOs in the entire codebase are
  **Auradine's**: `dto/miner/auradine/
  auradine_ip_report_dto.dart` +
  `auradine_ip_report_response_dto.dart` (fromJson /
  toJson), referenced from `AuradineLockedDeviceApi.
  ipReport` and `BaseAuradineRepository.
  _updateIpReportFields`, alongside the path strings
  `/ipreport` and `/ipreport2` (VERIFIED pools + file
  map).

### 5.2 What is MISSING — the wire format

None of the following is evidenced anywhere in the
shipped materials, and each is required to build a
listener honestly:

1. **Transport + port of the Toolkit's listener.** No
   port number, bind address, or socket option in either
   string pool is attributable to `IpReportService`.
   (`RawDatagramSocket` symbols exist in the pools, but
   they are generic dart:io symbols also present in the
   CLI's scanner code — attribution would be a guess.
   `HttpServer` appears in neither pool.)
2. **The packet/payload format.** The Auradine DTOs'
   JSON field names do not survive in the pools in an
   attributable form, and the `/ipreport` paths are the
   **miner-side device API** (the Toolkit calling an
   Auradine miner), which says nothing about what a
   broadcast sender transmits or what the Toolkit's own
   listener parses.
3. **The sender set.** Whether reports come only from
   Auradine firmware, or also from Antminer hardware
   IP-report buttons / VNish firmware, is not observable
   — the DTO evidence points Auradine-only, the panel's
   placement suggests broader use; both readings are
   speculation.

### 5.3 Decision

**Not built in v0.28** — no `beesky ipreport`, no app
toggle, no fixture invented to fill the hole. Building
any of it would require choosing a port and a packet
shape out of thin air — precisely what the dissection
rule forbids. To close the gap, ONE of these evidences
suffices: a packet capture from a real miner's IP-report
send with the Toolkit listening; a blutter-grade
disassembly of `ip_report_service.dart` + the Auradine
DTOs recovering field names + the bind call; or
HashCore documentation of the listener. The §5.1 surface
(placement, toggle, group-opening) is recorded so the
port can proceed the day the wire evidence exists.

---

## 6. Stretch items (v0.24–v0.27 named leftovers)

- **Grid Note column**: v0.27 left the note app-side only
  (detail tab). v0.28 adds a `note` column ("GHI CHÚ") to
  the grid universe fed by the app's note store: records
  are decorated app-side (`MinerRecord.note`, keyed by
  `deviceKeyFor` exactly like the note store) wherever
  records land — scan results, rescan replacements, note
  saves. The wire record does NOT gain the field (notes
  are the app's data, not the miner's); `toJson` does not
  emit it. Sort/filter/search see the decorated value
  through the column's normal text path.
- **Group merge** (v0.24 gap §2.6): the groups screen
  gains "Gộp nhóm" — merge group B into group A with
  `mergeGroups` (groups.dart, pure + tested): A keeps its
  id/name/autoscan; targets = the union of both target
  specs (comma-joined, item-deduped); creds = A's sets
  then B's sets not already present (identity = label +
  user + type + api_key); last_scan = the NEWER of the
  two when both exist, the existing one when only one
  side was ever scanned, null only when neither was —
  a merged group that either side scanned is not "new".
  (Semantics are BeeSky's choice — HashCore's
  merge internals are UNKNOWN; its existence and menu
  placement are VERIFIED.)
- **"Lưu & quét"**: the group editor gains a second
  submit — save the group and immediately enter + scan
  it (the editor returns `(group, scanAfter)`; the home
  page routes scanAfter through the existing
  `_scanGroup`). HashCore's editor behaviour here is
  UNKNOWN; this is a BeeSky UX addition, named as such.

---

## 7. Divergence / gap register (summary)

| # | Item | Status |
|---|---|---|
| D1 | Preset storage JSON keys differ from HashCore's (theirs UNKNOWN) | divergence (storage-internal only) |
| D2 | No per-slot Don't change/Delete markers stored in presets | divergence (markers are dialog state in the original too) |
| D3 | Pattern tokens needing unavailable data FAIL the device (HashCore: UNKNOWN) | divergence, deliberate |
| D4 | `{mac}` / `{host}` unresolvable in BeeSky (no source data) vs HashCore's Anthill-only gating | gap (data), behaviour mirrored |
| D5 | `{n}` = position in the job's target list (HashCore's counting UNKNOWN) | named choice |
| D6 | Clone = pools-only vs HashCore's whole-profile clone | scope divergence (no write primitive for the rest) |
| D7 | Cloned slots carry no password; target keeps its own | consequence of the data, stated in UI |
| G1 | **IP-Report: NOT BUILT — wire format is a RESEARCH-GAP** (§5.2 lists the missing evidence) | gap |
| G2 | Stock scan records carry no pools (no scan-time source) | gap (data); inspect covers it on demand |
| — | Also observed, out of scope: HashCore's CSV bulk network-config import (8 documented columns, AOT help text) | noted, not ported |

