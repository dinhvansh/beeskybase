# Auradine + SealMiner + Pit-Bit adapter mapping (v0.38.0)

Source: the vendors' own published material and the two
established open-source miner libraries — the same
docs-route as v0.33 (MicroBT manuals) and v0.36 (pyasic)
and v0.37 (Epic docs + dashboard):

  * **Auradine** — asic-rs `asic-rs-firmwares/auradine`
    (RPC 4028 + web :8080 backends, with real test-JSON
    fixtures for every command) and pyasic
    (`pyasic/miners/backends/auradine.py`,
    `pyasic/web/auradine.py`, `pyasic/rpc/gcminer.py`,
    `pyasic/miners/auradine/flux/*`, docs/miners/auradine)
    — the two libraries agree on transport, auth and every
    control body below; the Auradine Hardware Reference
    (auradine.com, OFFICIAL-DOC) confirms the ports
    (80/443/4028 TCP API/8443 REST API) and the FluxVision
    cloud surface.
  * **SealMiner** — asic-rs `asic-rs-firmwares/sealminer`
    (RPC 4028 + web CGI backends, real test-JSON fixtures)
    plus the Bitdeer setup guides (cryptominerbros,
    yesmining — web dashboard on :80, Sealminer Tool,
    default credentials) for the web-UI facts the code
    does not state.
  * **Pit-Bit** — no vendor doc, no OSS implementation in
    either library; only the Toolkit re-mining traces
    (docs/vendor-remining.md §2) and Awesome Miner's
    public Pitbit-firmware support notes.

Evidence grades used below: OFFICIAL-DOC (vendor docs),
OSS-IMPLEMENTATION (asic-rs / pyasic code — the vendor's
shipping client behaviour as implemented by two
independent libraries), CORROBORATED (both libraries
agree, or library + vendor doc agree), INSUFFICIENT
(not evidenced anywhere — never implemented on a guess),
UNKNOWN (not evidenced — never implemented).

## §1 Auradine (Teraflux) — CLOSED (CORROBORATED)

### §1.1 Transport — CLOSED

Two surfaces, both used:

  * **RPC**: TCP **4028**, cgminer-JSON
    `{"command": "<name>"}\n` (optional `"parameter"`),
    replies carry a cgminer STATUS array
    (`"STATUS": "S"` + `Description`). asic-rs
    `backends/v1/rpc.rs`; pyasic `GCMinerRPCAPI`
    (pyasic/rpc/gcminer.py — "No documentation for this
    API is currently publicly available", i.e. pyasic
    itself reverse-engineered it; the two agree on the
    envelope).
  * **Web**: HTTP port **8080**, token auth
    (asic-rs `backends/v1/web.rs`, pyasic
    `web/auradine.py` — identical): POST `/token`
    `{"command": "token", "user": ..., "password": ...}`
    → token at `/Token/0/Token`; every later request
    carries a `Token` header; a 401 / token-expired
    reply re-authenticates once and retries. POST
    payloads are `{"command": ..., ...params}`.
    Default credentials **admin/admin** (asic-rs
    `HasDefaultAuth`, pyasic settings
    `default_auradine_web_password: admin` + web
    username `admin`).

The hardware reference's **8443 REST API** (and the
FluxVision cloud's "40+ REST API endpoints") are
OFFICIAL-DOC that they exist, but no endpoint shape is
evidenced in either library — UNKNOWN (U-AU2), not
implemented. The on-device :8080 web API is the
implemented surface.

### §1.2 Detection — CLOSED

Discovery commands (asic-rs `firmware.rs`):
`version` + `devdetails`. Identification
(`identify_rpc`): the reply contains "GCMINER" or
"FLUXOS" — the miner's cgminer fork is **GCMiner** and
its firmware **FluxOS** (STATUS Descriptions
"GCMiner-2023-05.24-…", "FluxOS-2023-12.27-…",
`/VERSION/0/GCMiner` = "0.5").

Divergence D-AU1 (case): asic-rs checks the two
markers case-SENSITIVELY, but its own fixtures carry
them mixed-case ("GCMiner", "FluxOS"), so a literal
case-sensitive check fails on the worked examples.
BeeSky matches case-insensitively ("gcminer" /
"fluxos" over the whole version reply). Pinned by the
fixture-based mock.

Non-collision vs every family BeeSky already detects
(witnesses in `tests/mock_vendors5_test.py`):

  * stock / LuxOS / Avalon / Braiins / SealMiner all
    speak cgminer-JSON on 4028, but their version
    replies carry "mockminer"/"cgminer",
    "LUXminer …", "BOSminer+ …", "bdminer …" —
    none contains "gcminer" or "fluxos" ("cgminer"
    is not "gcminer": the substrings differ at the
    second letter);
  * Whatsminer speaks its Msg-envelope dialect on
    4028 — never reaches the version check;
  * VNish dashd serves HTTP JSON on :80, never :4028;
  * IceRiver serves its web UI on :80, never :4028;
  * Epic serves HTTP JSON on :4028 — its version
    reply is not a cgminer reply at all.

Probe placement: the same `version`-reply refinement
as LuxOS (v0.33) / Braiins (v0.36) inside the cgminer
claim in `discover.probe_host` — after the Avalon
refinement, alongside the LuxOS/Braiins checks, on
the one `version` call the probe already pays for.

### §1.3 Reads — CLOSED

RPC (no auth), all fixtures from asic-rs
`src/test/json/v1/`:

  * `summary` — `MHS 5s` / `MHS av` / `MHS 1m` /
    `MHS 15m` (MH/s), `Elapsed` (s), `Accepted` /
    `Rejected`, `Total MH`. (Fixture magnitudes look
    like a dev unit — `MHS av` ≈ 8 TH/s on a
    150–260 TH/s line — U-AU3; the UNITS are MH/s
    per the cgminer convention and both libraries
    agree, so the record reads them as MH/s.)
  * `version` — `/VERSION/0/GCMiner` ("0.5"),
    `/VERSION/0/API` ("1.0").
  * `devs` — per board: `DEV`/`ID` (1-based),
    `Enabled`, `MHS 5s`, `Name` "ASICBoard",
    `Status` "Alive", `Temperature` (°C).
  * `asccount` — `BoardCount` (3), `AsicCount`
    (396) → 132 chips/board.
  * `pools` — `POOL`, `URL`, `User`, `Status`
    ("Alive"/"Dead"), `Stratum Active`, `Accepted` /
    `Rejected` — the plain cgminer pools shape, so
    `pools_normalised_from` applies verbatim.

Web (token auth, best-effort — a failed web call
costs the field, never the record):

  * `ipreport` — `/IPReport/0/{mac, SerialNo,
    hostname, model ("AT1500"), version
    ("2023-12.27"), InternalType ("T0"),
    CBSerialNo, ChassisSerialNo, HBSerialNo[]}`.
  * `fan` — `/Fan[]` `{ID, Speed (rpm), Max,
    Target}` (4 fans in the fixture).
  * `psu` — `/PSU/0/{PowerIn ("58.94W" — a string
    WITH units, parsed like asic-rs
    `parse_number_from_units`), FanSpeed1/2
    ("4052.00 RPM"), Vin, Vout, Iin, Iout}`.
  * `temperature` — `/Temperature[]` `{ID, Name,
    BoardTemp[{ID, Temperature}], ChipTemp[{ID,
    Temperature}]}`; ID 0 is "Control Board", IDs
    1..3 are "Hash Board 1..3" (board positions are
    ID−1, asic-rs `board_position_from_id`).
  * `voltage` — `/Voltage[]` `{ID,
    ChipVoltage[{ID, Voltage}]}`; `frequency` —
    `/Frequency[]` `{ID, ChipFrequency[{ID,
    Frequency}]}`.
  * `led` — `/LED/0/{Code, Msg}` (Code 2 = normal,
    3 = locate); `mode` — `/Mode/0/{Mode, Power,
    Ths, Sleep ("on"/"off")}`.

Model: `devdetails` `/DEVDETAILS/0/Model`
uppercased (asic-rs `get_model`); known models
AI2500, AT1500, AI3680, AT2880, AH3880 (asic-rs
enum) + AT2870 (hardware reference) + AD2500/AD3500
(pyasic docs). Fallback: the ipreport `model`
field; then the family label "Auradine".

### §1.4 Controls — exact params (CORROBORATED)

All web POSTs, token auth; password rule: the
winning auradine-tagged set's password, else the
factory default **admin/admin** (same rule as
epic's "letmein", mapping D-E5). Wired into
`actions.execute` (family `auradine`):

  * `reboot` → POST `restart` (no params) — full
    device reboot (asic-rs `Restart`, pyasic
    `reboot`).
  * `restart_mining` → POST `restart` with param
    `"gcminer"` — restarts only the mining program
    (asic-rs comment: "`restart` with no parameter
    reboots the miner; the `gcminer` parameter
    restarts only the mining program"; pyasic
    `restart_gcminer`).
  * `pause_mining` → POST `mode` `{"sleep": "on"}`
    (asic-rs `Pause`, pyasic `stop_mining`).
  * `resume_mining` → POST `mode` `{"sleep": "off"}`
    (asic-rs `Resume`, pyasic `resume_mining`).
  * `find_miner` → POST `led` `{"code": 3}` (on) /
    `{"code": 2}` (off) (asic-rs `SetFaultLight`,
    pyasic `fault_light_on/off` with
    `AuradineLEDCodes.LOCATE_MINER/NORMAL`).
  * `switch_pool` → POST `updatepools` `{"pools":
    [{url, user, pass}]}` — max 3 pools (asic-rs
    `build_update_pools_payload`, take(3)), empty
    password becomes "x". BeeSky reads the current
    RPC `pools` first, replaces slot `pool_id`
    (default 0), re-sends the rest unchanged.
  * `set_power_target` (auradine handler of the
    epic-born command type) → POST `mode`
    `{"mode": "custom", "tune": "power", "power":
    <watts>}` (asic-rs `SetPowerLimit`, pyasic
    `set_power_limit`).

NOT wired (named, with the reason):

  * `set_fan_speed` — a per-fan form exists
    (pyasic `set_fan(fan, speed_pct)` → POST `fan`
    `{index, percentage}`) but no set-all form;
    BeeSky's task carries no fan selector, so
    picking fan 1 would be an invented behaviour.
  * `factory-reset` — destructive scope.
  * `firmware_upgrade` — firmware scope.
  * `set_network` / `set_psu` / `register` /
    `restart_api_server` — no BeeSky concept.

### §1.5 Record shape + divergences

  * Native rate is MH/s (`summary` "MHS 5s"/"MHS
    av", v0.20 discipline); `ghs_5s` = MHS 5s/1000,
    `ghs_av` = MHS av/1000; `rate_value` = MHS av/1e6
    TH/s (the stable average, Braiins precedent).
  * Chips: `chips_total` = AsicCount/BoardCount
    (132) per board; `chips_alive` follows
    asic-rs's rule — expected minus failed, where
    failed = chips PRESENT in the temperature data
    but not working (temp ≤ 0 and voltage ≤ 0 and
    frequency ≤ 0). The fixture's ChipTemp arrays
    are partial (3 of 132 chips per board), so a
    board with no failed chips reports 132 alive;
    absent chips are never counted dead.
  * Temps: per-board `temp_c` from `devs`
    Temperature (RPC, always present); the
    temperature endpoint refines inlet/outlet
    (min/max of BoardTemp) when the web call
    succeeds — recorded on the record as
    `board_temp_min_c` / `board_temp_max_c` only
    when present, never invented.
  * Fans: `fans_rpm` from web `fan` (Speed, rpm);
    empty when the web call fails (degraded, not
    failed).
  * Power: `power_w` = summary `Wattage` when
    numeric, else PSU `PowerIn` parsed from its
    units string, else None.
  * Pools: `pools_normalised_from` on the RPC
    `pools` reply (URL/User/Status verbatim).
  * `hostname`, `mac`, serial: from `ipreport`
    when the web call succeeds; `model` from
    devdetails, else ipreport, else "Auradine".
  * Over-temp: the shared 85 °C rule (`report.py`)
    applies to the devs/board temperatures.

### §1.6 UNKNOWNs

  * U-AU1 — exact canonical payload bytes: the
    fixtures are asic-rs's test captures, not a
    live-miner session; one real reply is the
    one-datum close.
  * U-AU2 — the :8443 REST API shapes (see §1.1).
  * U-AU3 — fixture rate magnitudes (see §1.3).
  * U-AU4 — board/chip counts for AT2870/AD2500/
    AD3500 (Unknown fallback covers; devdetails +
    asccount report the real counts at runtime).
  * U-AU5 — web STATUS descriptions vary by
    endpoint (`temperature`/`voltage` carry "2.2.0",
    `fan`/`psu`/`led` carry "GCMiner-…",
    `mode`/`ipreport` carry "FluxOS-…") — no
    impact: BeeSky never gates on them.

## §2 SealMiner (Bitdeer) — CLOSED (CORROBORATED)

### §2.1 Transport — CLOSED

Two surfaces:

  * **RPC**: TCP **4028**, cgminer-JSON
    `{"command": "<name>"}\n` (optional `"parameter"`
    — a JSON STRING for `updatepools`/`ascset`, see
    §2.4), replies carry a cgminer STATUS array
    (asic-rs `backends/v2025/rpc.rs`).
  * **Web**: HTTP **:80** CGI (asic-rs
    `backends/v2025/web.rs`): POST
    `/cgi-bin/login.php` with form body
    `username=<user>&origin_pwd=<pass>` +
    `Content-Type: application/x-www-form-urlencoded;
    charset=UTF-8` + `X-Requested-With:
    XMLHttpRequest` → session cookie from the
    `set-cookie` header (first segment); later
    calls are GET/POST `/cgi-bin/<command>.php`
    with a `Cookie` header. Default credentials
    **seal/seal** (asic-rs `default_auth`).
    Divergence D-SE2 (case): one setup guide
    prints SEAL/SEAL, another seal/seal; the
    CODE says lowercase "seal". BeeSky tries
    "seal" first; a fleet that changed the
    password uses saved sets (the actions path
    resolves the winning set's password).

### §2.2 Detection — CLOSED

Discovery commands (asic-rs `firmware.rs`):
`version` (RPC) + HTTP web root. Identification
(`identify_rpc`): the reply contains "BDMINER" —
the miner's cgminer fork is **BDMiner**
(STATUS Descriptions "bdminer 4.11.1",
`/VERSION/0/BDMiner` = "4.11.1", API "3.7").

Divergence D-SE1 (case): asic-rs checks the
marker case-SENSITIVELY, but its own fixtures
carry it lowercase ("bdminer 4.11.1") and
mixed-case ("BDMiner"). BeeSky matches
case-insensitively ("bdminer" over the whole
version reply). Pinned by the fixture-based mock.

Non-collision vs every family BeeSky already
detects (witnesses in `tests/mock_vendors5_test.py`):

  * stock / LuxOS / Avalon / Braiins / Auradine
    version replies carry "mockminer"/"cgminer",
    "LUXminer …", "BOSminer+ …", "GCMiner …" —
    none contains "bdminer";
  * Whatsminer never reaches the version check
    (Msg envelope); VNish dashd is :80-only;
    IceRiver is :80-only; Epic is HTTP JSON.

Probe placement: the same `version`-reply
refinement as LuxOS/Braiins/Auradine inside the
cgminer claim in `discover.probe_host`.

NOT used: asic-rs's second fingerprint,
`identify_web` (the HTTP root body contains
"amazeui") — the Amaze-UI framework is suspected
(shared, unverified) to also appear in
AvalonMiner's web UI, so it cannot claim a host
on its own (U-SE1); the RPC fingerprint is
sufficient and has no such doubt.

### §2.3 Reads — CLOSED

RPC (no auth), all fixtures from asic-rs
`src/test/json/v2025/`:

  * `summary` — `MHS 5s` / `MHS av` (MH/s),
    `Elapsed`, `Accepted` / `Rejected`,
    `Best Share`, `Hardware Errors`. (Fixture
    magnitudes are realistic: `MHS 5s` ≈
    368 TH/s on an A2-class unit.)
  * `stats` — the whole board/PSU picture in ONE
    flat object: per board `"<n> Chip Count"`,
    `"<n> Bad Chip Count"`, `"<n> Temp 0..3"`,
    `"<n> Speed"` (fan rpm), `"<n> SN"`,
    `"<n> Online"`, `"<n> Freq"`,
    `"<n> MHS(Sample)"`, `"<n> MHS(Ideal)"`,
    `"<n> Tune Status"`; totals `"Board Count"`
    (3), `"Chip Count"` (459), `"Firmware"`
    ("2025091001"), `"MAC"`, `"Ctrl Board"`
    ("taurus_air_v1.1"), `"Ctrl Board SN"`,
    `"ASIC"` ("Seal02-V1"), `"Fan Count"` (4),
    `"PSU Input Power"` (3504 W), `"PSU Output
    Power"`, `"PSU Input/Output Voltage"`,
    `"PSU Output Current"`, `"PSU Efficiency"`,
    `"PSU Temp AMB"`, `"PSU Model"`,
    `"PSU SN"`, `"PSU Firmware"`, `"PSU Fan
    Speed"`, `"System Uptime"`, `"Temp"` (70),
    `"PM State"` ("Running"), `"Mining Mode"`
    ("Normal"), `"Power Limit"` (3500).
  * `version` — `/VERSION/0/BDMiner` ("4.11.1"),
    `/VERSION/0/API` ("3.7").
  * `pools` — `POOL`, `URL`, `User`, `Status`
    ("Alive"/"Dead"), `Stratum Active`,
    `Accepted` / `Rejected` — plain cgminer pools
    shape, so `pools_normalised_from` applies.

Web (cookie auth, best-effort — a failed web
call costs the field, never the record):

  * `get_system_info` — `{brand: "Sealminer",
    miner_type: "A2", firmware_version:
    "2025091001", macaddr, ipaddress, led:
    "on", miningMode: "2", ctrl_version,
    crtl_sn, psu_model: "boco_v2.0",
    ratedHashrate}`.
  * `miner_psu_status` — `{Power: 3504,
    Current: 206, Voltage: 15.67, Temp: 26,
    Online: 1}` (the stats PSU keys are the
    primary power source; this is the fallback).

Model: `devdetails` `/DEVDETAILS/0/Model`
(RPC first, asic-rs `get_model_with_auth`),
fallback web `get_system_info` `miner_type`;
known models A2, A3 Pro Hydro (asic-rs enum;
" A3 Pro Hydro" is the dashboard spelling of
the same model) + Unknown fallback. The
firmware version is the YYYYMMDD build
("2025091001" → 2025-09-10 in asic-rs's
semver parse); BeeSky records it verbatim.

### §2.4 Controls — exact params (CORROBORATED)

Password rule: the winning sealminer-tagged
set's password, else the factory default
**seal/seal** (same rule as epic/auradine).
Wired into `actions.execute` (family
`sealminer`):

  * `reboot` → web GET `reboot.php` (asic-rs
    `Restart` → `web.reboot()`).
  * `pause_mining` → RPC `ascset` with parameter
    `"0,suspend"` (asic-rs `Pause`).
  * `resume_mining` → read RPC `stats` first:
    if `/STATS/0/PM State` == "Running" the
    miner is already hashing and the action is a
    no-op success; else RPC `restart` (asic-rs
    `Resume` — note the guard is asic-rs's own,
    not BeeSky's invention).
  * `find_miner` → web POST `led_conf.php`
    `{"key": "led", "value": "on"}` / `"off"`
    (asic-rs `web.set_led`).
  * `switch_pool` → RPC `updatepools` with
    parameter = the JSON STRING
    `{"pools": [{url, user, pass}]}` (asic-rs
    `rpc.updatepools` — the parameter is a
    stringified JSON object, not an object),
    then web `reboot()` fire-and-forget
    (asic-rs `set_pools_config`: a failed
    updatepools is a failure; the reboot after a
    successful one is best-effort — `let _ =`).
    BeeSky reads the current RPC `pools` first,
    replaces slot `pool_id` (default 0),
    re-sends the rest unchanged.
  * `set_power_target` (sealminer handler of
    the epic-born command type) → RPC `ascset`
    with parameter
    `"0,powerlimit,{\"value\":\"<watts>\"}"`
    (asic-rs `set_power_limit`; whole watts
    only — the code enforces finite, whole,
    non-negative, u32-representable). Success is
    STATUS "S" **and** Code 119 (asic-rs
    `set_tuning_option` — the code asserts both).
  * `set_mining_mode` (new command type, sealminer
    only) → RPC `ascset` with parameter
    `"0,workmode,{\"mode\": \"low_power\" |
    \"normal\" | \"high_performance\"}"` (asic-rs
    `set_mining_mode`). `low_power` is A2-only
    (asic-rs `set_tuning_config` bails otherwise)
    — BeeSky enforces the same gate
    client-side and reports it.

NOT wired (named, with the reason):

  * `restart_mining` — asic-rs's `RestartMining`
    impl is EMPTY (unsupported); there is no
    documented mining-process-only restart.
  * `change_password` / logs / factory reset /
    firmware upgrade — asic-rs marks all four
    unsupported.
  * The web numeric mining-mode form (POST
    `set_mining_mode.php` `{"miningMode": <u32>}`)
    — the numeric values are not documented
    anywhere (U-SE3); BeeSky wires the RPC
    `ascset` form instead.

### §2.5 Record shape + divergences

  * Native rate is MH/s (`summary` "MHS 5s"/"MHS
    av", v0.20 discipline); `ghs_5s` = MHS 5s/1000,
    `ghs_av` = MHS av/1000; `rate_value` = MHS av/1e6
    TH/s (stable average, Braiins precedent).
    Divergence D-SE3: asic-rs reads THE hashrate
    from stats `MHS(2m)` (and expected from
    `MHS(Rated)`); BeeSky reads the record rate
    from `summary` like every other cgminer-family
    adapter — the stats 2m figure is the same
    miner's 2-minute average and stays available
    in inspect; the choice is stated, not hidden.
  * Chips: per board `chips_total` = `"<n> Chip
    Count"`, `chips_alive` = total minus
    `"<n> Bad Chip Count"` (asic-rs rule);
    `dead_positions` stay empty (the stats carry
    counts, not positions — Whatsminer G-W2
    precedent).
  * Temps: per-board `temp_c` = MAX of the
    non-zero `"<n> Temp 0..3"` (asic-rs rule);
    intake = first, outlet = last of the same
    four (recorded as `board_temp_min_c` /
    `board_temp_max_c` when present).
  * Fans: `fans_rpm` from `"<n> Speed"` for n in
    0..`"Fan Count"` (4 in the fixture — indices 0–2
    are the board fans and index 3 is the fourth
    chassis fan; asic-rs `GetFans` reads exactly
    this range, and the separate `"PSU Fan Speed"`
    key feeds only the PSU-fan list).
  * Power: `power_w` = stats `"PSU Input Power"`
    (3504 W), fallback web `miner_psu_status`
    `Power`.
  * Pools: `pools_normalised_from` on the RPC
    `pools` reply.
  * `mac` from stats `MAC` (fallback sysinfo
    `macaddr`); serial from `"Ctrl Board SN"`;
    `model` from devdetails, else sysinfo
    `miner_type`, else "Sealminer".
  * Over-temp: the shared 85 °C rule (`report.py`)
    applies to the per-board max temps.

### §2.6 UNKNOWNs

  * U-SE1 — the "amazeui" web fingerprint (§2.2).
  * U-SE2 — exact canonical payload bytes: the
    fixtures are asic-rs's test captures, not a
    live-miner session.
  * U-SE3 — the web numeric mining-mode values
    (§2.4).
  * U-SE4 — `PM State` values other than
    "Running" (only "Running" is evidenced in
    the fixtures; any other value takes the
    restart path in `resume_mining`).

## §3 Pit-Bit — INSUFFICIENT (named gap G-PB1, unchanged)

What it is: **PITBIT custom Antminer firmware**
(Russian AI-autotuning firmware for Antminers —
"PITBIT ONLINE", dev-fee or lifetime licence;
Awesome Miner lists Pitbit firmware support with
pool changes, reboot, LED flash, password
change, set target frequency, estimated power
reading; a 2026-10 pool incident blamed it,
unconfirmed).

What the Toolkit binaries actually contain
(docs/vendor-remining.md §2, re-mining strings):
`PitBitRepository`, `PitBitApiSession` — and the
one informative line: **`PitBitApiSession.
fromBitmainSession`** — the Pit-Bit session is
constructed FROM a Bitmain session. The adapter
speaks the **Bitmain stock protocol** (cgminer
RPC on 4028 + stock CGI web). No version-string
fingerprint literal exists anywhere in the
binaries; no vendor doc; no OSS implementation
in pyasic or asic-rs (neither library has a
pitbit module at all).

Consequence, stated plainly: a Pit-Bit-flashed
Antminer is **already readable by BeeSky's
stock/cgminer path** — correct data, family label
"cgminer"/"stock" instead of "pit-bit". What is
missing is only the *detection* that would label
it "pit-bit". The one datum that closes G-PB1 is
a `version` reply from a Pit-Bit machine (the
marker string in its Description). There is no
"pit-bit" cred tag either (it was never added to
CRED_TYPES — a Pit-Bit machine's sets are tagged
"stock", the protocol it speaks); detection stays
gap G-PB1.

## §4 Scoreboard

Real read adapters: **12** of HashCore's 15–16
(cgminer-generic, dashd for hashcore+oldVnish,
bitmain stock, canaan, microBt, braiins,
iceriver, luxos, epic, **auradine**,
**sealminer**). Jasminer + pit-bit remain the
only cred-tag-only families. Vendor breadth is
now the smallest remaining parity gap; the
others are production unlock payloads (U-1..U-5),
IP-Report wire confirmation on real hardware,
and code signing (owner's part).
