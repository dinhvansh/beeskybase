# Vendor adapters from open-source implementations — v0.36.0

The Toolkit-app dissection route is exhausted for Braiins and IceRiver
(v0.33, docs/vendor-docs-mapping.md §3–§5): the AOT materials hold only
their enum names + cred tags, no API strings. This leg mines established
open-source miner-management libraries instead — pyasic (Upstream Data,
Apache-2.0, actively maintained, production fleet use) as the prime
source, asic-rs (256foundation) as the independent corroboration for
Braiins, and a real captured IceRiver packet (HackMD, KS0 Ultra owner)
as the worked example. Jasminer was put through the same treatment and
stays a gap (§4).

Evidence grades: OFFICIAL-DOC (the vendor's own published docs) /
OSS-IMPLEMENTATION (a named open-source library's shipped code) /
CORROBORATED (two independent sources agreeing, or one OSS
implementation + a reproducible worked example) / INSUFFICIENT.

## Verdicts

| Family | Verdict | Evidence |
|---|---|---|
| Braiins OS (BOSMiner RPC) | **IMPLEMENTED** — detection + reads + pause/resume | CORROBORATED (official Academy worked examples + pyasic + asic-rs) |
| IceRiver | **IMPLEMENTED** — detection + reads + find_miner | CORROBORATED (pyasic + real captured packet + manuals) |
| Jasminer / SunLune | **GAP G-J1** — no OSS implementation exists | INSUFFICIENT |

Coverage scoreboard after v0.36.0: **9 real read adapters** of
HashCore's 15–16 (stock, vnish, whatsminer, avalon, luxos, braiins,
iceriver + cgminer-generic counts as the stock-cgminer family).

## §1 Braiins OS — CLOSED (G-B1)

### §1.1 Sources

* **OFFICIAL-DOC — Braiins Academy, "BOSminer API"**
  (academy.braiins.com/braiins-os/papi-bosminer): the 4028 API is a
  "basic subset of the upstream CGMiner API" plus new commands;
  `echo '{"command":"pools"}' | nc IP 4028`. Command list: cgminer
  commands (asccount, asc, config, devdetails, devs, edevs, pools,
  summary, stats, version, estats, check, coin, lcd, switchpool,
  enablepool, disablepool, addpool, removepool — the pool-mutation
  commands "are not fully implemented… do not activate the pools")
  and new commands (fans, tempctrl, temps, tunerstatus, pause,
  resume). Worked examples with real payloads for fans, tempctrl,
  temps, tunerstatus, devdetails, pause/resume log output.
* **OSS-IMPLEMENTATION — pyasic** (`pyasic/miners/backends/braiins_os.py`,
  `pyasic/rpc/bosminer.py`, `pyasic/miners/factory.py`): the BOSMiner
  (pre-gRPC) handler reads everything over the 4028 RPC; the BOSer
  (post-gRPC) handler reads via gRPC for most data but still uses the
  same RPC API for version/pools. Detection in
  `MinerFactory._parse_socket_type`: `"BOSMINER" in upper_data or
  "BOSER" in upper_data` on the `version`/`devdetails` reply.
* **OSS-IMPLEMENTATION — asic-rs** (256foundation; DeepWiki
  "Supported Miners"): identification pattern "Response contains
  'BOSMINER' or 'BOSER' → MinerFirmware::BraiinsOS, RPC"; Braiins
  backend: RPC (4028/4029) ✓, WebAPI ✗ — the same fingerprint from
  a second, independent implementation.

### §1.2 The fingerprint — and where it sits (the datum v0.33 lacked)

Every BOSminer 4028 reply carries a STATUS section whose
`Description` is the miner build string. The Academy's worked
examples all show it verbatim:

```json
"STATUS": [{"STATUS": "S", "When": 1595938455, "Code": 202,
            "Msg": "4 Fan(s)", "Description": "BOSminer+ 0.2.0-ea64aec8e"}]
```

Detection (BeeSky `is_braiins_version`, in `beesky/core/braiins.py`):
case-insensitive substring `"bosminer"` OR `"boser"` anywhere in the
`version` reply. It matches pyasic's rule and asic-rs's rule
exactly, and it is anchored on the official worked example above.
Non-collision: stock cgminer answers `Description: "cgminer …"` /
`"bmminer …"`, LuxOS answers `"LUXminer …"`, Whatsminer does not
answer the cgminer envelope at all, VNish does not answer 4028 —
none contains either substring. The v0.36 mock suite re-runs the
non-collision battery against all four.

### §1.3 Transport + read contract (all TCP 4028, cgminer JSON envelope)

| BeeSky field | Command → section → keys |
|---|---|
| rate (native TH/s) | `summary` → SUMMARY[0]: `"MHS 1m"` first, then `"MHS 5s"`, then `"MHS av"` (pyasic reads MHS 1m); MHS / 1e6 = TH/s; legacy `ghs_*` = MHS / 1000 |
| uptime | `summary` → SUMMARY[0]["Elapsed"] (seconds) |
| pools | `pools` → POOLS[]: URL / User / Status / Accepted / Rejected / Get Failures / Remote Failures / Stratum Active / POOL (cgminer `pools_normalised` shape, as for LuxOS) |
| fans | `fans` → FANS[n]["RPM"] (Academy example: 4 fans, RPM + Speed) |
| boards | `temps` → TEMPS[]: ID / Chip / Board; `devdetails` → DEVDETAILS[]: ID / Chips / Model; `devs` → DEVS[]: ID / "MHS 1m" / "Nominal MHS". ID offset (pyasic): 6 when the first ID is in {6,7,8} (S9-style chains 6–8, Academy example), else 1 |
| power | `tunerstatus` → TUNERSTATUS[0]["ApproximateMinerPowerConsumption"] (watts; Academy example 1419); "PowerLimit" available |
| model | `devdetails` → DEVDETAILS[0]["Model"] (Academy example: "Bitmain Antminer S9"), fallback `"Braiins OS"` |
| tuner problems | `tunerstatus` → TUNERSTATUS[0]["TunerChainStatus"][]: Status not in {"Stable", "Testing performance profile", "Tuning individual chips"} → a `TUNER` problem on that chain (pyasic `_get_errors`) |

Auth: none for reads (the 4028 API is unauthenticated, like stock
cgminer). The `braiins` cred family stays tag-only for now — no
4028 call needs it.

### §1.4 Actions (documented only)

* `pause_mining` → `{"command": "pause"}`; `resume_mining` →
  `{"command": "resume"}`. pyasic's stop/resume_mining expect a
  JSON reply carrying a `"PAUSE"` / `"RESUME"` section (non-empty =
  success) — BeeSky requires the same key. (The Academy page's
  pause/resume listings show the miner's *log* output, not the wire
  reply; the wire reply shape is pyasic's, graded
  OSS-IMPLEMENTATION.)
* `reboot`: **NOT implemented** — no reboot command exists in the
  Academy's 4028 list; pyasic reboots via SSH (`ssh.reboot()`).
  BeeSky has no SSH path for miners, so reboot stays
  "not supported" for braiins with that reason.

### §1.5 UNKNOWNs (U-B*)

* U-B1 — the exact `Description` string on a **BOSer** (post-gRPC,
  BOS 24.x+) machine: pyasic/asic-rs match the substring "BOSER",
  but no worked example of a BOSer 4028 reply was found in any
  public source. The substring rule covers it if the string is
  present; a BOSer that dropped the 4028 API entirely would not be
  detected — that needs a real BOSer machine to confirm.
* U-B2 — pause/resume wire-reply success semantics rest on
  pyasic's `"PAUSE"`/`"RESUME"`-section check; no official worked
  example of the reply JSON exists. Hardware-unconfirmed.
* U-B3 — gRPC PAPI reads (port 50051, v0.33 §3.1) are still out of
  scope: no stdlib HTTP/2 + protobuf. The 4028 route covers the
  BOSMiner generation and (per pyasic's BOSer handler) the RPC
  surface of the BOSer generation; the gRPC-only fields (e.g. the
  streaming status) are not ported.

## §2 IceRiver — CLOSED (G-I1)

### §2.1 Sources

* **OSS-IMPLEMENTATION — pyasic** (`pyasic/miners/backends/iceriver.py`,
  `pyasic/web/iceriver.py`, `pyasic/miners/factory.py`,
  `pyasic/miners/device/models/iceriver/`): a complete backend —
  web API class, data readers, factory detection, per-model classes
  (KS0/KS1/KS2/KS3/KS3L/KS3M/KS5/KS5L/KS5M/AL3; KS = kHeavyHash,
  AL3 = BLOCKFLOW/Alephium Blake3; 3 hashboards each; KS0
  `expected_fans = 0`, KS3/AL3 4 fans).
* **CORROBORATED — real captured packet** (HackMD, "Monitoring my
  KS0 ULTRA KAS miner remotely", owner-published, 2024-06-30): the
  author sniffed the LAN console traffic himself and published the
  full `GET http://<IP>/user/userpanel?post=4` response (see §2.3).
  The endpoint, the `post=4` parameter and the `softver1` model
  string agree with pyasic exactly.
* **CORROBORATED — user manuals** (manuals.plus: AL0, AL3, RX0):
  default login `admin` / `12345678`, IP Report button, pool config
  through the web UI — the credentials pyasic uses as defaults.

### §2.2 Transport + auth

HTTP :80, no TLS. pyasic's `IceRiverWebAPI.send_command`:

1. `POST /user/loginpost` with params `post=6, user=admin,
   pwd=<password>` (default `12345678`; an `iceriver`-tagged cred
   set's password wins when one is saved);
2. `POST /user/userpanel` with param `post=4` → the status JSON.

The HackMD author notes no token is needed to call the API — the
login is best-effort in BeeSky (a failed login never fails the
fetch; cookies returned by loginpost are forwarded when present).
Detection is two-gated (see §2.4): a cheap title probe, then the
panel-shape validation.

### §2.3 The panel payload (real packet, KS0 Ultra, verbatim shape)

```json
{"error": 0,
 "data": {"model": "none", "algo": "none", "online": true,
  "firmver1": "BOOT_3_3", "firmver2": "image_1.0",
  "softver1": "ICM168_3_2_14_ks0ultra_miner",
  "softver2": "ICM168_3_2_14_ks0ultra_bg",
  "firmtype": "Factory", "nic": "eth0",
  "mac": "00:0a:66:30:00:6d", "ip": "192.168.0.136",
  "host": "ICERIVER", "locate": 0,
  "rtpow": "359G", "avgpow": "375G", "unit": "G",
  "runtime": "00:01:15:16", "powstate": true,
  "fans": [6079, 6079, 0, 0],
  "pools": [{"no": 1.0, "addr": "stratum+tcp://kas-asia.f2pool.com:1400",
             "user": "kwl88347.001", "pass": "21235365876986800",
             "connect": -1.0, "accepted": 281.0, "rejected": 0.0,
             "state": 1.0, "lsdiff": 0.0, "lstime": "00:00:00"}],
  "boards": [{"no": 1.0, "chipnum": 18.0, "freq": 875.0,
              "rtpow": "359.17G", "avgpow": "376.28G",
              "intmp": 48.0, "outtmp": 37.0, "state": true}]},
 "message": ""}
```

Field table (BeeSky `fetch_record`):

| BeeSky field | Source |
|---|---|
| model | `data.softver1`: split on `_`; last token `"miner"` → take [-2], else strip `"miner"` from [-1]; upper-cased (pyasic's rule: `ICM168_3_2_14_ks0ultra_miner` → `KS0ULTRA`) |
| rate (native) | `data.rtpow` + `data.unit`: number with the unit suffix stripped; unit `"G"` → `"GH/s"`, `"T"` → `"TH/s"`, `"M"` → `"MH/s"`, `"K"` → `"kH/s"` — the response's own unit is the native unit (v0.20 discipline; KS models report G, AL3 reports T) |
| uptime | `data.runtime` `"DD:HH:MM:SS"` → seconds |
| fans | `data.fans[]` (RPM, as reported — the KS0 Ultra reports [6079, 6079, 0, 0]) |
| boards | `data.boards[]`: index = `no`, chips_total = `chipnum`, chips_alive = `chipnum` when `state` is true else 0, temp_c = `intmp` (pyasic maps `temp = intmp`, `chip_temp = outtmp`; intmp is the hotter internal temp, so it is the chain temp for the 85 °C rule) |
| pools | `data.pools[]`: url = `addr`, worker = `user`, accepted, rejected, active = (`connect` == 1), alive = (`state` == 1). The `pass` field is **never** copied into the record |
| mac | `data.mac` (normalised upper-case); `host` is the hostname |
| mining? | `data.powstate` (true = hashing); `locate` is the fault-light state |
| power | **not reported** — the panel carries no wattage field (G-I2, named gap; energy math skips the miner) |

**Response-shape divergence (U-I1, handled, not hidden):** the real
packet above is `{"error": 0, "data": {...}}` — top-level `data`.
pyasic's backend reads `web_userpanel["userpanel"]["data"]` instead,
i.e. it expects a `userpanel` wrapper that the captured packet does
not have. BeeSky parses **both** shapes (wrapper first, then
top-level `data`) and the mock suite covers both; which firmware
generations return which shape is hardware-unconfirmed. (The
inconsistency is inside pyasic too — its own factory
`get_miner_model_iceriver` reads `result["data"]["softver1"]`,
top-level, while its backend reads the wrapper — so the top-level
shape is the one pyasic's own model detection relies on.)

### §2.4 Detection (two gates, positive-only)

1. **Title gate (cheap):** `GET http://<ip>/` returns a page
   containing `<TITLE>用户界面</TITLE>` (pyasic's factory
   `_parse_web_type` rule — the IceRiver console's title).
2. **Shape gate (decisive):** the `userpanel` POST returns JSON
   with `error == 0` and a data object containing `softver1`.

A host is claimed only when gate 2 passes. Non-collision: no
Antminer-family web UI has a `/user/userpanel` endpoint returning
this shape; the mock suite asserts the stock CGI payload, the
dashd summary and a Whatsminer summary all fail the shape gate,
and the title gate alone never claims a host. Scan cost: gate 1 is
one GET on hosts the dashd/stock steps already left unclaimed, and
the two POSTs only run on a title match.

### §2.5 Actions (documented only)

* `find_miner` → `POST /user/userpanel` with `post=5, locate=1`
  (pyasic `IceRiverWebAPI.locate(True)`); `locate=0` turns it off.
  BeeSky sends only the "on" form — the ops job's find action is a
  one-shot locate.
* `reboot` / `switch_pool`: **NOT implemented**. No reboot endpoint
  appears in pyasic or the captured traffic. Pool-setting exists
  (`GET /user/machineconfig?...&post=3`, HackMD) but its
  query-string form uses `?` separators between parameters (not
  `&`), which is non-standard enough that a write built on this
  single source is not trusted — it stays a named gap (G-I3) until
  a second source confirms the format.

## §3 Braiins/IceRiver in BeeSky — wiring notes

* `beesky/core/braiins.py`: `BraiinsClient` over the shared
  `CgminerClient`; `is_braiins_version(resp)` is the §1.2
  fingerprint. `fetch_record` builds via `report._finalise_record`
  (the whatsminer pattern — explicit native rate).
* `beesky/core/iceriver.py`: `IceRiverClient` over stdlib
  `http.client` (+ `urllib.parse`); `is_iceriver_panel(resp)` is
  the §2.4 shape gate; `parse_model(softver1)` is pyasic's rule.
* `discover.probe_host`: the Braiins refinement reuses the
  `version` reply the LuxOS refinement already fetched (same
  else-branch, after the Avalon check); the IceRiver probe runs
  after the stock loop and before the locked-dashd 401 fallback,
  trying `iceriver`-tagged cred passwords then the factory default
  `12345678`; the winning password rides the candidate
  (`Candidate.iceriver_password`) into the fetch stage.
* Fetch (`cli._fetch_record`, `ops._fetch_record`) and
  `inspect.inspect_device` gain `braiins` / `iceriver` branches;
  `actions.execute` gains braiins pause/resume and iceriver
  find_miner. Dart `sourceLabel` gains both families.
* `docs/parity-audit.md` is a v0.35 snapshot and is NOT rewritten
  here; the coverage scoreboard moves in `tests/RESULTS.md`
  (7 → 9 real adapters) and the audit's G-B1/G-I1 rows are closed
  by this mapping.

## §4 Jasminer / SunLune — GAP G-J1 (unchanged)

* Searched: pyasic (no Jasminer backend, factory, model or web
  class anywhere in the tree), asic-rs (no Jasminer support),
  GitHub/web search for an OSS Jasminer API client — the only hit
  is Find-My-Miner (OBitsPlease), a heuristic IP scanner whose
  Jasminer fingerprint is explicitly "heuristic and
  firmware-dependent" (a `version` query on 4028 + hints), not a
  read API. The X4 user manual (SunLune, Aug 2021) documents only
  the web UI + their `sl_Miner.exe` IP tool.
* Closing needs a published spec, an OSS read implementation, or a
  real device. `jasminer` stays a cred-family tag only.
