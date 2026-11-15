# ePIC adapter mapping (v0.37.0)

Source: Epic's own published material — the ePIC Dashboard repo
(github.com/epicblockchain/epic-dashboard), read 2026-11-12:

  * `docs/APIv2.md` — API v2, epic-miner firmware v4.0.0 on the SC200
    (394 lines, OFFICIAL-DOC);
  * `docs/APIv3.md` — API v3, PowerPlay (636 lines, OFFICIAL-DOC);
  * `README.md` — default password, scan behaviour, hostname
    example (OFFICIAL-DOC);
  * the dashboard's own connection code (CODE — the vendor's
    shipping client, ground truth where it disagrees with the
    docs): `src/portscan.js` (scan probe), `src/main.js`
    (request URLs), `src/minerHttp.mjs` (request helper +
    OpenAPI gating), `src/app.jsx` `handleApi` (every POST body
    the UI actually sends), `src/tabs/ControlTab.jsx`,
    `src/tabs/FanTab.jsx`, `src/apiCompatibility.mjs`
    (preset/tune shapes), `src/boardControl.mjs`,
    `src/minerTable.mjs` (model handling).

Evidence grades used below: OFFICIAL-DOC (vendor docs),
CODE (dashboard source), CORROBORATED (doc + code agree),
UNKNOWN (not evidenced anywhere — never implemented on a guess).

## §1 Transport — CLOSED

HTTP JSON to `http://<ip>:4028/...`. GET needs no password; POST
carries `{"param": ..., "password": "..."}` and returns
`{"result": bool, "error": string|null}` (APIv2 §POST,
APIv3 §POST — OFFICIAL-DOC, identical in both versions).

The PORT is 4028, pinned three times in the dashboard code
(the API docs only ever write `<port>`):

  * `src/portscan.js:24` — the scan probe opens
    `{hostname: ip, port: 4028, path: '/summary', method: 'GET'}`;
  * `src/main.js:100` — firmware-update POSTs go to
    `http://${miners[i].address}:4028${api}`;
  * `src/app.jsx:1201` — every `handleApi` POST goes to
    `http://${miners[i].address}:4028${api}`.

4028 is also the cgminer port — but the wire here is HTTP JSON,
not the cgminer text protocol, so the two never collide (see §2).

## §2 Detection — CLOSED

The dashboard's own scan (`src/portscan.js` `checkGet`) is the
detection contract: GET `:4028/summary`, parse the JSON, take
`.Hostname`. BeeSky's fingerprint is that probe plus a
structural gate — a claim needs ALL of:

  * HTTP 200 with a JSON object body;
  * `"Hostname"` a non-empty string;
  * `"Session"` an object carrying `"Average MHs"` (number);
  * `"HBs"` a list.

Positive-only: anything else is not a claim. The hostname
prefix is deliberately NOT part of the fingerprint — the
dashboard never checks it (it accepts any `Hostname`), and
README's example `epicminer30032518` is only a naming
convention (blacklist entries are "hostname/unique id", e.g.
`"epicminer30032518"`). The structural keys are the claim;
the hostname value is recorded verbatim on the record.

Non-collision vs every family BeeSky already detects
(witnesses in `tests/mock_vendors4_test.py`):

  * stock / LuxOS / Avalon / Braiins all speak the cgminer
    TEXT protocol on 4028 — an HTTP GET there returns no JSON
    object, let alone one with Hostname/Session/HBs;
  * Whatsminer speaks its Msg-envelope dialect on 4028 — same;
  * VNish dashd serves HTTP JSON on :80, never :4028;
  * IceRiver serves its web UI on :80, never :4028.

Probe placement: step 1c in `discover.probe_host`, after the
Whatsminer (1a) and cgminer (1b) probes fail on the same open
4028 port — an Epic miner answers both earlier probes with
non-parseable replies, so it falls through to 1c cleanly.

## §3 Reads — CLOSED

`/summary` alone (GET, no password) covers the record:

  * rate: `Session["Average MHs"]` (float, native MH/s) and
    `Session["LastAverageMHs"]["Hashrate"]` (the recent sample,
    used as the 5s-equivalent GH/s value);
  * uptime: `Session["Uptime"]` (uint seconds);
  * shares: `Session["Accepted"]` / `["Rejected"]` (totals);
  * boards: `HBs[]` — `Temperature` (°C, uint), `Input
    Voltage` / `Output Voltage`, `Input Current` /
    `Output Current`, `Input Power` / `Output Power`
    (watts — the unit is the doc's `Target Power` in watts,
    see §4 `/mode`; power_w is `Power Supply Stats`'s
    `Input Power` when present (dashboard code,
    `table.jsx` `totalPower`), else Σ HBs `Input Power`,
    else Σ `Output Power`);
  * Chain index is `HBs[].Index` verbatim — the dashboard
    displays Index as the board number (`table.jsx`
    `activeHBs`), so BeeSky shows the same number; no
    +1 is applied.
  * fans: `Fans["Fans Speed"]` — ONE percentage (0–100), NOT
    per-fan rpm (see §5);
  * pool: `Stratum["Current Pool"]` + `["Current User"]` +
    `["IsPoolConnected"]`; `StratumConfigs[]` — `{pool,
    login, password}` (passwords are never copied into the
    record, IceRiver rule);
  * coin/algorithm: `Mining["Coin"]` / `["Algorithm"]`;
  * preset: `PresetInfo["Preset"]` / `["Target Power"]`;
  * hostname: `Hostname`; software: `Software`;
  * `Misc["Locate Miner State"]` (LED on/off),
    `Misc["Append Unique Id To Worker"]` (unique_id flag).

`/capabilities` (GET, no password) gives `Model` (the record's
model; e.g. SC200 per APIv2 — the dashboard's test fixtures
use arbitrary model strings, so no other model value is
asserted), `Presets` + `PresetsPowerLevels`, `Coins`, and —
v3 only — `Display`, `"Tune Presets"`, `"Temp Sensor Info"`,
`"Psu Info"`. The fetch reads it once per miner; a failure
there degrades the model to the family label "Epic" and
leaves presets/coins unknown — never a failed record.

v3-only GETs (APIv3, OFFICIAL-DOC): `/hashrate` (per-chip
hashrate), `/temps`, `/voltages`, `/history` (15-min samples,
48 h). `/history` is not wired (no BeeSky concept consumes
it); `/hashrate` is a chip-count candidate, see U-E5.

## §4 Controls — exact params (CODE where stated)

POST body is always `{"param": ..., "password": ...}`; success
is `"result": true`. Password rule (D-E5): the winning
epic-tagged credential set's password, else the factory
default `"letmein"` — the README documents it as the default
for ALL miners ("By default all of the miners have a
password of **letmein**"), so this is a documented default,
not a guess. Reads need no password.

Wired into `actions.execute` (family `epic`):

  * `reboot` → POST `/reboot` `{"param": 0}` — uint delay,
    0 = instant (DOC + CODE, app.jsx `/reboot` case).
  * `restart_mining` → POST `/softreboot` `{"param": 0}` —
    restarts only the mining program (DOC + CODE).
  * `pause_mining` → POST `/miner` `{"param": "stop"}` —
    CODE only: `ControlTab.jsx` initialises `cmd: 'stop'`
    and its only `/miner` button is "Stop Mining".
  * `find_miner` → POST `/identify` `{"param": true}` —
    LED on (DOC + CODE; the dashboard toggles with the
    current `Misc["Locate Miner State"]`, BeeSky turns it
    on — the only direction a find action needs).
  * `switch_pool` → POST `/coin` — the dashboard-faithful
    body (CODE, app.jsx `/coin` case): `param` is
    `{coin, stratum_configs: [{pool, login, password}],
    pool_url, login, unique_id}` where `login` is the
    `address.worker` string and `pool_url`/`login` repeat
    slot 0. The doc's format omits `pool_url`/`login`
    (divergence D-E1 — the doc is incomplete, the code is
    the shipped behaviour). BeeSky reads the current
    `/summary` first (coin + existing configs + unique_id),
    replaces slot `pool_id` (default 0), re-sends the rest
    unchanged. Max 3 configs (doc).
  * `set_preset` → POST `/mode` — `param` is
    `{preset, power_target}` when a power target is given,
    else the preset string alone (DOC + CODE, app.jsx
    `/mode` case). Preset must come from `/capabilities`.
  * `change_password` → POST `/password` — `param` is the
    new password, `password` the old one (DOC + CODE).
    The old password is the winning set's (same rule as
    dashd's change_password); with no set it is "letmein"
    per D-E5.
  * `set_power_target` (epic-only action name) → POST
    `/power` `{"param": <uint watts>}` — DOC only; the
    dashboard never sends `/power` (no case in its switch),
    so this is OFFICIAL-DOC without code corroboration.
  * `set_shutdown_temp` (epic-only) → POST `/shutdowntemp`
    `{"param": <usize °C>}` — DOC + CODE (app.jsx case;
    doc default 85 °C).
  * `tune` (epic-only) → POST `/tune` — `param` is
    `{"clks": "<MHz>", "voltage": "<mV>"}` as STRINGS
    (CODE, app.jsx `/tune` case: `clks:
    data.clock.toString()`, `voltage:
    (data.voltage * 1000).toString()`). The doc's
    `<string>` placeholders are pinned by this code;
    `apiCompatibility.buildPerformancePresetAction`
    sends `{clock, voltage}` as data, which the same
    `/tune` case converts — consistent. Clocks are
    capped by the miner at 1000 MHz / 15 V (doc).

NOT wired (named, with the reason):

  * `resume_mining` — the `/miner` "start" value is UNKNOWN
    (U-E3): the doc says "Autostart or stop the mining
    program" but no value is evidenced anywhere in the
    dashboard (only `'stop'` ever appears). Use
    `restart_mining` (`/softreboot`) to get a stopped
    miner hashing again.
  * `/tune/voltage`, `/tune/clock/all` — param `<string>`
    with no verified format (U-E4): no dashboard usage,
    no example. Not implemented.
  * `/fanspeed` auto form — `param: {Auto: {"Target
    Temperature": t, "Idle Speed": s}}` (CODE, FanTab)
    is recorded but not wired: BeeSky has no auto-fan
    concept. Manual `/fanspeed` IS wired as an epic-only
    action (`set_fan_speed`, param = speed): divergence
    D-E2 — the doc says "Provide a string from 1-100"
    while the dashboard sends a NUMBER (FanTab state is
    `Number(...)`); the shipped client wins, so BeeSky
    sends an int 1–100.
  * `/network` — param `"dhcp"` or `{"static": {...}}`
    (DOC with real examples) — not wired: network
    reconfiguration is safety scope (same rule as
    v0.29's configure-network gap).
  * `/systemupdate` — multipart firmware upload — not
    wired: firmware scope.
  * `/defaultconfig` — `param: null` factory reset (CODE)
    — not wired: destructive scope.
  * `/hwconfig` — `param: true` recalibrate (DOC + CODE)
    — recorded, not wired into ops (no BeeSky task type
    for it; recalibration is a 15-minute operation).
  * `/clearhashrate` — `param: null` (DOC) — not wired:
    no BeeSky concept.
  * `/debug`, `/log` — GET endpoints, no BeeSky concept.

## §5 Record shape + divergences

  * Native rate is MH/s (`Session["Average MHs"]`,
    v0.20 discipline); `ghs_5s` = LastAverageMHs/1000,
    `ghs_av` = Average MHs/1000.
  * Chips: 0/0 — the API reports no chip counts
    (Whatsminer G-W2 precedent). `/hashrate` (v3) is
    the candidate source, see U-E5. Boards still
    report per-board temp + power from `HBs[]`.
  * Fans: `fans_rpm` is EMPTY — the API reports one
    speed percentage, and putting a % into an rpm
    field would corrupt it. The percentage rides the
    record as `fan_speed_pct` (int); the inspect Fans
    section says so explicitly instead of pretending.
  * Pools: `StratumConfigs[]` → `[{url, worker,
    status}]`; `status` is "Alive" only for the current
    pool while `IsPoolConnected` is true — the API
    carries no per-pool liveness, so standby pools
    read "Dead" by this rule (divergence D-E4, stated
    on the record's face in the mapping, not hidden).
    Per-pool accepted/rejected are not in the API;
    the totals ride the record as `accepted` /
    `rejected` extra keys.
  * `HBStatus`: the `/summary` doc does not list it,
    but `boardControl.mjs` reads `summary.HBStatus`
    (per-board enabled state) — code-corroborated;
    carried on the record as `hb_status` when present,
    never invented when absent.
  * Over-temp: the shared 85 °C rule (`report.py`)
    applies to `HBs[].Temperature` — and 85 °C is also
    the miner's own documented default shutdown
    temperature, so the two agree.
  * D-E3 (OpenAPI gating): the dashboard fetches
    `/openapi.json` per miner and refuses POSTs the
    miner does not advertise (`minerHttp.mjs`).
    BeeSky does NOT gate: v2 miners do not publish
    the document, and the dashboard's own comment says
    "the actual request remains the source of truth"
    for older APIs. A refused POST surfaces verbatim.

## §6 UNKNOWNs

  * U-E1 — the exact canonical `/summary` payload bytes:
    the docs show shapes with `<placeholders>`, no real
    example reply. The mock is built from the doc shapes
    + the dashboard's field usage; a real reply is the
    one-datum close.
  * U-E2 — model strings beyond SC200: `/capabilities`
    `Model` is free-form; only SC200 is documented.
    PowerPlay model names are unknown.
  * U-E3 — `/miner` "start" value (see §4): resume not
    implemented.
  * U-E4 — `/tune/voltage` and `/tune/clock/all` param
    formats (see §4): not implemented.
  * U-E5 — `/hashrate` as a chip-count source: the doc
    says "hashrate per chip", so `len(Data)` per board
    is a candidate chip count, but the three floats per
    chip are undocumented and the endpoint is v3-only.
    Chips stay 0/0 until a real reply is seen.
  * U-E6 — whether v2 (SC200) miners serve `/hashrate`,
    `/temps`, `/voltages` at all: the docs list them
    under APIv3 only. The fetch never calls them.

## §7 Scoreboard

Real read adapters: 10 of HashCore's 15–16 (cgminer-generic,
dashd for hashcore+oldVnish, bitmain stock, canaan, microBt,
braiins, iceriver, luxos, **epic**). Jasminer remains the
only cred-tag-only family.
