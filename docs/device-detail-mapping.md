# Device detail tabs — HashCore Toolkit → BeeSky behaviour mapping (v0.27.0)

Dissected BEFORE building, per the dissect-before-porting rule.
Evidence: the Toolkit's shipped translation table
(`research/hashcore/toolkit-x64/data/flutter_assets/assets/
translations/en.json`, the `device_info_dialog.*`,
`device_info_board_info.*` and `device_info_pools_info.*` keys),
`research/hashcore/UI-ANALYSIS.md` §2.3, the VNish dashd OpenAPI
document (`research/vnish/rootfs/usr/share/dashd/ui/docs/
api-doc.json` — the firmware HashCore itself manages), and a
file:line audit of BeeSky's own adapters and record builder.

## 1. The original, as observed

HashCore's row detail is a **modal dialog** (`device_info_dialog`)
with tabs (translation keys VERIFIED):

| Tab | Keys | Content |
|---|---|---|
| Metrics | `device_info_dialog.metrics` | the device's headline numbers |
| Charts | `.charts`, `.hashrate`, `.temperature` | hashrate + temperature line charts (fl_chart) |
| Boards | `.boards`; `device_info_board_info.board_nr` "Board {}", `.total` "CHIPS TOTAL: ", `.stable` "STABLE: ", `.slow` "SLOW: ", `.critical` "CRITICAL: " | per board: chip counts in four buckets |
| Pools | `.pools`; `device_info_pools_info.pool_url` "Pool {} URL", `.pool_worker` "Pool {} worker" | one URL + worker row per pool slot |
| Fans | `.fans`, `.fans_mode` "Mode", `.fans_speed` "Speed", `.fan_nr` "Fan {}" | fan mode + per-fan speed |
| Hotel Fee | `.hotel_fee` | the hotel-fee arrangement for the device |
| Note | `.note`, `.note_placeholder` "Device note", `.save_note` "Save note" | an editable per-device note with an explicit Save button (a field of the dialog, not a tab of its own) |

How the original READS the data: the Toolkit manages VNish-family
firmware through the dashd API, whose `/summary` document is the
single source for almost every tab (§2). Its Charts history
mechanics (session-only vs persisted, sampling interval) could
NOT be observed from the shipped materials — **UNKNOWN**, not
guessed; BeeSky's own chart design is named as a divergence in
§4 instead of pretending to copy an unobserved mechanism.

## 2. What the firmware actually exposes (the data audit)

### 2.1 VNish / HashCore dashd (`beesky/core/dashd.py`)

`GET /api/v1/summary`'s `AntmMinerStats` (api-doc schema) carries
FAR more than the scan record keeps:

- `pools`: `PoolStats[]` — `{id, url, pool_type, user, use_tls,
  status (offline|working|disabled|active|rejecting|unknown),
  accepted, rejected, stale, ping, …}` (api-doc `PoolStats`).
  BeeSky's `fetch_record` drops it entirely.
- `cooling`: `Cooling{fan_num, fans: Fan{id, rpm, status
  (ok|lost), max_rpm}, settings: FanSettings{mode}, fan_duty}`.
  `FanSettings.mode` is a tagged object: `{name: "auto", param}`
  | `{name: "manual", param}` | `{name: "immersion"}` (api-doc
  `FanSettingsMode`). BeeSky keeps only the rpm list
  (dashd.py `fetch_record`, the `cooling.get("fans")` read).
- `chains[]`: each board carries `chip_statuses{red, orange,
  grey}` COUNTS and `chip_temp{max}` / `pcb_temp{max}` ranges.
  The counts are used today only to derive chips_total/alive
  (dashd.py, the summary-only fallback in `fetch_record`).
- `GET /api/v1/boards`: per-chip `{id, hr, grade, temp, …}` —
  grade ∈ grey/orange/red. BeeSky already fetches it during a
  scan and keeps only the red chips' positions.

Grade semantics (dashd.py module doc, from the firmware's own
behaviour): **grey = normal, orange = degraded but hashing,
red = dead**. That is a 1:1 map onto HashCore's buckets for the
firmware HashCore itself ships:

    STABLE = grey · SLOW = orange · CRITICAL = red · TOTAL = sum

### 2.2 cgminer RPC (`beesky/core/cgminer.py`, `report.py`)

- The scan record's chains derive from the STATS `chain_acsN`
  strings (`report.build_record`): one character per chip,
  `'o'` = alive; EVERY other character becomes a dead position.
  The per-chip characters do NOT survive into the record — only
  counts + dead positions do.
- `CgminerClient.pools()` EXISTS (cgminer.py, the `pools`
  command) and returns `POOLS[]` — `{POOL, URL, Status, User,
  Accepted, Rejected, …}`. The scan never calls it.
- Fans: STATS `fanN` keys → the record's `fans_rpm` (complete).
  Fan MODE: bmminer STATS carries no mode key — **no source**.
- The acs alphabet beyond `'o'`: BeeSky's evidence shows `'x'`
  for dead chips (tests/mock_miner.py `_acs`); the semantics of
  any other character are NOT documented in our materials.
  There is therefore **no honest STABLE/SLOW/CRITICAL split**
  for this family — only ok / not-ok per chip (DATA-GAP, §5).

### 2.3 Bitmain stock web CGI (`beesky/core/bitmain.py`)

- The status CGIs return cgminer-shaped SUMMARY/STATS
  (`_to_cgminer_shape`) — acs strings and `fanN` ride along, so
  boards + fan speeds work exactly like the cgminer family.
- Pools: the adapter's known CGI set (status + system info) has
  **no pool list**. Real stock bmminer also answers the cgminer
  RPC on :4028 (BeeSky's own probe order tries it FIRST —
  discover.py module doc), so inspect tries the RPC `pools`
  command for stock devices too and reports the section
  unsupported when the RPC does not answer.
- Fan mode: no source (same as cgminer).

### 2.4 The scan record itself (all families)

`chains[] = {index, chips_total, chips_alive, dead_positions,
temp_c}` (temp_c = CHIP temp; a separate PCB/board temp is NOT
carried — dashd's `pcb_temp` is dropped), `fans_rpm[]`,
`max_temp_c`, `power_w`, `rate_value`/`rate_unit`, `problems`.
Records carry **no MAC** (models.dart parses one defensively;
nothing emits it) and **no pools** (the v0.25 grid's Pools
columns are wired to an optional wire `pools` list that no
adapter fills). Inspect therefore fetches pools/fans/boards
on demand per device instead of widening the scan record.

## 3. The port — `beesky inspect --json <ip>`

One-device deep fetch, read-only, reusing the scan's own
machinery: `discover.probe_host` claims the device (family
detection + the v0.23 creds-file / v0.24 group credential
resolution — `--creds-file`, `--group`, `--groups-file`,
`--user/--password`, `--api-key`, `--token` exactly like scan)
and the winning credential set's token/key/username ride the
candidate into the section fetches, exactly like `_fetch_record`.

Output: ONE JSON document on stdout:

    {"ip", "source", "model", "cred_label",
     "boards": <section>, "pools": <section>, "fans": <section>}

A section is `{"supported": true, …}` with its data, or
`{"supported": false, "reason": "…"}` — an explicit marker,
never an empty success. A device no adapter claims yields
`{"ip", "source": null, "error": "…"}` with exit 0 (the app
renders the state); a malformed target (not one IPv4 address)
exits 2 before any I/O, like scan's validation contract.

Per family:

| Section | vnish | cgminer | stock |
|---|---|---|---|
| boards | summary `chip_statuses` counts → stable/slow/critical + totals; `/boards` per-chip list (pos, hr, grade, temp) + dead positions; chip AND pcb temps | STATS acs: per chain `{acs, chips_total, chips_ok, dead_positions, other_chars{char: n}, temp_c}` — counts only, NO grade buckets (DATA-GAP) | same acs shape, from the status CGI payload the probe already fetched |
| pools | summary `pools` (PoolStats subset: id/url/user/status/accepted/rejected/stale/ping) | RPC `pools` → POOLS subset (id/url/user/status/accepted/rejected) | RPC `pools` attempted; failure → unsupported with the reason (no CGI source) |
| fans | cooling: fans `{id, rpm, status, max_rpm}` + `mode` (+ `param`) + `fan_duty`; mode parsed from BOTH the api-doc object shape and a plain-string shape (the test mock serves a string) | STATS fan speeds; `mode: null` — speeds only, stated | status-CGI fan speeds; `mode: null` |

## 4. The Flutter port — tabs in the side panel

**Layout divergence (named, pre-approved):** HashCore's detail
is a modal dialog; BeeSky keeps the v0.22 right-side panel.
The TABS and their content are the parity target, not the
container. Tab order mirrors the dialog: Số liệu (Metrics) ·
Biểu đồ (Charts) · Board (Boards) · Pools · Quạt (Fans) ·
Ghi chú (Note). (The Metrics tab is NOT named "Tổng quan":
that label already names the grid's Overview density on the
same screen — one label, one meaning.) **Hotel Fee: NOT
built** — BeeSky has no
hotel-fee concept anywhere (no data, no settings); a tab would
be pure theatre. Named not-applicable, not a gap to fill later
unless the product grows the concept.

- **Số liệu** — the v0.22 panel content VERBATIM (metrics,
  issues, per-board lines): the panel's existing contract —
  including its widget tests — is a shipped behaviour, so the
  board summary lines stay here AND the Board tab carries the
  deep view (a deliberate, named duplication).
- **Biểu đồ** — HashCore charts hashrate + temperature.
  BeeSky's samples are LOCAL: every completed scan appends one
  sample per device `{ts, rate_value, rate_unit, max_temp_c,
  power_w}` to `beesky-history.json` (keyed by MAC when a
  record ever carries one, else IP), capped at 300
  samples/device. Charts are drawn per device ONLY — a
  device's series is never aggregated with another unit's
  (the v0.20 mixed-unit lesson), the rate chart is labelled
  with the device's own unit, and samples lacking a metric
  are skipped for that metric's line. Hand-drawn
  CustomPainter (the app keeps zero third-party deps, where
  HashCore uses fl_chart — a library divergence, not a
  behaviour one). Empty state says plainly that charts fill
  in as scans accumulate. DIVERGENCE: HashCore's chart
  history mechanics are UNKNOWN (§1), so BeeSky's
  scan-sampled local history is its own named design, not a
  claimed copy.
- **Board** — per-board rows from the scan record immediately
  (index, chips ok/total, chip temp, dead positions); when
  the inspect fetch for the device has landed, vnish boards
  gain the STABLE/SLOW/CRITICAL split (labelled Ổn định /
  Chậm / Nghiêm trọng) + PCB temp + per-chip grades, and
  cgminer/stock boards gain the acs character breakdown.
  The split is shown ONLY where the data exists (§5).
- **Pools** — the record's `pools` when a future core fills
  them; otherwise the inspect fetch on first open, with a
  loading state and the core's unsupported reason shown
  verbatim per family. Rows mirror `device_info_pools_info`:
  "Pool {n} URL" / "Pool {n} worker" (+ status when known).
- **Quạt** — fan speeds from the record immediately; the
  inspect fetch adds mode (+ duty) where the firmware
  reports one (vnish). No mode → the tab says the firmware
  does not report one; nothing is invented.
- **Ghi chú** — HashCore's Note field + Save button, ported
  as a tab (the panel's tab strip is the container BeeSky
  has): a per-device note keyed MAC-else-IP, persisted to
  `beesky-notes.json` beside the executable (the stores'
  usual primary/%APPDATA% strategy), placeholder "Ghi chú
  cho máy này" (HashCore: "Device note"), explicit
  "Lưu ghi chú" save (HashCore: "Save note").

**Grid Note column: NOT wired.** v0.25's mapping listed
HashCore's `note` column as not-offered, and the grid's cell
text is a pure function of the record (`GridColumnDef.textOf`)
— notes live outside records, in the app store, so wiring
the column means changing the grid's data contract, not a
trivial hookup. Left for a later pass, named here and in
RESULTS.md.

**Mock mode:** MockBridge gains `inspect` fixtures per sample
device (vnish with the grade split + fan mode, two cgminer
with acs boards + pools, the unreachable unit as an error
document) and the app seeds a few history samples for the
sample fleet so every tab renders in tests and demos.

## 5. DATA-GAPs (named, never faked)

1. **cgminer/stock chip grade split** — the acs string's
   non-`'o'` characters have no documented per-grade
   semantics in BeeSky's evidence; boards show ok/total +
   dead positions + the raw character counts. The
   STABLE/SLOW/CRITICAL buckets ship for vnish ONLY, where
   the firmware's grades define them.
2. **Fan mode for cgminer/stock** — no source key exists;
   the section reports speeds with `mode: null`.
3. **Stock pools when the RPC is silent** — no CGI source;
   the section is unsupported with the reason, not empty.
4. **PCB/board temperature in the scan record** — carried
   only by inspect (vnish); record chains keep chip temp.
5. **MAC keying** — history/notes key by MAC "when present";
   no adapter emits one today, so IP is the working key.
