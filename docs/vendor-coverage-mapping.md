# Vendor coverage — dissection & port mapping (v0.30.0)

How HashCore Toolkit 1.7.5 talks to each miner vendor, what of it is
*evidenced* in the shipped build, and what BeeSky ports in v0.30.0.
Written BEFORE the port, per the dissect-before-porting rule; the
implementation follows it section by section, and
`tests/RESULTS.md` (v0.30.0) grades the result against this map.

Evidence grades:

- **VERIFIED** — the literal string / key / class name was read out
  of the shipped build this pass (AOT string pools
  `toolkit-x64/strings-libapp.txt` + `strings-toolkit_cli.txt`,
  `package-paths.txt`, `assets/translations/en.json`).
- **INFERRED** — strongly implied by verified structure (DTO names,
  sibling paths, session class shape) but not itself a literal.
- **UNKNOWN** — not recoverable from the materials. Never guessed:
  an UNKNOWN contract ships as a named gap, not an invention.

Source materials: `~/workspace/asic-os-s19pro/research/hashcore/`
(`toolkit-x64/` = the extracted Linux build 1.7.5, `MAP.md`,
`UI-ANALYSIS.md` §§2–3).

---

## 0. The vendor universe (VERIFIED)

`enum.firmware_vendor_enum` in en.json — HashCore keys its unlock
methods, sessions and repositories by these values:

| HashCore key | Label | BeeSky source token | BeeSky cred key |
|---|---|---|---|
| unknown | CG Miner | `cgminer` | — (generic) |
| bitmain | Bitmain | `stock` | `stock` |
| hashcore / oldVnish | Hashcore / Old Vnish | `vnish` (dashd) | `vnish` |
| microBt | MicroBT | **`whatsminer`** (new) | **`whatsminer`** (new) |
| canaan | Canaan | **`avalon`** (new) | **`avalon`** (new) |
| iceRiver | IceRiver | — gap | **`iceriver`** (new, tag-only) |
| sunLune | SunLune (Jasminer) | — gap | **`jasminer`** (new, tag-only) |
| braiins | Braiins | — gap | **`braiins`** (new, tag-only) |
| luxor | Luxor | — gap | **`luxos`** (new, tag-only) |
| auradine, epic, pitBit, bitdeer, mock | … | — out of scope | — |

Architecture (VERIFIED, `package-paths.txt`): one session class per
vendor (`device_api/api_session/device_sessions/*_api_session.dart`),
one API surface per vendor (`device_api/device_apis/*_device_api.dart`),
one repository per vendor, and DTOs **code-generated from each
vendor's own API spec** (`dto/miner/<vendor>/…*.g.dart`). BeeSky's
shape is the same idea at its own scale: one adapter module per
family in `beesky/core/`, one normalisation point (`report.py`).

Discovery (VERIFIED): the probe walks ports in the order given by
the pool literal `"Port 80 not available. Checking port 4028"` —
HTTP :80 first, then the socket API on TCP 4028. (BeeSky's chain
tries 4028 first — a pre-existing BeeSky design decision, kept; this
port is about the per-vendor contracts, not probe order.)

---

## 1. MicroBT Whatsminer — the deep port

### 1.1 Two transports (VERIFIED)

- **API v2 socket**: `MicroBtApiV2Session`, `MicroBtApiV2DeviceApi`,
  `MicroBtRequestAdapter`, `MicroBtSocketDiscoverResult`. JSON
  command envelopes over a TCP socket; the one verbatim request
  literal in the build is `{"cmd": "get_token"}` — privileged
  access is a **token session** minted via `get_token`.
- **HTTP**: `MicroBtHttpApiSession` (with `parseFromHeaders` —
  the session is derived from login-response headers),
  `MicroBtHttpDeviceApi`, `MicroBtHttpRepository`.

### 1.2 Socket read model (VERIFIED structure)

DTO family (all `*SocketDto`, code-generated):

- `WhatsMinerSummaryItemSocketDto` — the summary payload is a
  **list of items** (cgminer SUMMARY shape).
- `WhatsMinerDevSocketDto` / `WhatsMinerDevsSocketDto` /
  `WhatsMinerDevsStatusSocketDto` — per-board reads exist.
- `WhatsMinerPoolsInfoSocketDto` / `WhatsMinerPoolInfoSocketDto` /
  `WhatsMinerPoolStatusSocketDto` — pool reads exist.
- `WhatsMinerInfoSocketDto` + `WhatsMinerInfoMsgSocketDto`,
  `WhatsMinerVersionSocketDto` + `WhatsMinerVersionMsgSocketDto`
  — info/version replies wrap their payload in a **`Msg`**
  envelope.
- `WhatsMinerLanInfo` — a LAN/info DTO rides discovery
  (`MicroBtSocketDiscoverResult`).

Command names for the reads (`summary` / `devs` / `pools` /
`version` sent as `{"cmd": …}` values): **INFERRED** from the DTO
names — only `get_token` is a verbatim cmd literal. The bare pool
strings `status`, `summary`, `version`, `restart` exist but are
generic. `restart_btminer` / `restartBtMiner` are VERIFIED method
names — the restart exists, and it rides the token session.

Summary vocabulary (VERIFIED presence in the pool): the
cgminer-family keys `MHS 5s`, `MHS 1m`, `MHS 5m`, `MHS 15m`,
`MHS av`, `GHS 5s`, `GHS av`, `Elapsed`, `Accepted`, `Rejected`,
`Hardware Errors`, `Device Hardware%`, `Stratum URL` — plus the
Whatsminer-distinctive **`Fan Speed In`** and **`Fan Speed Out`**
(the Antminer cgminer SUMMARY has no fan fields at all; its fans
live in STATS as `fan1..N`). The fan pair is therefore the
detection fingerprint: a socket that answers the `{"cmd": …}`
dialect with a summary item carrying `Fan Speed In/Out` is a
Whatsminer, and nothing else in the dissected fleet matches that
combination. A generic cgminer device answers the foreign dialect
with a STATUS-E error envelope (BeeSky's own mock proves the
negative), so trying the dialect first cannot mis-claim a cgminer
miner, and a Whatsminer never reaches the dashd/stock steps.

### 1.3 Token scheme (UNKNOWN → actions gap)

How the password and the `get_token` reply combine into the token
sent with privileged commands: **UNKNOWN** from the materials (no
attributable salt/hash construction in the pools). Per the
no-invention rule, BeeSky does **not** implement socket-side
privileged calls: `reboot` and every other write for source
`whatsminer` return the honest NOT_SUPPORTED result. The scan path
never sends `get_token` — reads are anonymous, and the mock suite
asserts the command is never issued during a scan.

### 1.4 HTTP transport (VERIFIED paths, INFERRED set)

LuCI on `/cgi-bin/luci` (VERIFIED base + `sysauth` cookie string +
`luci_username` / `luci_password` keys), admin pages (VERIFIED
literals): `/admin/status/overview`, `/admin/status/btminerstatus`,
`/admin/status/cgminerstatus` (+ `/admin/status/cgminerstatus/restart`),
`/admin/network/btminer`, `/admin/network/cgminer`,
`/admin/network/iface_status/lan`, `/admin/system/reboot/call`.
Attributing the sibling paths to MicroBT follows the two
`btminer`-named pages (btminer is MicroBT's miner stack) —
**INFERRED-STRONG** as a set.

The build's only LuCI HTML-scrape contract (VERIFIED regexes):
`cbid.pools.default.{coin_type, pool{1..3}{url,user,pw}}`,
`cbid.table.1.{elapsed, fanspeedin, fanspeedout, power, temp}`,
`cbid.table.2.temp`, `cbid.table.{4,5,6}.{mhs5s, mhsav, ths1m,
thsav}`, plus a hidden `name="token"` input (LuCI form token).
Attribution to the MicroBT HTTP session: **INFERRED** (the pool
holds exactly one LuCI stack, and §4 shows SunLune's contract is
JSON, not HTML). Residual uncertainty is recorded here rather than
hidden. **Not built in v0.30.0** — the socket read path is the
evidenced core; the LuCI read/reboot ride is a follow-up gap (G-W3)
until the attribution is confirmed against hardware.

### 1.5 BeeSky port (what ships)

- `beesky/core/whatsminer.py`: socket client for the `{"cmd": …}`
  dialect; tolerant envelope parsing (Msg list / Msg dict /
  cgminer-style sections); `fetch_record` normalising into the
  shared record via `report._finalise_record`:
  - rate: the MHS pair is the device's truth — `ghs_*` = MHS/1000,
    native rate displayed in TH/s (MHS/1e6), the same display-scale
    convention `report._native_rate` applies to GHS fields;
  - fans: `[Fan Speed In, Fan Speed Out]`;
  - chains: one entry per devs board, temp from the board's
    `Temperature` when numeric, **chip counts 0/0** — per-chip
    semantics are not in the evidenced contract, so no counts are
    emitted (the L9 rule: never invent chip data);
  - power: **not read** — the `Power` key is not attributable to
    the socket summary in the pool (it appears in LuCI/Luxor
    contexts), so `power_w` stays None;
  - pools: the pools read, normalised like the cgminer enrichment
    (verbatim URL/User/Status), failure omits the field.
- Detection in `discover.probe_host`, step 1a (before the cgminer
  envelope): dialect summary + the fan-pair fingerprint.
- Inspect: boards/pools/fans sections from the same reads.
- Cred family `whatsminer`: sets are orderable through the
  existing `ordered_creds` (the socket reads are anonymous today;
  the tag exists for parity and future token support).

Divergence from HashCore, named: HashCore reads Whatsminer over
BOTH transports; BeeSky v0.30 reads the socket only (G-W3).

---

## 2. Canaan Avalon — cgminer-family refinement

- Transport/read model (VERIFIED): `canaan_device_api.dart`,
  `CanaanApiSession`, DTOs `AvalonMinerInfoDto` +
  `AvalonCgConfigDto`, and — decisive — `CgminerCommonStatsDto.
  fromAvalonJson`: Avalon STATS are parsed **from cgminer STATS
  JSON** by a dedicated factory on the *common* cgminer DTO.
  Avalon is a cgminer-API device with its own stats flavour.
- Fingerprint (VERIFIED presence): the STATS key `MM ID0` — Avalon
  cgminer STATS entries are keyed by module (`MM ID<n>`); stock
  Antminer STATS carries no such keys (BeeSky's Antminer fixtures
  confirm the negative). A `Type` starting `Avalon` is accepted as
  the same fingerprint's second form.
- Avalon-specific STATS field semantics beyond the fingerprint:
  **UNKNOWN** (keys exist in the pool but cannot be attributed
  field-by-field). BeeSky therefore reads Avalon through the
  common cgminer builder: whatever `chain_acs` / temps / fans the
  payload carries is normalised exactly like a cgminer record;
  nothing Avalon-specific is invented. Chip counts appear only
  when the payload itself carries acs strings.
- Port: probe refinement — after a cgminer claim, one `stats`
  fetch (cached on the candidate for the fetch stage) checks the
  fingerprint; a hit reclassifies the candidate to source
  `avalon`. Fetch/inspect then ride the cgminer paths with
  source `avalon`. Actions: `reboot` rides the cgminer privileged
  `restart` RPC (the family-shared mechanism; refusal surfaces
  verbatim) — every other action keeps the cgminer family's
  honest gaps.

---

## 3. IceRiver — NAMED GAP (structure only)

VERIFIED structure: `IceRiverApiSession`, `ice_river_api.dart`,
DTOs `IceRiver{Response, Info, Boards, Board, BoardPow, Fan, Net,
Pools, Pool, SetPool, SetPoolItem}Dto`, the session scheme string
`iceRiverApi://`, and app-metrics naming (`getBoardPow`,
`fromIceRiverPowsReply`) — an HTTP API with a response envelope
and info / boards (+ per-board power) / fans / net / pools reads
and a pool-write shape.

Endpoints, payload keys, auth and the detection probe: **UNKNOWN**
— no literal in the materials is attributable to IceRiver.
Detection, read and actions are **not built** (G-I1); the cred
family key `iceriver` ships so sets can be tagged and ordered.

## 4. SunLune / Jasminer — NAMED GAP (structure only)

VERIFIED structure: `SunLuneApiSession`, `sun_lune_device_api.dart`,
and a full JSON DTO family — `SunLune{Summary, HashLine,
AvgHashLine, RejectLine, Boards, BoardItem, Pools, PoolItem,
PoolConfig, MinerConfig, Status, AsicSn, HashBoardSn}Dto`, all
FromJson: a JSON API whose summary embeds per-line sub-objects
(hash / average-hash / reject lines), with board + ASIC serial
DTOs. `_parseSunLuneValue` implies stringly-typed values parsed
client-side; `_convertMinerPoolToJasminerConfDto` implies pool
writes convert to a Jasminer config DTO.

Endpoints, keys, auth, detection: **UNKNOWN** → not built (G-S1).
Cred family key `jasminer` ships (the hardware brand; HashCore's
enum key is `sunLune`, its label "SunLune (Jasminer)").

## 5. Braiins OS + LuxOS — NAMED GAPS (detection contract unknown)

VERIFIED structure: `braiins_device_api.dart` with
`Braiins{Config, ConfigResponse, Fans, FansResponse, TunerStatus,
TunerStatusResponse}Dto`; `luxor_device_api.dart` with
`Luxor{Session, SessionResponse, Config, ConfigResponse, Power,
PowerResponse, Temp, TempsResponse, Version}Dto`; and a **shared**
`BraiinsLuxorTempDto` (+ response) — the two firmwares expose
near-identical HTTP API surfaces (config / fans-or-temps / power /
tuner / version reads), Luxor with an explicit session DTO
(session auth of some kind).

The distinguishing detection marker (version string, endpoint
paths): **UNKNOWN** from the materials — no `bosminer` literal, no
attributable API paths. Detection and read are **not built**
(G-B1, G-L1): a Braiins/LuxOS Antminer still reads through
BeeSky's existing cgminer/stock chain exactly as before, and is
deliberately **not** reclassified on a guess. Cred keys `braiins`
/ `luxos` ship for tagging parity.

---

## 6. Cred-family extension (all six keys)

`discover.CRED_TYPES` grows from `(any, stock, vnish)` to `(any,
stock, vnish, whatsminer, avalon, iceriver, jasminer, braiins,
luxos)`, and every normaliser that whitelisted the old pair
(`cli._normalise_creds`, `ops._normalise_creds`, the Flutter
`CredSet.fromJson`) accepts the full set — a set tagged with a new
family keeps its tag end-to-end (it is no longer squashed to
`any`), and `ordered_creds` tries it first for its family through
the unchanged ordering logic. The Flutter cred dialog + group
editor share `credTypeLabels`, so both dropdowns gain:
Whatsminer (MicroBT) · Avalon (Canaan) · IceRiver · Jasminer
(SunLune) · Braiins OS · LuxOS.

## 7. Non-collision contract (hard requirement)

Probe order after this port: whatsminer-dialect → cgminer
envelope (+ Avalon refinement) → dashd → stock → locked-dashd
fallback. Every pre-existing fixture must classify exactly as
before: Antminer cgminer mock → `cgminer` (its STATUS-E reply to
the foreign dialect is not a fingerprint; its STATS carries no
`MM ID`), dashd mock → `vnish`, stock mock → `stock`, L9/Z15
fixtures unchanged. The Whatsminer mock must classify
`whatsminer` and must NOT be claimable by the cgminer envelope
(it answers STATUS-E to `{"command": …}`). The regression suites
pin all of it.

## 8. Gap register (carried into RESULTS.md)

- **G-W1** Whatsminer privileged actions (reboot etc.) — token
  computation UNKNOWN (§1.3).
- **G-W2** Whatsminer per-chip data — semantics not evidenced;
  chains carry temps only, counts 0/0 (§1.5).
- **G-W3** Whatsminer HTTP/LuCI transport (read + reboot) —
  attribution INFERRED, unbuilt (§1.4).
- **G-W4** Whatsminer socket power — `Power` key unattributable
  to the socket summary (§1.5).
- **G-A1** Avalon-specific STATS semantics beyond the fingerprint
  (§2).
- **G-I1** IceRiver: detection/read/actions (§3).
- **G-S1** SunLune/Jasminer: detection/read/actions (§4).
- **G-B1 / G-L1** Braiins OS / LuxOS: detection/read (§5).
- Old-dialect Whatsminers (cgminer-envelope-only firmware) still
  classify `cgminer` — the pre-v0.30 behaviour, unchanged.
