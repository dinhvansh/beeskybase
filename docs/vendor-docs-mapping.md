# Vendor docs mapping — v0.33.0 (docs-based vendor adapters)

Method: the spec source for each family is that vendor's own
published API documentation, found via web research (official
vendor docs and first-party API references first; community
wikis / GitHub API clients only as corroboration, graded lower).
Evidence grades: **OFFICIAL-DOC** (the vendor's own published
doc), **CORROBORATED** (first-party code/package or independent
implementations agreeing with the official doc), **INSUFFICIENT**
(no usable public spec found). A family whose spec stays
INSUFFICIENT ships as a named gap — no invented dialects.

This mapping closes the v0.30 gaps where the docs allowed it
and names the rest precisely. The v0.30 mapping
(`docs/vendor-coverage-mapping.md`) stays the record for the
HashCore-dissection side (whatsminer read dialect §1, Avalon §2,
cred families §6); this document is the docs-first side.

## Verdict table (v0.33.0)

| Family | Verdict | Evidence | What ships |
|---|---|---|---|
| Whatsminer actions (G-W1) | **CLOSED** — token flow implemented + worked-example verified | OFFICIAL-DOC (MicroBT manuals V2.0.5/V2.2.2 + V1.3.11) | reboot / restart_mining / pause / resume / find_miner / switch_pool via the token flow (§1) |
| LuxOS | **IMPLEMENTED** — detection + reads + reboot + curtail | OFFICIAL-DOC (docs.luxor.tech) + CORROBORATED (Luxor `luxos` PyPI package) | `luxos` source: version-fingerprint detection, cgminer-compatible reads, `rebootdevice`, `curtail` sleep/wakeup (§2) |
| Braiins OS | **GAP G-B1** — gRPC spec documented, no stdlib path; socket equivalent's detection fingerprint unverified | OFFICIAL-DOC (gRPC PAPI) + CORROBORATED (bosminer 4028 API) | none — reason + future path in §3 |
| IceRiver | **GAP G-I1** — no public API spec found | INSUFFICIENT | none — §4 |
| Jasminer / SunLune | **GAP G-J1** — no public API spec found | INSUFFICIENT | none — §5 |

Coverage scoreboard after v0.33.0: **7 real read adapters** of
HashCore's 15–16 (stock, vnish, whatsminer, avalon, luxos +
cgminer-generic counts as the stock-cgminer family; the v0.30
count of 6 gains LuxOS). Whatsminer is now the first family
with token-authenticated writes outside VNish.

---

## §1 Whatsminer — privileged API (G-W1 CLOSED)

### §1.1 Sources

* **OFFICIAL-DOC** — MicroBT "Whatsminer Privilege API"
  V2.0.5 (2024-02-18), hosted on MicroBT's own S3 bucket
  (`aws-microbt-com-bucket.s3.us-west-2.amazonaws.com`,
  file `1708246996819WhatsminerAPI2.0.5_20240218.pdf`).
* **OFFICIAL-DOC** — same manual V2.2.2 (20250724),
  `cdn.miners.tools/downloads/whatsminer/docs/WhatsMiner_API_User_Manual_20250821.pdf`
  (miners.tools is the community mirror of MicroBT's own
  downloads; the V2.0.5 copy above is the MicroBT-hosted
  original — the two agree on the token flow, §1.3).
* **OFFICIAL-DOC** — V1.3.11 (`WhatsminerAPIV1.3.11.pdf`,
  same mirror) for the plaintext writable envelope: its §2
  writable commands carry the `"token"` field in plain JSON,
  the form BeeSky implements (§1.5). V1.3.8 is the same
  document generation.
* Local copies of the extracted manual text live in the
  research notes only (not in the repo): the mapping quotes
  the sections that matter.

### §1.2 Transport (V2.0.5 §2 Protocol)

* TCP **4028**, one JSON object per connection, reply ends
  with NUL. Idle timeout 10 s after connect.
* Max **16 IP clients**; one IP may hold **32 tokens**;
  a token's keepalive is **30 minutes**.
* Reply envelope (all commands):
  `{"STATUS": "string", "When": <int>, "Code": <int>,
  "Msg": "string"|object, "Description": "string"}` — in
  practice the `STATUS` value is a one-entry list in the
  firmware's JSON (see the v0.30 read dialect); the codes
  below are the manual's own table:
  `14` invalid API command/data, `23` invalid JSON,
  `45` permission denied, `131` command OK,
  `132` command error, `134` get token message OK,
  `135` check token error, `136` token over max times,
  `137` base64 decode error.

### §1.3 Token computation — the part v0.30 was missing

Flow (V2.0.5 §2.2 / §3, V2.2.2 §3):

```
client -> miner: {"cmd": "get_token"}
miner  -> client: {"time": "5626", "salt": "BQ5hoXV9",
                   "newsalt": "jbzkfQls"}        (manual's example)
```

```
key  = md5(salt + admin_password)          (manual's text formula)
sign = md5(newsalt + key + time)           (time = its LAST FOUR chars)
```

**The text formula is NOT what the manual's own reference
code does.** The reference implementation printed in both
manuals is:

```
key  = `openssl passwd -1 -salt $salt "${admin_password}" | cut -f 4 -d '$'`
sign = `openssl passwd -1 -salt $newsalt "${key}${time: -4}" | cut -f 4 -d '$'`
```

`openssl passwd -1` is **MD5-crypt** (`$1$` — Poul-Henning
Kamp's algorithm), not plain MD5: the value used is the
checksum field (field 4) of the `$1$salt$checksum` string.
The reference implementation governs over the prose formula
— every field tool that talks to Whatsminers uses md5crypt,
and the worked example below only reproduces under md5crypt.
BeeSky implements pure-Python MD5-crypt in
`beesky/core/md5crypt.py` (stdlib `hashlib.md5` only; the
`crypt` module is absent on Windows and deprecated on
CPython 3.11+, so no stdlib shortcut exists).

**Worked example (the manual's own inputs, gold standard).**
Inputs: `time="5626"`, `salt="BQ5hoXV9"`,
`newsalt="jbzkfQls"`, password `"admin"` (the manual's
default: "The default user name and password are admin").
Expected values, generated with the manual's own reference
implementation (OpenSSL 3.0.13, `openssl passwd -1`):

```
key  = RxmaDUO33TS7O26yeMHZ81
sign = w.BNbkCV6n1aNWgiBWLzT/
```

i.e. `$1$BQ5hoXV9$RxmaDUO33TS7O26yeMHZ81` and
`$1$jbzkfQls$w.BNbkCV6n1aNWgiBWLzT/`. The mock test
(`tests/mock_vendors2_test.py`) reproduces both values
exactly from the pure-Python implementation — if either
value ever differs, the token flow is wrong, not the test.
The mock Whatsminer server uses these exact example
salts, so the end-to-end action test verifies the client's
token against the worked example, not against itself.

### §1.4 Ciphertext mode — DOCUMENTED, NOT implemented

V2.0.5 §2.1 / V2.2.2 §2.1: the readable API supports
plaintext **and** ciphertext; the writable API supports
**only ciphertext** on V2 firmware. Ciphertext construction:

```
api_cmd  = token,$sign|api_str
enc_str  = aes256(api_cmd, $aeskey)        # AES-256, ECB mode
tran_str = base64(enc_str)
aeskey   = sha256($key)
wire     = {"enc": 1, "data": tran_str}
```

Why BeeSky does NOT implement this in v0.33.0: the manuals
give **no complete worked ciphertext example** — no full
`enc` payload for known inputs — so three choices are
unverifiable from the text alone: the byte form of `aeskey`
(raw sha256 digest vs its hex string), the padding scheme
for ECB, and what the `token` in the `token,$sign|api_str`
prefix is (the `sign` just computed, or a separate token
value). Implementing any of the three by guess would be an
invented dialect. The plaintext token-command envelope
(§1.5) IS fully specified and is what the V1 manuals and
every field implementation use; it is what ships. A V2
firmware that enforces ciphertext-only will refuse a
plaintext write with Code 45 — the executor surfaces that
refusal verbatim, and the ciphertext mode is the named
follow-up (it needs one captured `enc` payload from a real
V2 device, or a complete worked example from MicroBT).

### §1.5 Writable commands implemented (plaintext token envelope)

Envelope: `{"token": "<sign>", "cmd": "<name>", ...}` —
the command JSON bodies are the manuals' own §3 shapes,
with `"token"` carrying the §1.3 `sign`.

| BeeSky action | Whatsminer cmd (manual §) | Body | Miner reply |
|---|---|---|---|
| `reboot` | `reboot` (§3.8 Reboot system — restarts the control board) | `{"token","cmd":"reboot"}` | Code 131 |
| `restart_mining` | `restart_btminer` (§3.2 — restarts btminer only, not the board) | `{"token","cmd":"restart_btminer"}` | Code 131 |
| `pause_mining` | `power_off` (§3.3 — stops mining, powers off hashboards) | `{"token","cmd":"power_off"}` | Code 131 |
| `resume_mining` | `power_on` (§3.4 — starts mining, powers on hashboards) | `{"token","cmd":"power_on"}` | Code 131 |
| `find_miner` | `set_led` (§3.5 — `param:"auto"` returns LED to auto flashing) | `{"token","cmd":"set_led","param":"auto"}` | Code 131 |
| `switch_pool` | `update_pools` (§3.1 — updates pools, switches immediately) | `{"token","cmd":"update_pools","pool1","worker1","passwd1","pool2",...}` | Code 131 |

Notes:

* `switch_pool` with only a `pool_id` (activate an
  already-configured slot) has NO Whatsminer equivalent in
  the manual — `update_pools` always rewrites the pool
  lines — so the executor requires url+user (+password,
  defaulting to the slot's existing password is impossible
  to know; the payload password defaults to `""` and the
  message says so). Pool slot mapping: BeeSky `pool_id`
  selects which of pool1/2/3 the new values land in; the
  other two slots are re-sent unchanged — the mock verifies
  the request shape, the hardware does not echo them back.
  **Hardware-unconfirmed:** the real miner's behaviour
  when a slot is re-sent with empty strings is unknown;
  the first real run should use a full three-pool payload.
* `set_led` manual setting (`color` red/green + period /
  duration / start) exists in §3.5 but BeeSky only sends
  the `auto` form (the find-miner semantic); the manual
  form is noted, not wired.
* Password source: the winning `whatsminer`-tagged
  credential set's password; with no set, the manual's
  factory default `"admin"` (V2.0.5 §3: "The default user
  name and password are admin"). The executor's message
  names the default when it uses it — a fleet that changed
  the admin password must save a whatsminer set, exactly
  like the VNish API-key rule.
* Reads are unchanged (v0.30 dialect) and still NEVER
  send `get_token`: only an explicit action mints a token.

### §1.6 Documented, NOT implemented (Whatsminer)

* Ciphertext envelope (§1.4) — needs a worked example or
  a real V2 capture.
* `set_power_pct` (§3.21 fast mode) / `set_power_pct_v2`
  (§3.22 normal mode) — throttle exists in the manual but
  the parameter shapes were not extracted for this build;
  the `throttle` action stays a gap for whatsminer.
* Firmware upgrade (§3.7, `"update_firmware"` text flow),
  restore-to-factory (§3.9), password change (§3.10),
  network config (§3.11), log download (§3.12), target
  frequency (§3.13), fast boot (§3.14), temp offset
  (§3.23) — documented, out of scope for the ops surface.
* **API v3 on TCP 4433** (2024+ firmware, LAN only) —
  reported by third-party product pages (Kratos); NOT in
  the V2.0.5/V2.2.2 manuals BeeSky worked from, so not
  implemented and not claimed.
* Power (W) remains unread (G-W4): no power field is in
  the evidenced read contract.

---

## §2 LuxOS (Luxor) — IMPLEMENTED

### §2.1 Sources

* **OFFICIAL-DOC** — Luxor Firmware API docs,
  `docs.luxor.tech/firmware/api/`:
  Getting Started (`/firmware/api/intro`), Sessions
  (`/firmware/api/sessions`), and the per-command pages
  `atmset`, `curtail`, `events`, `profileset`
  (all under `/firmware/api/luxminer/`).
* **CORROBORATED** — Luxor's own `luxos` PyPI package
  (LuxOS Tools Repository): `rexec(host, port=4028,
  cmd=...)`; its CLI runs `--cmd version` (reply
  `LUXminer 2024.5.1.155432-f2badc0f`) and
  `--cmd rebootdevice`. The package confirms the command
  names the docs pages imply but do not all spell out.
* **CORROBORATED** — independent fleet tools agree on
  the wire: "TCP 4028 with sessions" (Kratos miner table),
  "LuxOS implements a CGMiner-compatible TCP API on port
  4028. Commands are JSON-formatted" (ThermoHash protocol
  doc).

### §2.2 Transport (Getting Started page)

> "For easier integration with existing tools, LUXminer
> supports a rich API layer… The API follows the same
> pattern as the CGMiner API, that is, a raw TCP (**not
> HTTP**) connection which accepts commands in text or
> json format, and outputs the result accordingly, closing
> the connection immediately afterwards."

* TCP **4028**; request `{"command": "<name>"}` with an
  optional `"parameter"` string; reply is the cgminer
  envelope (`STATUS` list + command section + `"id": 1`),
  NUL-terminated. "When working with LUXminer, always
  favor the TCP API."
* An HTTP layer also exists (port **8080**, single RPC
  endpoint `POST /api`) — a thin wrapper over the TCP API;
  BeeSky does not use it (the docs themselves say to
  favor TCP).
* `luxminer.toml`: `[app.api.tcp] enabled = true,
  port = 4028` by default.

### §2.3 Sessions (Sessions page — read this before writing)

> "LUXminer sessions are **not a security feature**! They
> are just a easy way for multiple processes to
> 'exclusively' coordinate changes of the miner
> configuration."

* `logon` (no parameter, no password) → `SESSION:
  [{"SessionID": "yJN2nlj1"}]`, STATUS Code **316**
  "Session created". The SessionID is passed as the FIRST
  parameter of every write command
  (`"parameter": "<session_id>,..."`).
* Sessions **expire after one minute**, refreshed on each
  use; **max one session at a time** — `logon` must be
  checked, and a failed logon means wait and retry, never
  force. `logoff` (Code 317) drops it cleanly; `kill`
  (Code 318) force-kills someone else's session and logs
  a warning — BeeSky NEVER sends `kill`.
* **Reads need no session.** Only commands that write or
  change configuration require one.

### §2.4 Detection

`version` → `STATUS[0].Description` starts with
`"LUXminer"` (Luxor's own CLI prints exactly
`LUXminer 2024.5.1.155432-f2badc0f` as the version reply).
Positive-only: stock cgminer answers `version` with a
`cgminer …` / `bmminer …` Description, VNish does not
answer the 4028 cgminer envelope at all, and Whatsminer
answers it with a STATUS-E refusal — so the prefix cannot
mis-claim any family BeeSky already detects. The probe
refines a cgminer claim to `luxos` exactly like the v0.30
Avalon refinement (one extra `version` call, cached).

### §2.5 Reads

cgminer-compatible commands on the same envelope:
`summary`, `stats`, `devs`, `pools` — the fields are the
cgminer vocabulary BeeSky already parses
(`GHS 5s` / `GHS av`, `Elapsed`, `chain_acs*`,
`temp*`, `fan*`). Per-board temperatures come from STATS
via the shared `_chain_temp` rule; chip counts from
`chain_acs*` via the shared rule (an `'o'` is an alive
chip — the same rule as stock, since LUXminer is a
cgminer-lineage miner; **hardware-unconfirmed** whether
LuxOS emits `chain_acs` at all — if a real LuxOS STATS
carries no acs keys the record degrades to temps-only,
exactly like Avalon, and says so). Pools come from the
`pools` command (v0.28 enrichment shape). Record rate
uses the shared `_native_rate` (LuxOS runs on Antminers:
SHA-256, GHS → TH/s).

### §2.6 Actions implemented

| BeeSky action | LuxOS command | Auth | Reply |
|---|---|---|---|
| `reboot` | `rebootdevice` (Luxor's own CLI: `--cmd rebootdevice`) | none documented — sent parameter-less, per the CLI's usage | STATUS S |
| `pause_mining` | `curtail` `sleep` (§curtail page) | session: `logon` → `curtail` with `"<session>,sleep"` → `logoff` | `CURTAIL: [{"Action": "sleep mode"}]`, Code 335 "Curtailment command sent" |
| `resume_mining` | `curtail` `wakeup` (§curtail page) | session, same flow, `"<session>,wakeup"` | `CURTAIL: [{"Action": "wake up", "FrequencyStep": 5, "VoltageStep": 0.05}]`, Code 335 |

Notes:

* `rebootdevice` session requirement is **UNKNOWN** in
  the docs read: the Sessions page says sessions are
  required for commands that *write/change configuration*,
  and Luxor's own CLI example runs it as a bare
  `--cmd rebootdevice`. BeeSky sends it parameter-less;
  a real miner that demands a session will refuse with a
  STATUS-E the executor surfaces verbatim — the follow-up
  then is logon-first, not a guess now.
* `curtail` wakeup accepts `voltage_step` /
  `frequency_step` / `mode=safe|unsafe` — BeeSky sends the
  safe default form only (`wakeup`, no steps): `unsafe`
  ramps "as fast as possible" and the docs warn it
  stresses chips ("Beware of device stress and potential
  damage"), so it is never sent.
* A `sleep` rig can only be woken by `wakeup` — the
  curtailment state **persists across a reboot** (docs).
  BeeSky's `resume_mining` is therefore the only way back
  from a LuxOS pause, and the pause message says so.
* `profileset` (profile by name / hashrate / power /
  relative position), `atmset`, `powertargetset`,
  `frequencyset` / `voltageset` are documented write
  commands BeeSky does not wire in v0.33.0 — they are
  tuning, not the ops surface (throttle/set_preset stay
  VNish-only).

---

## §3 Braiins OS — GAP G-B1 (spec documented, no stdlib path)

### §3.1 The official surface: gRPC PAPI (OFFICIAL-DOC)

* **Source:** Braiins OS+ Public API — protocol buffers
  at `github.com/braiins/bos-plus-api`; README + Braiins
  Academy guides ("Using gRPCurl with BOS API", "Using
  Postman…"). Introduced BOS 23.03, **stable 1.0.0 since
  BOS 24.03** (API 1.7.0 on BOS 25.07).
* **Transport:** gRPC over HTTP/2, **plaintext**, port
  **50051**, with **gRPC Server Reflection** (no compiled
  protos needed client-side). `grpcurl -plaintext
  <miner>:50051 list` returns:
  `braiins.bos.ApiVersionService`,
  `braiins.bos.v1.{ActionsService, AuthenticationService,
  ConfigurationService, CoolingService, LicenseService,
  MinerService, NetworkService, PerformanceService,
  PoolService}`.
* **Auth:** `AuthenticationService/Login` returns a token
  (a session id, **3600 s** expiry); `ApiVersionService`
  is unauthenticated. Services cover reads
  (`MinerService/GetMinerDetails|GetMinerStats`,
  streaming `GetMinerStatus`) and writes
  (`ActionsService` pause/resume/restart,
  `PerformanceService/SetPowerTarget`, `PoolService`).
* **Why not implemented:** Python's standard library has
  no HTTP/2 and no protobuf. A hand-rolled HTTP/2 +
  protobuf client is a multi-thousand-line dependency in
  disguise, unverifiable without hardware, and the wrong
  place to spend the sprint. The correct path is a small
  sidecar (bundled `grpcurl`, or a Go/Rust helper) driving
  the documented protos — the mapping above is the spec
  that sidecar needs, and it is complete enough to build
  from. **No stdlib code was written for this surface.**

### §3.2 The socket equivalent: bosminer cgminer API (CORROBORATED)

* **Source:** Braiins' own open-source bosminer —
  `open/bosminer/bosminer/src/api.rs`,
  `open/bosminer/bosminer/src/api/cgminer.rs`,
  `open/protocols/cgminer-api/` (repo `braiins/braiins`);
  Braiins Academy Troubleshooting ("Braiins OS metrics
  are exposed on port 8081 and CGMiner API uses 4028");
  Braiins Academy FAQ, Farm Operators:
  `echo '{"command":"pause"}' | nc IP 4028`.
* TCP **4028**, JSON `{"command": ...}` (+ optional
  `"parameter"`), cgminer envelope replies. Commands:
  `pools`, `devs`, `summary`, `config`, `devdetails`,
  `stats`, `coin`, `asccount`, `asc`, `version` (STATUS
  codes: Summary 11, Version 22, Stats 70, …).
* **Why still a gap:** the one datum detection needs —
  the exact `version` reply string (what `STATUS[0].
  Description` / the VERSION section actually says on a
  real BOS machine) — could not be recovered from any
  public source BeeSky could reach. Without it, any
  fingerprint is a guess that could mis-claim a stock
  cgminer miner (which answers the same envelope on the
  same port). Closing G-B1 needs exactly one of: a
  `version` reply captured from a real Braiins OS machine,
  or the source line in `cgminer.rs` that builds the
  version Description.
* **REST /api/v1 (BOS ≥ 25.07)** is claimed by one
  third-party product page (Kratos) and by nothing
  official BeeSky found — graded CORROBORATED-LOW, not
  implemented, not relied on.

### §3.3 What stays

`braiins` remains a cred-family tag only (v0.30 §6).
No probe, no adapter, no mock — a mock would be a
fabricated dialect. The day the version string is known,
the adapter is mechanical: CgminerClient + a
`version`-prefix refinement, exactly the LuxOS shape.

---

## §4 IceRiver — GAP G-I1 (INSUFFICIENT)

* Searched: official IceRiver docs/site, manuals.plus
  user manuals (KS0, KS0 Pro, AL3, AE2), GitHub API
  clients, first-party packages. Found only **user
  manuals**: web UI login `admin` / `12345678`, pool
  configuration through the web UI, no API endpoint
  documented anywhere public.
* Closed fleet tools (Awesome Miner, Braiins Manager)
  list IceRiver as supported, but through closed
  implementations with no public contract to port from.
* Closing needs an official or strongly corroborated HTTP
  API spec (endpoint list + auth + field semantics), or a
  real device to dissect the web UI's own calls.
  `iceriver` stays a cred-family tag only.

---

## §5 Jasminer / SunLune — GAP G-J1 (INSUFFICIENT)

* Searched: official Jasminer docs, the X4 user manual
  (tophash.ua-hosted PDF), GitHub API clients. Found
  only the user manual — no API endpoint, no command
  list, no auth scheme in any public source.
* Same closing condition as IceRiver: a published spec,
  or a real device. `jasminer` stays a cred-family tag
  only.

---

## §6 Regression gates (v0.33.0)

* Non-collision, re-run every build: Whatsminer dialect
  vs cgminer envelope (both directions), LuxOS `version`
  prefix vs stock `cgminer …` / `bmminer …` Descriptions,
  Avalon refinement vs plain cgminer, dashd/stock
  unchanged. A LuxOS mock answering `version` with a
  stock-style Description must NOT be claimed as luxos.
* Reads never mint tokens/sessions: the Whatsminer mock
  log must show no `get_token` from any read path; the
  LuxOS mock log must show no `logon` from any read path.
* Worked-example gate: `md5crypt("admin", "BQ5hoXV9")`
  checksum is `RxmaDUO33TS7O26yeMHZ81` and
  `md5crypt("RxmaDUO33TS7O26yeMHZ81" + "5626", "jbzkfQls")`
  checksum is `w.BNbkCV6n1aNWgiBWLzT/` — the manual's own
  example, reproduced by the pure-Python implementation.
