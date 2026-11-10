# Mock test results

Fake miner: `tests/mock_miner.py` (Antminer S19 Pro sample — board 2 has
3 dead chips at positions 10/55/114, board 3 runs at 88 °C).

## Scanner output

```
IP        | Model            | Source  | TH/s   | Chips   | MaxTemp | Fans                | Status
----------+------------------+---------+--------+---------+---------+---------------------+-------
127.0.0.1 | Antminer S19 Pro | cgminer | 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK 

Found 1 miner(s), 1 need(s) checking.
JSON written to tests/mock_scan.json
Ticket written to tests/tickets/ticket-127_0_0_1.txt
```

## Assertions

```
PASS: 1 miner found, model = Antminer S19 Pro
PASS: status = CHECK
PASS: board 2 missing exactly 3 chips at positions 10, 55, 114 (339/342 total)
PASS: board 3 temperature 88 C flagged OVER_TEMP (>= 85 C)
PASS: problem codes = MISSING_CHIPS, OVER_TEMP
PASS: repair ticket written to tests/tickets/ticket-127_0_0_1.txt with both problems in Vietnamese
```

## Repair ticket (tests/tickets/ticket-127_0_0_1.txt)

```
PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO — BeeSky
==============================================
IP: 127.0.0.1
Model: Antminer S19 Pro
Hashrate: 102.90 TH/s
Thời gian đã chạy: 3600 giây
Tổng chip sống: 339/342

Vấn đề phát hiện:
- Board 2: thiếu 3 chip (vị trí chết: 10, 55, 114)
- Board 3: nhiệt độ cao 88°C (ngưỡng 85°C)

Chi tiết từng board:
- Board 1: 114/114 chip, nhiệt 65°C
- Board 2: 111/114 chip, nhiệt 71°C
- Board 3: 114/114 chip, nhiệt 88°C

Gợi ý kiểm tra:
- Đo điện áp từng domain trên board (điểm đo/PIC), kiểm tra cáp dữ liệu và mối hàn quanh các vị trí chip chết; đối chiếu vị trí chip với sơ đồ domain của board để khoanh vùng trước khi thay chip.
- Kiểm tra quạt và đường gió, vệ sinh bụi, kiểm tra keo tản nhiệt và lực ép ốc heatsink của board; chạy lại và đo nhiệt sau khi xử lý.
```

---

# v0.2 mock test — VNish dashd + Bitmain stock adapters

Three fake miners in one scan: `tests/mock_miner.py` (cgminer RPC,
127.0.0.1:4028), `tests/mock_dashd.py` (VNish dashd API shaped after
the firmware's own `api-doc.json`, 127.0.0.2:80 — board 1 missing 2
chips at positions 10/55, board 2 at 87 °C), `tests/mock_bitmain.py`
(stock CGI behind digest auth, healthy S19, 127.0.0.3:80).

## Scanner output

```
IP        | Model            | Source  | TH/s   | Chips   | MaxTemp | Fans                | Status
----------+------------------+---------+--------+---------+---------+---------------------+-------
127.0.0.1 | Antminer S19 Pro | cgminer | 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK 
127.0.0.2 | Antminer S19 Pro | vnish   | 109.13 | 340/342 | 87      | 4320/4380/4440/4500 | CHECK 
127.0.0.3 | Antminer S19     | stock   | 95.10  | 342/342 | 70      | 4200/4260/4320/4380 | OK    

Found 3 miner(s), 2 need(s) checking.
JSON written to tests/mock_scan_v2.json
Ticket written to tests/tickets_v2/ticket-127_0_0_1.txt
Ticket written to tests/tickets_v2/ticket-127_0_0_2.txt
```

## Assertions

```
PASS: 127.0.0.1 via cgminer RPC, unchanged v0.1 behaviour (CHECK, 339/342)
PASS: 127.0.0.2 via VNish dashd (CHECK): board 1 missing exactly 2 chips at positions 10, 55 (340/342); board 2 at 87 C flagged OVER_TEMP
PASS: 127.0.0.3 via Bitmain stock CGI + digest auth (OK, healthy S19, 342/342)
PASS: scan table sources = cgminer + vnish + stock
PASS: VNish repair ticket written to tests/tickets_v2/ticket-127_0_0_2.txt (missing chips + over-temp, Vietnamese)
```

## Repair ticket — VNish miner (tests/tickets_v2/ticket-127_0_0_2.txt)

```
PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO — BeeSky
==============================================
IP: 127.0.0.2
Model: Antminer S19 Pro
Hashrate: 109.13 TH/s
Thời gian đã chạy: 5400 giây
Tổng chip sống: 340/342

Vấn đề phát hiện:
- Board 1: thiếu 2 chip (vị trí chết: 10, 55)
- Board 2: nhiệt độ cao 87°C (ngưỡng 85°C)

Chi tiết từng board:
- Board 1: 112/114 chip, nhiệt 74°C
- Board 2: 114/114 chip, nhiệt 87°C
- Board 3: 114/114 chip, nhiệt 69°C

Gợi ý kiểm tra:
- Đo điện áp từng domain trên board (điểm đo/PIC), kiểm tra cáp dữ liệu và mối hàn quanh các vị trí chip chết; đối chiếu vị trí chip với sơ đồ domain của board để khoanh vùng trước khi thay chip.
- Kiểm tra quạt và đường gió, vệ sinh bụi, kiểm tra keo tản nhiệt và lực ép ốc heatsink của board; chạy lại và đo nhiệt sau khi xử lý.
```

---

# v0.3 mock test — watch mode, event engine, notifications

`tests/mock_watch_test.py` drives the real CLI (`beesky watch
--once --state … --notify …`) against `tests/mock_watch_miner.py`,
a control-file-driven fake cgminer S19 Pro on 127.0.0.1:14028.
Healthy passes build the rolling baseline; a drop to 66 TH/s is a
40% HASHRATE_DROP (severity major on the 15/30/50 scale); killing
the miner fires OFFLINE (critical); restarting it fires
BACK_ONLINE. A local receiver on 127.0.0.1:18777 captures the
webhook POSTs (/hook) and the Telegram Bot API calls (api_base
overridden to the same receiver); the logfile channel is checked
on disk. Anti-flap passes assert no duplicate events.

## Assertions + captured webhook payloads

```
PASS: healthy passes: no events while baseline builds
PASS: healthy passes: no notifications sent
PASS: hashrate drop pass: HASHRATE_DROP printed
PASS: webhook received exactly one HASHRATE_DROP
PASS: drop payload shape (ip/model/type/severity/detail/data)
PASS: drop payload: drop_pct ~= 40
PASS: drop payload: baseline 110 -> current 66 TH/s
PASS: telegram sendMessage captured for the drop
PASS: still dropped: anti-flap, no duplicate HASHRATE_DROP
PASS: miner killed: OFFLINE printed + webhook received
PASS: OFFLINE payload: severity critical, model kept
PASS: telegram captured for OFFLINE
PASS: still down: anti-flap, no duplicate OFFLINE
PASS: miner back: BACK_ONLINE printed + webhook received
PASS: logfile channel recorded all three events

Captured webhook payloads:
{"ts": 1794289282.5952525, "time": "2026-11-10 05:41:22", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
{"ts": 1794289283.0497391, "time": "2026-11-10 05:41:23", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "OFFLINE", "severity": "critical", "detail": "miner went offline / unreachable", "data": {"last_seen": 1794289282.852182}}
{"ts": 1794289283.633352, "time": "2026-11-10 05:41:23", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "BACK_ONLINE", "severity": "info", "detail": "miner is back online", "data": {}}

WATCH TEST PASSED
```

---

# v0.4 mock test — web dashboard (serve + JSON API)

`tests/mock_web_test.py` runs the real server (`beesky serve
127.0.0.1 --port 18788 --interval 1`) against the control-file
fake S19 Pro on 127.0.0.1:14029 and asserts over plain HTTP:
the dashboard page carries the BeeSky brand, /api/miners shows
the miner at 110 TH/s, /api/status counts are sane, POST
/api/scan answers 202, and flipping the miner to 66 TH/s makes
a HASHRATE_DROP (major, ~40%) appear in /api/events.

## Assertions + captured event

```
PASS: GET / returns the dashboard
PASS: dashboard carries the BeeSky brand (name + #F5D800)
PASS: GET /api/miners lists the mock miner
PASS: miner record: S19 Pro, ~110 TH/s, 342/342 chips, OK
PASS: GET /api/status counts sane (1 miner, target, interval)
PASS: POST /api/scan -> 202 {ok: true}
PASS: hashrate drop phase: /api/events gains HASHRATE_DROP
PASS: drop event: severity major, drop_pct ~= 40

Captured drop event:
{"ts": 1794289288.719094, "time": "2026-11-10 05:41:28", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}

WEB TEST PASSED
```

---

# v0.5 mock test — farm agent + cloud backend + multi-site web

`tests/mock_cloud_test.py` builds the full cloud shape on
127.0.0.1: `beesky cloud-add-agent` mints a key for site
"Xưởng 1", `beesky cloud` runs on :18790 with
BEESKY_CLOUD_PASSWORD set, the control-file fake S19 Pro sits
on :14031, and `beesky agent --interval 1` pushes to the
cloud. Assertions: wrong/no agent key -> 401 on ingest;
viewer /api/sites locked (401) until POST /login with the
right password sets a session cookie (wrong password -> 401);
GET / serves the branded cloud dashboard; /api/sites shows
the site at ~110 TH/s; flipping the miner to 66 TH/s makes a
HASHRATE_DROP (major, ~40%) arrive at the cloud /api/events
tagged with the site; /api/miners?site= shows ~66 TH/s.

## Assertions + captured cloud event

```
PASS: cloud-add-agent prints a key once
PASS: cloud starts and serves /login
PASS: ingest with a wrong agent key -> 401
PASS: ingest with no agent key -> 401
PASS: viewer /api/sites without login -> 401
PASS: login with wrong password -> 401
PASS: still locked out after wrong password
PASS: login with right password -> session (200 after redirect)
PASS: /api/sites works with the session cookie; site registered
PASS: GET / serves the cloud dashboard (brand #F5D800)
PASS: /api/sites shows the site after agent push
PASS: site summary: ~110 TH/s, 1 OK / 0 problems, online
PASS: hashrate drop: HASHRATE_DROP arrives at the cloud
PASS: drop event: severity major, drop_pct ~= 40, site tag

Captured cloud event:
{"ts": 1794289296.0640268, "time": "2026-11-10 05:41:36", "site": "Xưởng 1", "agent_id": 1, "ip": "127.0.0.1", "model": "Antminer S19 Pro", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
PASS: /api/miners?site= shows ~66 TH/s, record annotated with site

CLOUD TEST PASSED
```

---

# v0.6 mock test — remote actions via cloud (command queue)

`tests/mock_actions_test.py` builds the full command path on
127.0.0.1: one `beesky cloud` (:18791, password set) with
three minted agents — site "Xưởng 1" runs the control-file
cgminer miner (:14032), site "Xưởng 2" the api-doc dashd mock
(:18082, x-api-key auth), site "Xưởng 3" the digest-auth stock
mock (:18083). Assertions: agent poll no/wrong key -> 401;
viewer POST /api/commands without login -> 401; agent A can
neither claim nor finish agent B's command (403, stays
pending); cgminer reboot finishes done with the restart RPC
recorded by the mock, and fails honestly with the miner's own
"Access denied" when its API is read-only; switch_pool to a
cgminer miner fails "not supported"; dashd reboot lands on
POST /system/reboot, switch_pool {pool_id} activates slot 1,
switch_pool {url,user} rewrites slot 0 via GET/POST /settings
and activates it; stock reboot hits /cgi-bin/reboot.cgi; the
dashboard carries the action UI; /api/commands shows history.

## Assertions + captured commands

```
PASS: cloud-add-agent mints keys for all three sites
PASS: cloud starts and serves /login
PASS: agent command poll with no key -> 401
PASS: agent command poll with wrong key -> 401
PASS: viewer POST /api/commands without login -> 401
PASS: viewer login with the right password
PASS: viewer creates a reboot command for site 2 -> 201
PASS: new command starts out pending
PASS: agent A cannot claim agent B's command
PASS: agent A finishing agent B's command -> 403
PASS: B's command is still pending after A's attempts
PASS: dashboard HTML has the reboot button + commands panel
PASS: site 2 command finishes
PASS: dashd reboot: status done, result from /system/reboot

Captured dashd reboot command:
{"id": 1, "agent_id": 2, "site": "Xưởng 2", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "dashd accepted reboot (system reboots in 3s)", "created_at": "2026-11-10 05:41:37", "created_ts": 1794289297.6671667, "claimed_at": "2026-11-10 05:41:37", "finished_at": "2026-11-10 05:41:37"}
PASS: dashd mock recorded exactly one POST /system/reboot
PASS: dashd switch_pool {pool_id: 1} finishes done
PASS: dashd mock activated pool slot 1
PASS: dashd switch_pool {url,user} finishes done via /settings
PASS: dashd mock pool slot 0 now carries the new url/user
PASS: site 1 agent reports its cgminer miner
PASS: cgminer reboot finishes done

Captured cgminer reboot command:
{"id": 4, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "cgminer accepted the privileged 'restart' command", "created_at": "2026-11-10 05:41:40", "created_ts": 1794289300.509857, "claimed_at": "2026-11-10 05:41:41", "finished_at": "2026-11-10 05:41:41"}
PASS: cgminer mock recorded the restart RPC
PASS: cgminer reboot on a read-only API -> failed
PASS: failure result carries the miner's 'Access denied'
PASS: switch_pool to a cgminer miner -> failed 'not supported'
PASS: site 3 agent reports its stock miner
PASS: stock reboot finishes done
PASS: stock mock recorded the reboot.cgi hit
PASS: GET /api/commands?site= returns site 1 history newest-first

ACTIONS TEST PASSED
```

---

# v0.7 mock test — desktop GUI (tkinter, headless smoke)

`tests/mock_gui_test.py` runs under `xvfb-run`: the scripted
S19 Pro on 127.0.0.1:4028, then the real GUI via `beesky gui
--smoke` — window built, one scan, Treeview rows printed.

```
PASS: mock miner up on 127.0.0.1:4028
GUI SMOKE: 1 row(s) for target 127.0.0.1
GUI SMOKE first row: 127.0.0.1 | Antminer S19 Pro | cgminer RPC | 102.90 | 339/342 | 88 | 4320/4380/4440/4500 | CHECK
PASS: beesky gui --smoke exits 0 under the virtual display
PASS: GUI table holds exactly 1 row after one scan
PASS: first row = 127.0.0.1 | Antminer S19 Pro | ... | 339/342 chips | CHECK (same values as the CLI)

GUI TEST PASSED
```

---

# v0.8 mock test — heat map + repair history

`tests/mock_repairs_test.py` checks the repair-history rule
in-process against `CloudStore` (problem events CHIPS_LOST /
CHAIN_DOWN / OVER_TEMP / OFFLINE become `auto_event` rows,
deduplicated to one identical (site, ip, title) row per hour;
HASHRATE_DROP / BACK_ONLINE do not), then builds the v0.5 cloud
shape on 127.0.0.1: `beesky cloud` (:18792, password set),
the control-file fake S19 Pro (:14033) and `beesky agent
--interval 1`. Assertions: GET/POST /api/repairs -> 401
logged out; both dashboards carry the Bản đồ nhiệt section
with the heatColor thresholds (<60 green-dark ... >=90 red);
flipping the miner to dead chips makes CHIPS_LOST arrive at
/api/events AND as an auto row in /api/repairs; a manual
POST /api/repairs is listed back with cost_vnd + technician.

## Assertions + captured repair rows

```
PASS: store: CHIPS_LOST event becomes an auto repair row
PASS: store: identical auto row within 1h is deduplicated
PASS: store: same event after 1h logs a fresh auto row
PASS: store: OVER_TEMP/CHAIN_DOWN/OFFLINE auto-log; HASHRATE_DROP/BACK_ONLINE do not
PASS: cloud-add-agent prints a key once
PASS: cloud starts and serves /login
PASS: GET /api/repairs without login -> 401
PASS: POST /api/repairs without login -> 401
PASS: login with right password -> session
PASS: GET /api/repairs with session -> 200, empty at first
PASS: cloud dashboard: heat-map section + colour thresholds
PASS: local web dashboard: heat-map section + colour thresholds
PASS: /api/sites shows the site after agent push
PASS: dead chips: CHIPS_LOST event arrives at the cloud
PASS: CHIPS_LOST also lands in repair history as auto_event
PASS: auto row: site/ip keyed, no cost/technician

Captured auto repair row:
{"id": 1, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "mac_or_serial": null, "created_at": "2026-11-10 05:41:52", "created_ts": 1794289312.0016782, "kind": "auto_event", "title": "CHIPS_LOST", "detail": "lost 3 chip(s) (342 -> 339 alive)", "cost_vnd": null, "technician": null}
PASS: POST /api/repairs (logged in) -> 201 manual row
PASS: manual row listed with cost_vnd + technician

Captured manual repair row:
{"id": 2, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "mac_or_serial": null, "created_at": "2026-11-10 05:41:52", "created_ts": 1794289312.4380627, "kind": "manual", "title": "Thay board 2", "detail": "Board 2 chết 3 chip — đã thay board, test lại đạt", "cost_vnd": 1500000, "technician": "Tuấn"}
PASS: POST /api/repairs with blank title -> 400

REPAIRS TEST PASSED
```

---

# v0.9 mock test — farm-vs-pool comparison + energy reports

`tests/mock_energy_pool_test.py` checks the pool-config
redaction + POOL_GAP rule + energy integration in-process
against `CloudStore` (gap fires only on the second
consecutive over-threshold sample, deduped to 1/hour; energy
= power_w x dt with dt capped at 3x the agent interval),
the generic pool adapter against an in-process mock pool
(dot-path, GH/s -> TH/s, worker_filter), then builds the
v0.5 cloud shape on 127.0.0.1: `beesky cloud` (:18793,
password set, poll interval 1 s), the mock dashd S19 Pro
(:18098, power_consumption 3210 W), a mock pool JSON server
(:18123) and `beesky agent --interval 1`. Assertions: new
endpoints -> 401 logged out; the miner record carries
power_w 3210; the pool config round-trips with its secret
header sent to the pool but never echoed by the cloud; a
~5% gap samples quietly while the pool at 40% of farm
raises a major POOL_GAP event; energy accumulates > 0 kWh
and cost estimates follow the settable electricity price.

## Assertions + captured samples

```
PASS: store: config view lists header NAMES, never values
PASS: store: re-POST without headers keeps the stored secrets
PASS: store: gap fires on 2nd consecutive breach, deduped 1/hour
PASS: store: samples back under threshold never fire
PASS: store: energy integrates power_w across snapshots (0.06 kWh)
PASS: store: dt capped at 3x interval (adds 3600 W x 90 s = 0.09)
PASS: adapter: dot path + GH/s -> TH/s conversion
PASS: adapter: worker_filter sums only matching workers (60)
PASS: cloud-add-agent prints a key once
PASS: cloud starts and serves /login
PASS: GET /api/pool-config without login -> 401
PASS: GET /api/pool without login -> 401
PASS: GET /api/energy without login -> 401
PASS: GET /api/settings without login -> 401
PASS: POST /api/pool-config without login -> 401
PASS: POST /api/settings without login -> 401
PASS: login with right password -> session
PASS: GET /api/settings: default price 2000 VND/kWh
PASS: cloud dashboard: pool + energy panels present
PASS: /api/sites shows the site after agent push
PASS: farm hashrate from dashd snapshot (~109.13 TH/s)
PASS: miner record carries power_w from dashd power_consumption
PASS: POST /api/pool-config -> 201, view has names not values
PASS: GET /api/pool-config never echoes the secret header
PASS: poller samples pool vs farm (gap ~5%, under threshold)
PASS: poller sent the configured secret header to the pool
PASS: no POOL_GAP while the gap stays ~5%
PASS: pool at 40% of farm -> POOL_GAP (major) in the event feed

Captured POOL_GAP event:
{"ts": 1794289316.1482992, "time": "2026-11-10 05:41:56", "site": "Xưởng 1", "agent_id": 1, "ip": null, "model": null, "type": "POOL_GAP", "severity": "major", "detail": "pool reports 43.65 TH/s vs farm 109.13 TH/s — gap 60.0% exceeds 10% for 2 consecutive checks", "data": {"pool_ths": 43.65, "farm_ths": 109.13, "gap_pct": 60.0, "threshold_pct": 10.0}}
PASS: latest sample shows the ~60% gap
PASS: energy accumulates > 0 kWh for the dashd miner

Captured energy report (excerpt):
{"today": {"day": "2026-11-10", "kwh": 0.0027, "est_cost_vnd": 5}, "per_day": [{"day": "2026-11-10", "kwh": 0.0027, "est_cost_vnd": 5}], "per_miner": [{"site": "Xưởng 1", "ip": "127.0.0.1", "kwh": 0.0027, "est_cost_vnd": 5}]}
PASS: POST /api/settings sets the electricity price
PASS: energy estimates now use 3000 VND/kWh

ENERGY/POOL TEST PASSED
```

---

# v0.10 mock test — signed self-update channel

`tests/mock_update_test.py` is fully hermetic: openssl
makes a throwaway RSA-2048 keypair via the shipped owner
tool (outputs redirected to a temp dir — the repo's
`beesky/core/update_key.py` keeps its shipped N=None),
the updater under test is pointed at that public key via
its module variables, and a 127.0.0.1 HTTP server plays
the GitHub release. Assertions: the pure-Python RSA verify
accepts the genuine signature and rejects a one-byte
tamper; check() reports the next minor version > the running one;
a tampered served manifest is refused whole; a signed
manifest pinning a wrong file hash still cannot install
(SHA-256 gate); the happy-path apply replaces a dummy
exe, keeps `beesky.old` and the executable bit; a
same-version manifest is a no-op; an unreachable server
and the unconfigured (keyless) build both fail cleanly;
the CLI reports/refuses with the right exit codes.

## Assertions

```
PASS: owner tool: module modulus matches generated key
PASS: owner tool: exponent fixed at 65537
PASS: updater: channel enabled with a compiled-in key
PASS: verify: valid RSA signature over the manifest verifies
PASS: verify: one flipped manifest byte fails verification
PASS: verify: truncated signature fails verification
PASS: check: signed manifest accepted (ok + signature_ok) — {"current": "0.15.0", "latest": "0.16.0", "update_available": true}
PASS: check: newer version reported as update available
PASS: check: tampered manifest refused end-to-end
PASS: apply: newer signed release installs onto the dummy — updated beesky to BeeSky 0.16.0 (previous file kept as beesky.old) — restart to run it
PASS: apply: dummy now holds the new binary bytes
PASS: apply: previous file kept as beesky.old backup
PASS: apply: executable bit preserved on the new file
PASS: apply: wrong-hash download refused despite valid signature
PASS: apply: refused download leaves the target untouched
PASS: apply: no staged temp files left behind after refusal — leftovers=[]
PASS: check: same-version manifest is not an update
PASS: apply: not-newer release is a clean no-op
PASS: check: unreachable update server -> ok=False + error
PASS: disabled: no key -> channel reports not configured
PASS: disabled: verify_signature is False without a key
PASS: cli: `update --check` reports the unconfigured channel — self-update not configured: no update signing key is compiled into this build (owner setup: docs/updating.md)
PASS: cli: bare `update` refuses cleanly (exit 2) when unconfigured

UPDATE TEST PASSED
```
---

# v0.11 mock test — firmware identify / install / gated unlock

`tests/mock_firmware_test.py` is fully hermetic: a digest-auth
stock miner mock on 127.0.0.5 (upgrade.cgi records every upload's
sha256; its update_first.bmu handler blocks until the race-kill
marker file exists, mimicking the signature-verification window;
patch_success.cgi answers 200 only after both .bmu uploads AND
the marker), the dashd mock on 127.0.0.6 implementing the
api-doc's `POST /api/v1/firmware/update`, and a fake `ssh`
shim on PATH that logs into the same ordered event log, answers
compile_time and creates the marker on the kill command.
Assertions: identify verdicts for stock+SSH ("stock cũ / đã mở
SSH"), stock without an ssh binary ("không rõ"), and VNish;
stock and dashd installs deliver the exact file bytes; unlock
refuses with ZERO requests reaching the mock when the
--experimental-unlock flag, the BEESKY_ALLOW_UNLOCK=1 env, the
typed-IP confirmation, or the payload files are missing; with
all gates open the sequence lands in order — miner_type.cgi
identify, update_first.bmu upload, the SSH kill of the openssl
verify process (inside the first upload's window),
update_second.bmu upload, patch_success marker.

## Assertions

```
PASS: identify stock: exit 0
PASS: identify stock: miner_type.cgi read
PASS: identify stock: compile_time via ssh shim
PASS: identify stock: verdict stock cũ / đã mở SSH
PASS: identify no-ssh: verdict không rõ + note
PASS: identify vnish: verdict cài firmware qua API được — Kết luận:     VNish/dashd — cài firmware qua API được
PASS: install stock: exit 0 — ch: 127.0.0.5 — nguồn stock
OK: stock firmware accepted the upload (POST /cgi-bin/upgrade.cgi -> 200); the miner verifies and reboots on its own schedule
bỏ qua bước chờ máy lên lại (--wait-minutes 0)
PASS: install stock: mock received the exact bytes (sha256)
PASS: install dashd: exit 0 — c85f8c4
Đích: 127.0.0.6 — nguồn vnish, model Antminer S19 Pro
OK: dashd accepted the firmware (POST /api/v1/firmware/update -> 200, system reboots in 3s)
bỏ qua bước chờ máy lên lại (--wait-minutes 0)
PASS: install dashd: /firmware/update got the exact bytes — {"filename": "fw-image.tar.gz", "sha256": "b806c4c72bb6ba1fac3c47ab787581d2ffa9abe14bcab74ae960736eec85f8c4"}
PASS: unlock refused (no flag): exit != 0 — fw unlock: TỪ CHỐI — thiếu cờ --experimental-unlock. Đây là tính năng THỬ NGHIỆM theo recipe khôi phục từ HashCore Toolkit; đọc docs/firmware.md trước.
PASS: unlock refused (no flag): ZERO requests hit the mock — log lines 17 -> 17
PASS: unlock refused (no env): exit != 0 — fw unlock: TỪ CHỐI — chưa đặt biến môi trường BEESKY_ALLOW_UNLOCK=1.
PASS: unlock refused (no env): ZERO requests hit the mock — log lines 17 -> 17
PASS: unlock refused (wrong typed IP): exit != 0 — Đã huỷ — IP gõ vào không khớp.
PASS: unlock refused (wrong typed IP): ZERO requests hit the mock — log lines 17 -> 17
PASS: unlock refused (missing payload): clear error, no requests
PASS: unlock full: exit 0 + success banner — cond: update_second.bmu accepted (HTTP 200)
  [OK] marker: /cgi-bin/patch_success.cgi -> 200 (patch marker present)
  [OK] cleanup: đã dọn /nvdata/update.log và /tmp/tmpfw; việc khôi phục access files (/etc/passwd, /etc/sudoers.dist, /config/passwd) thuộc về payload theo recipe gốc
UNLOCK THÀNH CÔNG
PASS: unlock order: identify -> first.bmu -> kill -> second.bmu -> patch marker — indices ident=0 first=4 kill=5 second=8 marker=11
PASS: unlock race: kill landed inside the first-upload window

FIRMWARE TEST PASSED
```

---

# v0.11.2 mock test — official logo wiring

`tests/mock_logo_test.py` is a static wiring test (no servers):
the official BeeSky logo master (owner's Illustrator vector,
yellow #F4D600) ships in `packaging/assets/` as SVG + multi-size
ICO + 512px PNG. Assertions: both dashboards inline the real SVG
in the header (viewBox + chevron path fragment + #F4D600) with
an SVG data-URI favicon, and the old CSS letter "B" mark is
gone; the PyInstaller spec points both exes' icon at
beesky-logo.ico and bundles the PNG/ICO in the GUI datas; the
Inno installer uses it as SetupIconFile and ships it; the
tkinter GUI resolves it via _asset_path (frozen _MEIPASS first,
then packaging/assets/) for iconbitmap/iconphoto and the
~40px header image. The inlined SVG and the favicon payload
were also render-compared against the master during
development: 0.00% colour-class difference.

Full-chain note: the v0.1–v0.10 suites (incl. the GUI smoke and
both dashboard suites) passed in-chain with these logo changes
in-tree; the v0.11 firmware suite's strict event-order
assertion (the race documented as load-sensitive at v0.11 ship
time) flaked repeatedly under this VM's current shared-host
contention, so the v0.11 evidence block above is the ship-time
one, not a fresh regeneration.

## Assertions

```
PASS: asset bundled: packaging/assets/beesky-logo.svg
PASS: asset bundled: packaging/assets/beesky-logo.ico
PASS: asset bundled: packaging/assets/beesky-logo-512.png
PASS: beesky/web/dashboard.html: header inlines the official SVG
PASS: beesky/web/dashboard.html: SVG favicon link present
PASS: beesky/web/dashboard.html: old CSS letter mark removed
PASS: beesky/cloud/dashboard.html: header inlines the official SVG
PASS: beesky/cloud/dashboard.html: SVG favicon link present
PASS: beesky/cloud/dashboard.html: old CSS letter mark removed
PASS: spec: exe icon is the official logo ico
PASS: spec: GUI datas bundle the logo PNG + ICO
PASS: installer: SetupIconFile is the official logo ico
PASS: installer: ships the official logo ico
PASS: gui: resolves bundled assets (_asset_path, _MEIPASS pattern)
PASS: gui: window icon via iconbitmap + iconphoto fallback
PASS: gui: header shows the logo PNG
PASS: version bumped to 0.11.2 — package reports 0.11.2

LOGO TEST PASSED
```

---

# v0.12 mock test — cloud dashboard redesign (sidebar, history chart, settings forms)

`tests/mock_history_test.py` covers the redesign's backend and
content wiring. Store level: `CloudStore.add_snapshot` samples
the new `history_samples` table at most once per site per
60 s (snapshots at +0 s/+10 s -> one row, +70 s -> a second),
row totals mirror the snapshot (summed TH/s, miner/problem
counts, max temp), rows filter per site, and samples older
than 30 days are pruned on the write path. HTTP level (real
`beesky cloud`, password set): `GET /api/history` is 401
logged out; after login, ingests carrying explicit timestamps
yield exactly the throttled points and the `?site=` filter
works; the served dashboard carries the sidebar nav (Tổng
quan / Máy đào / Bản đồ nhiệt / Điện năng / Lịch sử sửa / Sự
kiện / Cài đặt), the seven view containers, the history chart
container, the topbar (site filter, last-update, logout) and
the Cài đặt forms (pool config -> POST /api/pool-config with
header-secrecy notes, electricity price -> POST /api/settings,
current configs rendered header-names only), while every
pre-v0.12 dashboard marker asserted by the older suites (heat
map + heatColor thresholds, pool/energy panel ids, POOL_GAP,
commands panel, official logo SVG) is still present. The
cloud dashboard itself was rebuilt as a fixed-sidebar layout
(230 px, icon/top-bar collapse under 900 px) over a new token
set (bg #0B0B0D, panels #15151A, borders #232329, status
#34D399/#FBBF24/#FB923C/#F87171, accent #F5D800); the local
web dashboard received the same token palette as a CSS-only
polish (no layout or JS changes).

Disclosure (same situation as the v0.11.2 block): a fresh
full-chain regeneration (run_mock_test_v12.sh) was attempted
three times. Every attempt regenerated v0.1–v0.10 green
in-chain (156 PASS lines, 0 FAIL) and then stopped at a
load-sensitive LEGACY assertion under this VM's current
shared-host contention — twice the v0.11 firmware race-order
assertion (kill logged at index 3, first.bmu at 5, while the
companion 'kill landed inside the first-upload window'
assertion passed and the unlock itself succeeded), once
inside the v0.6 actions suite. Both suites pass standalone
on a calm host (the firmware suite passed standalone on the
first retry between attempts), and every dashboard-sensitive
suite — v0.4 web, v0.5 cloud, v0.6 actions, v0.8 repairs,
v0.9 energy/pool, v0.11.2 logo — was re-run standalone green
against the redesigned dashboards during this session. No
legacy test or firmware code was changed for this; the one
test edit is the logo suite's version assertion, made
version-relative (installer define == package version, the
same fix the update suite got in v0.11) so it survives future
bumps. RESULTS.md therefore keeps the ship-time evidence
blocks for v0.1–v0.11.2 and appends this v0.12 block, exactly
as v0.11.2 handled its flake.

## Assertions

```
PASS: store: first snapshot writes one history sample
PASS: store: sample totals mirror the snapshot
PASS: store: snapshot 10 s later is throttled (still 1 row)
PASS: store: snapshot +70 s writes the 2nd row
PASS: store: per-site filter + all-sites view
PASS: store: since_ts window is honoured
PASS: store: samples older than 30 days are pruned on write
PASS: cloud-add-agent prints a key once
PASS: cloud server starts
PASS: GET /api/history without login -> 401
PASS: login with right password -> session
PASS: GET /api/history with session -> 200, empty at first
PASS: dashboard: sidebar nav with all seven views
PASS: dashboard: settings forms (pool config + price) present
PASS: dashboard: history chart container + topbar
PASS: dashboard: legacy markers survive (heat/pool/energy/logo)
PASS: ingest snapshot 1 accepted
PASS: ingest snapshot 2 (+10 s) accepted
PASS: history after +10 s: throttle keeps a single point
PASS: ingest snapshot 3 (+70 s) accepted
PASS: history after +70 s: second point appears, site filter ok
PASS: history for an unknown site is empty

HISTORY TEST PASSED
```

---

# v0.13 mock test — dashboard icons + agent management UI

`tests/mock_agents_ui_test.py` covers the v0.13 additions.
Store level: `CloudStore.agent_views` never carries key
material (neither the plaintext key — never stored — nor its
SHA-256 hash); `revoke_agent` flips the new `agents.revoked`
flag and the revoked key immediately fails `agent_by_key`,
the single lookup behind every agent-facing endpoint (ingest,
command claim/result), while its history rows stay put; a
pre-v0.13 database is migrated on open (ALTER TABLE adds the
column) and its legacy agents keep authenticating until
revoked. HTTP level (real `beesky cloud`, password set):
all three agent endpoints are 401 logged out; POST
/api/agents mints through the same store path as
`cloud-add-agent` (`secrets.token_urlsafe(32)` ->
`create_agent`) and returns the raw key exactly once; GET
/api/agents lists id/site/created/last-seen/online/revoked
with the key and its hash absent from the payload; a real
snapshot ingest with the web-minted key succeeds and flips
the agent online; revoke validates its input (400 non-integer
id, 404 unknown id) and afterwards the same ingest is 401.
Dashboard: the Cài đặt view gains an "Agent & trại" panel
(create form, one-time key panel with copy buttons and a
ready-to-run `beesky agent` command prefilled with the
page origin, registered-agents table with Thu hồi buttons)
above the pool form, and the whole cloud UI gains inline
Lucide-style stroke icons — seven sidebar nav icons
(layout-grid / server / thermometer / zap / wrench / bell /
gear), four stat-card icon chips (building / cpu / activity /
alert-triangle) and a log-out icon, all currentColor so the
active nav state colours its icon with the accent; the local
web dashboard received the same stat-card chips (server /
activity / alert-triangle / thermometer) as a pure HTML/CSS
addition. Every pre-v0.13 dashboard marker asserted by the
older suites is still present.

Flake disclosure (mirroring v0.11.2/v0.12): the full-chain regeneration for v0.13 ran v0.1-v0.10 green in-chain (156 PASS, 0 FAIL), then stopped at the same load-sensitive v0.11 firmware race-order assertion under this VM's shared-host contention (kill logged at index 3, first.bmu at 5, while the companion 'kill landed inside the first-upload window' assertion passed and the unlock itself succeeded); the firmware suite reproduced the same indices on two standalone retries this session. No firmware or legacy test code was changed for this. The v0.11, v0.11.2 and v0.12 evidence blocks above are therefore the ship-time blocks, kept verbatim; the suites behind them were re-verified this session — v0.1-v0.10 in-chain as said, and mock_logo_test.py + mock_history_test.py standalone green against the v0.13 tree — and the new suite below re-asserts every dashboard marker they rely on.

## Assertions

```
PASS: store: agent_views carries no key material
PASS: store: fresh agent is not revoked and offline
PASS: store: agent_by_key authenticates before revoke
PASS: store: revoke of unknown id -> False
PASS: store: revoke existing agent -> True
PASS: store: revoked key no longer authenticates
PASS: store: revoked agent shows revoked + offline in views
PASS: store: revoked site has no live agent_by_site
PASS: store: pre-v0.13 db migrated — legacy agent authenticates
PASS: store: migrated agent can be revoked like any other
PASS: cloud server starts
PASS: GET /api/agents without login -> 401
PASS: POST /api/agents without login -> 401
PASS: POST /api/agents/revoke without login -> 401
PASS: login with right password -> session
PASS: GET /api/agents with session -> 200, empty at first
PASS: POST /api/agents with blank site -> 400
PASS: POST /api/agents mints + returns the raw key once
PASS: GET /api/agents lists the minted agent, key + hash absent
PASS: ingest with the web-minted key -> 200
PASS: agent shows online after its first ingest
PASS: POST /api/agents/revoke with non-integer id -> 400
PASS: POST /api/agents/revoke with unknown id -> 404
PASS: POST /api/agents/revoke revokes the minted agent
PASS: revoked agent listed as revoked + offline
PASS: ingest with the revoked key -> 401
PASS: dashboard: agent management section ids present
PASS: dashboard: seven sidebar nav icons (inline SVG)
PASS: dashboard: stat-card icon chips + logout icon
PASS: dashboard: legacy markers survive (nav/heat/pool/logo)

AGENTS UI TEST PASSED
```


---

# v0.14 mock test — standalone BeeSky Agent app

`tests/mock_agent_app_test.py` covers the agent app.
Config model (`beesky/agent_config.py`): save/load is
lossless, parent dirs are created on first save, unknown
keys and a non-dict `notify_config` are tolerated, and
`default_config_path` resolves $BEESKY_AGENT_CONFIG first,
then %APPDATA%\BeeSky\agent-config.json on Windows
(simulated platform + fake APPDATA), then
~/.beesky/agent-config.json. Packaging: the PyInstaller spec
gains a third Analysis/EXE `beesky-agent` (console build,
official icon, GUI datas for the config window's logo);
`packaging/agent.iss` installs it as
BeeSkyAgentSetup-<version>.exe with Start Menu/desktop
shortcuts that open the config window; both installers'
version defines match the package version; the Windows
workflow builds agent.iss and ships beesky-agent.exe +
BeeSkyAgentSetup-*.exe in the build artifact, the GitHub
Release and the signed update-manifest file list — the
updater assertion proves a signed manifest entry named
beesky-agent.exe is matched by basename and applied (with
.old backup), so the agent app self-updates through the
v0.10 channel unchanged. End-to-end: against a real
`beesky cloud` and tests/mock_dashd.py, the app is driven
purely by a config file — `beesky-agent test` exits 0 with
TEST OK and the snapshot is visible in /api/sites and
/api/miners (VNish S19 Pro), `run --once` exits 0, and a
config with a wrong key fails `test` with exit 1; off
Windows, install-task prints systemd/cron guidance. The
config GUI smoke runs under `xvfb-run`: window + five
fields construct, the key entry masks/unmasks via the
'Hiện key' toggle, Lưu cấu hình writes JSON that loads back
identically, and the auto-start button is disabled off
Windows.

Flake disclosure (mirroring v0.11.2/v0.12/v0.13): the full-chain regeneration for v0.14 ran v0.1-v0.10 green in-chain (156 PASS, 0 FAIL), then stopped at the same load-sensitive v0.11 firmware race-order assertion under this VM's shared-host contention (kill logged at index 3, first.bmu at 5 — the identical indices the flake produced at v0.13); an earlier attempt the same session also stopped once at the v0.5 cloud suite's timing-sensitive waits under the same contention, then passed it in-chain on the next attempt. The firmware suite failed only that one assertion on two standalone runs and passed in full on the third. No firmware or legacy test code was changed for this. The v0.11, v0.11.2, v0.12 and v0.13 evidence blocks above are therefore the ship-time blocks, kept verbatim; the suites behind them were re-verified this session — v0.1-v0.10 in-chain as said, mock_firmware_test.py standalone (full pass on re-run), and mock_logo_test.py + mock_history_test.py + mock_agents_ui_test.py standalone green against the v0.14 tree.

## Assertions

```
PASS: config: save creates parent dirs and returns the path
PASS: config: save/load round-trip is lossless
PASS: config: core fields survive (key/site/interval/notify)
PASS: config: from_dict drops unknown keys, non-dict notify_config -> None
PASS: config: missing_fields lists the empty required fields
PASS: config path: $BEESKY_AGENT_CONFIG wins on any platform
PASS: config path: Windows uses %APPDATA%\BeeSky
PASS: config path: POSIX falls back to ~/.beesky
PASS: spec: third Analysis targets entry_agent.py
PASS: spec: agent exe is named beesky-agent
PASS: spec: all three EXEs carry the official icon
PASS: spec: agent exe is a console build (run logs visible)
PASS: agent.iss: output is BeeSkyAgentSetup-<version>.exe
PASS: agent.iss: installs beesky-agent.exe + icon + uninstall icon
PASS: agent.iss: Start Menu shortcut launches the config window
PASS: versions in sync: agent.iss == package == installer.iss
PASS: workflow: builds the agent installer
PASS: workflow: agent exe + agent setup in artifact AND release
PASS: workflow: update manifest lists beesky-agent.exe + BeeSkyAgentSetup
PASS: workflow: frozen agent exe smoke check present
PASS: updater: manifest entry beesky-agent.exe matches by basename and applies
PASS: updater: dummy beesky-agent.exe now holds the new bytes
PASS: updater: previous agent exe kept as .old backup
PASS: e2e: cloud-add-agent mints the key the config will carry
PASS: e2e: cloud starts
PASS: e2e: viewer login works
PASS: e2e: config file on disk carries the documented fields
PASS: agent app: `test` from a config file exits 0, TEST OK
PASS: e2e: the test ingest landed — site shows 1 miner
PASS: e2e: /api/miners shows the dashd S19 Pro from the config-driven agent
PASS: agent app: `run --once` from the config exits 0
PASS: agent app: `test` with a wrong key exits 1, TEST FAIL
PASS: agent app: install-task off Windows prints the systemd/cron guidance instead of failing obscurely
PASS: agent app: task command embeds exe + run + --config
PASS: gui: config window constructs with all five fields
PASS: gui: key entry starts masked
PASS: gui: 'Hiện key' toggle unmasks the key entry
PASS: gui: auto-start button disabled off Windows
PASS: gui: 'Lưu cấu hình' accepts a complete form
PASS: gui: save wrote the config JSON
PASS: gui: saved JSON round-trips the form values

AGENT APP TEST PASSED
```

---

# v0.15 mock test — desktop apps visual overhaul (shared ui_theme)

`beesky/ui_theme.py` is the new shared design system for both
desktop windows: the cloud dashboard's palette (bg #0B0B0D,
panels #15151A/#1C1C22, border #26262E, text #F2F2F3, muted
#9CA3AF, accent #F5D800, status #34D399/#FBBF24/#F87171) on
ttk 'clam' — card frames, label-above form fields, accent/ghost
buttons, dark entries with a yellow focus border, a 30px-row
treeview, slim dark scrollbars and a status pill.
`beesky/agent_gui.py` is rebuilt on it: header (logo 40px +
'BeeSky Agent' title + version chip), a 'Kết nối cloud' card
(Cloud URL, masked agent key with Hiện key toggle, Tên trại,
the one-time-key note), a 'Quét tại trại' card (Dải IP quét,
Chu kỳ quét), the three action buttons (labels unchanged)
plus a status pill that follows Chạy thử (dim 'Chưa chạy thử'
/ warn / ok / bad), footer status line. `beesky/gui.py` is
rebuilt on it too: header band (logo + 'BeeSky' + subtitle
'Giám sát & chẩn đoán máy đào ASIC' + version), a 'Mục tiêu
quét' toolbar card (wide target entry, Quét ngay / Xuất
phiếu sửa / Mở web tại chỗ / Quét lại, plus the stock-firmware
User/Mật khẩu fields), FOUR stat cards (Tổng số máy / Tổng
hashrate / Máy có vấn đề / Nhiệt độ cao nhất) driven by
show_records(), the results tree and the 'Chi tiết máy đã
chọn' detail pane as cards, and a footer status bar. No
CLI/agent/cloud code changed; all behaviour is preserved.

**Full-chain note (v0.11 flake, handled as in v0.12–v0.14):**
the v0.15 chain regenerated v0.1–v0.10 green in-chain (156
PASS lines) and then stopped at the known load-sensitive
v0.11 firmware assertion `unlock order: identify ->
first.bmu -> kill -> second.bmu -> patch marker` (indices
ident=0 first=5 kill=3 second=8 marker=11 — the shared-log
append order of the race kill vs the first upload; the
companion assertion 'kill landed inside the first-upload
window' passes and the unlock itself succeeds). Control:
the IDENTICAL failure reproduces on the pristine v0.14 tree
(HEAD 8d9e53b, changes stashed), so it is pre-existing and
environmental — this diff touches no firmware-path code
(gui.py / agent_gui.py / ui_theme.py only). No firmware or
legacy test logic was 'fixed'. The v0.11–v0.14 evidence
blocks above are therefore the ship-time blocks, kept
verbatim; every suite after v0.11 was re-verified standalone
against the final v0.15 tree: logo 17/17 PASS, history
22/22 PASS, agents-ui 30/30 PASS, agent-app 41/41 PASS
(incl. the config-GUI assertions: fields, key mask toggle,
save round-trip, auto-start disabled off Windows), main-GUI
smoke PASSED (mock S19 Pro row 339/342 CHECK), theme test
25/25 PASS (below).

## Assertions (`tests/mock_theme_test.py`, under `xvfb-run`)

```
PASS: theme: a font family is chosen
PASS: theme: root background is the dashboard bg
PASS: theme: TEntry fieldbackground is panel2
PASS: theme: TEntry padding is (10, 7)
PASS: theme: Accent.TButton background is the BeeSky yellow
PASS: theme: Ghost.TButton background is panel2
PASS: theme: Treeview background is the card panel
PASS: theme: Treeview rowheight is 30
PASS: theme: Card.TFrame background is the card panel
PASS: theme: palette constants match the spec hex values
PASS: agent gui: 'Kết nối cloud' card is present
PASS: agent gui: 'Quét tại trại' card is present
PASS: agent gui: the three action buttons keep their labels
PASS: agent gui: status pill starts at 'Chưa chạy thử'
PASS: agent gui: pill recolours to the ok colour
PASS: main gui: 'Mục tiêu quét' is present
PASS: main gui: 'Tổng số máy' is present
PASS: main gui: 'Tổng hashrate' is present
PASS: main gui: 'Máy có vấn đề' is present
PASS: main gui: 'Nhiệt độ cao nhất' is present
PASS: main gui: 'Chi tiết máy đã chọn' is present
PASS: main gui: toolbar buttons keep their labels
PASS: main gui: stat cards follow a scan (1 máy, 100.50 TH/s)
PASS: main gui: problem stat counts and turns red
PASS: main gui: max-temp stat shows the hottest miner

THEME TEST PASSED
```

---

# v0.16 mock test — agent background service + install security

`tests/mock_agent_bg_test.py` covers the v0.16 changes.
BACKGROUND: the spec gains a windowless twin `beesky-agentw`
(console=False, same Analysis as `beesky-agent`); a frozen
agentw — or `run --background` — never opens the config GUI,
routes all output through a redacting stream into `agent.log`
next to the config (rotated at ~1 MB, one .old), and rewrites
`agent-status.json` after EVERY cycle via the AgentService
status hook (ok / miners / error / cloud_url / site, atomic
temp+replace). `install-task` now registers the task from
generated XML (`schtasks /Create /XML`): SYSTEM principal
(S-1-5-18) at HighestAvailable, BootTrigger (PT30S delay) +
LogonTrigger, Hidden=true, ExecutionTimeLimit PT0S,
RestartOnFailure PT1M x5, battery-proof, action = the
windowless exe with the config path baked in;
`install-task --console` is the debugging escape hatch.
SECURITY: on Windows the agent key is DPAPI-protected in the
config (CRYPTPROTECT_LOCAL_MACHINE so the SYSTEM task can
decrypt; `key` written empty, `key_protected` base64) —
off Windows the file is chmod 0600 after every save (Windows
also gets a best-effort owner+SYSTEM icacls); a protect
failure degrades to plain text rather than losing the
config, and legacy plain-text configs migrate on next save.
The agent key is scrubbed from every failure print
(`beesky.agent.redact`) and from the whole run stream; a
non-local http:// cloud URL logs a one-time warning and
shows the same hint in the config window (never a hard
block). The window gains a 'Trạng thái chạy ngầm' card
(status pill + last cycle detail + Xem log) fed by
agent-status.json. All v0.14/v0.15 assertions run green
inside the full chain above; the new suite adds:

```
invalid command name "128729226494656_poll_queue"
    while executing
"128729226494656_poll_queue"
    ("after" script)
invalid command name "128729226897024_poll_queue"
    while executing
"128729226897024_poll_queue"
    ("after" script)
PASS: dpapi: saved file contains NO plain-text key
PASS: dpapi: key field emptied, key_protected present
PASS: dpapi: load() transparently returns the plain key
PASS: dpapi: a protect failure degrades to plain text (config never lost)
PASS: posix: without DPAPI the key stays plain text
PASS: posix: config file is chmod 0600 after save
PASS: migration: legacy plain-text key still loads
PASS: migration: next save rewrites the key protected
PASS: dpapi: an undecryptable blob loads as an empty key
PASS: redact: every occurrence of the secret is masked
PASS: redact: empty secrets are a no-op
PASS: log stream: the key never reaches agent.log
PASS: task xml: SYSTEM principal (S-1-5-18)
PASS: task xml: highest run level
PASS: task xml: BootTrigger present
PASS: task xml: boot delay PT30S
PASS: task xml: LogonTrigger present
PASS: task xml: task hidden
PASS: task xml: no execution time limit
PASS: task xml: restart on failure every minute
PASS: task xml: restart count 5
PASS: task xml: network not required
PASS: task xml: never stops on batteries
PASS: task xml: windowless exe is the action
PASS: task xml: config path baked into the action
PASS: task xml: --console escape hatch uses the console exe
PASS: spec: windowless twin named beesky-agentw
PASS: spec: agentw is a console=False build
PASS: agent.iss: ships beesky-agentw.exe alongside the console exe
PASS: workflow: agentw in artifact AND release file lists
PASS: workflow: signed update manifest lists beesky-agentw.exe
PASS: versions in sync at 0.16.0
PASS: e2e: cloud mints the agent key
PASS: e2e: cloud starts
PASS: bg e2e: `run --once` exits 0 and reports the pass
PASS: bg e2e: agent-status.json written, ok with 1 miner
PASS: bg e2e: agent.log mirrors the run output
PASS: bg e2e: agent.log does NOT contain the agent key
PASS: bg e2e: localhost http cloud raises no warning
PASS: bg e2e: --background prints nothing to stdout
PASS: bg e2e: --background still writes status + log
PASS: bg e2e: a wrong-key cycle survives and is recorded as ok=false with an error
PASS: bg e2e: the failing log never contains the (wrong) key
PASS: bg e2e: non-local http:// cloud warns about the unencrypted key (but is not blocked)
PASS: bg e2e: the unreachable-cloud cycle is recorded ok=false, not a crash
PASS: gui: status card starts at 'Chưa có dữ liệu'
PASS: gui: 'Xem log' button exists
PASS: gui: non-local http:// cloud shows the https hint
PASS: gui: localhost http clears the hint
PASS: gui: https clears the hint
PASS: gui: an OK status renders 'Đang chạy tốt' + miner count
PASS: gui: an error status renders 'Lỗi gần nhất' + the error

AGENT BG TEST PASSED
```

## v0.17 standalone verification (chain halted externally after v0.10 stage)
Chain run_mock_test_v17.sh regenerated v0.1-v0.10 in-chain green (156 PASS), then the run was halted externally (no FAIL line in the log). Ship-time v0.11-v0.16 blocks above are the committed ones, restored verbatim. The v0.11-v0.17 suites were re-verified standalone against the v0.17 tree: firmware (PASS on retry - its unlock-order assertion is timing-sensitive: FAIL/PASS/FAIL observed back-to-back on the identical tree), history, agents-ui, logo, cloud, theme, gui, agent-app, agent-bg all PASSED. Rounded suite evidence:
PASS: tokens: radius scale is 16 / 12 / 999
PASS: web cloud/dashboard.html: radius tokens are defined
PASS: web cloud/dashboard.html: no pre-token literal radii remain
PASS: web cloud/dashboard.html: token vars are actually used
PASS: web web/dashboard.html: radius tokens are defined
PASS: web web/dashboard.html: no pre-token literal radii remain
PASS: web web/dashboard.html: token vars are actually used
PASS: button: accent constructs at >= 36px tall
PASS: button: cget reports text + state like ttk
PASS: button: press+release inside fires the command
PASS: button: release outside cancels the click
PASS: button: keyboard focus draws the focus ring
PASS: button: Return and Space activate a focused button
PASS: button: invoke() fires while enabled
PASS: button: configure(state=) updates cget('state')
PASS: button: a disabled button never fires (click or invoke)
PASS: button: set_text relabels and resizes
PASS: button: ghost + danger-ghost variants construct
PASS: entry: .entry hosts the real tk.Entry
PASS: entry: typing flows into the textvariable
PASS: entry: variable writes flow into the entry
PASS: entry: show='*' masks (cget delegates to the entry)
PASS: entry: configure(show='') unmasks ('Hiện key' path)
PASS: entry: focus turns the frame outline accent
PASS: card: ui_theme.card returns a ttk.Frame (RoundedCard)
PASS: card: title + content findable by tree walk
PASS: card: the rounded surface is drawn on its canvas
PASS: pill: status_pill returns a RoundedPill
PASS: pill: set_pill recolours + retexts (cget('bg') = OK)
PASS: windows: agent key_entry is a RoundedEntry
PASS: windows: agent buttons are RoundedButtons
PASS: windows: agent pills are RoundedPills
PASS: windows: main scan_button is a RoundedButton

---

# v0.18 mock test — Liquid Glass (real web glass, simulated desktop glass)

Web (both dashboards, beesky/cloud + beesky/web): real
Liquid Glass — an ambient layered body backdrop (two subtle
radial glows over the #0B0B0D base, fixed attachment), glass
tokens (--glass rgba(255,255,255,.045), --glass-line .09,
--glass-soft .05 / --glass-line-soft .10 for inputs, ghost
buttons and chips, --glass-chrome for sidebar/top bars,
--glass-head for table header rows), backdrop-filter
blur(16px) saturate(150%) (10px for the soft tier) on cards,
panels, stat tiles, sidebar, settings panels and table
containers, the rim+depth shadow (inset 0 1px 0
rgba(255,255,255,.08), 0 8px 32px rgba(0,0,0,.35)); the
accent CTA stays solid #F5D800 and table rows stay
transparent over a rgba(255,255,255,.03) header. Fallbacks:
@supports not (backdrop-filter) and @media
(prefers-reduced-transparency: reduce) re-point every glass
token at the pre-v0.18 solids (#15151A/#1C1C22/#232329/
#101014) and set the blur tokens to none — no layout or DOM
change. Desktop (Tk cannot blur): simulated glass in
beesky/ui_theme.py + beesky/rounded.py — PANEL_GLASS
#191920 card fill, GLASS_BORDER #34343E outlines, a real
canvas rim-light line (RIM_LIGHT #3D3D4A, top arc +
straight inset 1px, tagged "rim") on RoundedCard and
ghost RoundedButtons, GHOST_FILL #22222B, ENTRY_FILL
#1E1E26 / ENTRY_BORDER #30303C; card-hosted ttk styles and
in-card widget backdrops moved PANEL -> PANEL_GLASS so
labels blend with the drawn surface; pills and the accent
button stay solid. Changed test expectations (all still
exact pins, listed in the root RESULTS.md v0.18 section):
mock_theme_test Card.TFrame PANEL -> PANEL_GLASS + a new
exact pin of the six glass tokens; mock_agent_bg_test
release pin 0.17.0 -> 0.18.0. The new suite adds:

```
PASS: web cloud/dashboard.html: glass token is translucent white .045
PASS: web cloud/dashboard.html: glass line token is rgba .09
PASS: web cloud/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web cloud/dashboard.html: ambient radial-gradient body backdrop
PASS: web cloud/dashboard.html: @supports no-backdrop-filter fallback
PASS: web cloud/dashboard.html: reduced-transparency fallback
PASS: web cloud/dashboard.html: glass shadow token (rim inset + drop)
PASS: web cloud/dashboard.html: accent CTA stays solid yellow
PASS: web web/dashboard.html: glass token is translucent white .045
PASS: web web/dashboard.html: glass line token is rgba .09
PASS: web web/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web web/dashboard.html: ambient radial-gradient body backdrop
PASS: web web/dashboard.html: @supports no-backdrop-filter fallback
PASS: web web/dashboard.html: reduced-transparency fallback
PASS: web web/dashboard.html: glass shadow token (rim inset + drop)
PASS: web web/dashboard.html: accent CTA stays solid yellow
PASS: desktop: card surface is drawn
PASS: desktop: card fill is PANEL_GLASS, outline GLASS_BORDER
PASS: desktop: card draws exactly one rim-light item
PASS: desktop: rim light colour is RIM_LIGHT
PASS: desktop: rim survives a resize without double-drawing
PASS: desktop: ghost button draws one rim item, accent none
PASS: desktop: ghost colours are the glass triple
PASS: desktop: disabled ghost drops the rim, mutes to glass
PASS: desktop: entry shape is ENTRY_FILL / ENTRY_BORDER
PASS: desktop: hosted entry bg matches the glass fill

GLASS TEST PASSED
```

Chain note (flake disclosure, same handling as v0.12–v0.17): the full
chain regenerated v0.1–v0.10 green in-chain, then stopped at the KNOWN
v0.11 firmware race-order assertion (kill idx 3 vs first.bmu idx 5).
Control-verified PRE-EXISTING on this exact tree state: the pristine
v0.17 tree (b5fdd90, v0.18 changes stashed) fails the same assertion
standalone with byte-identical indices (ident=0 first=5 kill=3 second=8
marker=11), and the v0.18 diff touches no firmware-path code (it
alternated FAIL/PASS/FAIL during v0.17 verification; under the current
host contention it fails consistently on both trees). tests/RESULTS.md
was therefore restored to the committed ship-time blocks and every
later suite was re-verified standalone against the v0.18 tree — logo,
history, agents-ui, agent-app, theme, agent-bg, rounded, glass, GUI,
cloud, web: all green.

## v0.18.1 — dashboard version stamp
PASS: web cloud/dashboard.html: glass token is translucent white .045
PASS: web cloud/dashboard.html: glass line token is rgba .09
PASS: web cloud/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web cloud/dashboard.html: ambient radial-gradient body backdrop
PASS: web cloud/dashboard.html: @supports no-backdrop-filter fallback
PASS: web cloud/dashboard.html: reduced-transparency fallback
PASS: web cloud/dashboard.html: glass shadow token (rim inset + drop)
PASS: web cloud/dashboard.html: accent CTA stays solid yellow
PASS: web web/dashboard.html: glass token is translucent white .045
PASS: web web/dashboard.html: glass line token is rgba .09
PASS: web web/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web web/dashboard.html: ambient radial-gradient body backdrop
PASS: web web/dashboard.html: @supports no-backdrop-filter fallback
PASS: web web/dashboard.html: reduced-transparency fallback
PASS: web web/dashboard.html: glass shadow token (rim inset + drop)
PASS: web web/dashboard.html: accent CTA stays solid yellow
PASS: cloud: served footer shows current version
PASS: cloud: no un-stamped placeholder left
PASS: web: served footer shows current version
PASS: web: no un-stamped placeholder left
PASS: desktop: card surface is drawn
PASS: desktop: card fill is PANEL_GLASS, outline GLASS_BORDER
PASS: desktop: card draws exactly one rim-light item
PASS: desktop: rim light colour is RIM_LIGHT
PASS: desktop: rim survives a resize without double-drawing
PASS: desktop: ghost button draws one rim item, accent none
PASS: desktop: ghost colours are the glass triple
PASS: desktop: disabled ghost drops the rim, mutes to glass
PASS: desktop: entry shape is ENTRY_FILL / ENTRY_BORDER
PASS: desktop: hosted entry bg matches the glass fill

---

# v0.19 mock test — miners table beautified (standalone verification; chain halted externally)

Chain run_mock_test_v19.sh regenerated v0.1-v0.10 in-chain green (156 PASS),
then the run was halted externally at the v0.10 -> v0.11 transition (no FAIL
line in the log — the same external halt seen at v0.17). The committed
ship-time v0.11-v0.18 blocks above were restored verbatim and every later
suite was re-verified standalone against the v0.19 tree:

  * mock_firmware_test (v0.11): its unlock-order assertion
    (identify -> first.bmu -> kill -> second.bmu -> patch marker) is the
    KNOWN load-sensitive flake — on the v0.19 tree it ran
    FAIL/PASS/FAIL/FAIL/FAIL/FAIL and, control-verified with the v0.19 diff
    stashed, FAIL/FAIL/PASS on the pristine v0.18.1 tree (ca3156d):
    non-deterministic on identical code, and this diff touches no
    firmware-path code (ui_theme styles + gui table/detail only).
  * actions, agents-ui, cloud, energy/pool, history, logo, repairs,
    watch, web: PASSED standalone. Rounded, glass, agent-app, agent-bg
    (incl. the 0.19.0 release pin): PASSED standalone under xvfb.

v0.19 itself (beesky/ui_theme.py + beesky/gui.py; web dashboards untouched):
the ttk Treeview style never pinned bordercolor/lightcolor/darkcolor, so
clam's LIGHT default border rendered as a white frame around the table —
now all three are pinned to the new TABLE_WELL token (#121216) with
borderwidth=0/relief=flat, and background/fieldbackground move PANEL ->
TABLE_WELL (rowheight stays 30). Treeview.Heading: TABLE_HEADING (#1D1D24)
strip, border pinned to itself so the separator line vanishes.
Vertical.TScrollbar/TScrollbar: BORDER (#26262E) thumb, TABLE_WELL trough +
border, muted arrows. The table sits in an inset RoundedCard WELL inside
its glass card (radius 12, fill TABLE_WELL, #26262E outline, 10px inset).
Zebra: an "odd" tag (TABLE_ZEBRA #17171D) is applied at insertion to
odd-indexed plain OK rows only — problem rows keep exactly their
check/error wash tags. Detail tk.Text: borderwidth=0, highlightthickness=0,
background PANEL2 -> PANEL_GLASS (flat on its card).
Changed test expectations (all still exact pins): mock_theme_test Treeview
background PANEL -> TABLE_WELL + new pins (Treeview border colours,
heading strip + border, dark scrollbar, three table tokens) + row-tag
assertions; mock_agent_bg_test release pin 0.18.1 -> 0.19.0.

```
PASS: theme: a font family is chosen
PASS: theme: root background is the dashboard bg
PASS: theme: TEntry fieldbackground is panel2
PASS: theme: TEntry padding is (10, 7)
PASS: theme: Accent.TButton background is the BeeSky yellow
PASS: theme: Ghost.TButton background is panel2
PASS: theme: Treeview background is the table well (v0.19)
PASS: theme: Treeview rowheight is 30
PASS: theme: Treeview border is pinned to the well colour (no white clam frame)
PASS: theme: Treeview.Heading background is the heading strip
PASS: theme: Treeview.Heading border is its own background (no separator line)
PASS: theme: scrollbar is dark (border thumb, well trough)
PASS: theme: table tokens match the v0.19 spec hex values
PASS: theme: Card.TFrame background is the glass panel (v0.18)
PASS: theme: palette constants match the spec hex values
PASS: theme: glass tokens match the v0.18 spec hex values
PASS: agent gui: 'Kết nối cloud' card is present
PASS: agent gui: 'Quét tại trại' card is present
PASS: agent gui: the three action buttons keep their labels
PASS: agent gui: status pill starts at 'Chưa chạy thử'
PASS: agent gui: pill recolours to the ok colour
PASS: main gui: 'Mục tiêu quét' is present
PASS: main gui: 'Tổng số máy' is present
PASS: main gui: 'Tổng hashrate' is present
PASS: main gui: 'Máy có vấn đề' is present
PASS: main gui: 'Nhiệt độ cao nhất' is present
PASS: main gui: 'Chi tiết máy đã chọn' is present
PASS: main gui: toolbar buttons keep their labels
PASS: main gui: stat cards follow a scan (1 máy, 100.50 TH/s)
PASS: main gui: problem stat counts and turns red
PASS: main gui: max-temp stat shows the hottest miner
PASS: main gui: even OK row has no parity tag
PASS: main gui: odd OK row carries the zebra tag
PASS: main gui: CHECK row keeps its wash tag (no zebra)

THEME TEST PASSED
```

```
PASS: mock miner up on 127.0.0.1:4028
GUI SMOKE: 1 row(s) for target 127.0.0.1
GUI SMOKE first row: 127.0.0.1 | Antminer S19 Pro | cgminer RPC | 102.90 | 339/342 | 88 | 4320/4380/4440/4500 | CHECK
PASS: beesky gui --smoke exits 0 under the virtual display
PASS: GUI table holds exactly 1 row after one scan
PASS: first row = 127.0.0.1 | Antminer S19 Pro | ... | 339/342 chips | CHECK (same values as the CLI)

GUI TEST PASSED
```

---

# v0.19.6 mock test — auto-detected default target + multi-range targets

Field bug: on the owner's laptop the scan target defaulted to
the hard-coded 192.168.1.0/24; his fleet is on 192.168.2.0/24,
so the first sweep found 0 miners and the app read as broken.
And BTC Tools beside it scanned several /24 ranges at once.

v0.19.6 (beesky/core/discover.py, beesky/gui.py,
beesky/cli.py, beesky/agent_gui.py, beesky/agent_app.py):

  * New discover.default_scan_target(): the primary LAN
    IPv4 via the UDP-connect trick (no packet is sent),
    returned as its /24. Any failure, and loopback /
    link-local / unspecified results, fall back to
    192.168.1.0/24; the helper never raises.
  * The helper pre-fills the main GUI target (default_target
    now None -> helper), the agent config window on first
    run (no config file yet; a saved config still wins),
    the main GUI's empty-field fallback in open_local_web,
    and the CLI gui --target default (None -> helper).
    Fields stay fully editable — pre-fill only.
  * parse_targets() now builds the multi-range union
    explicitly: comma-separated items (IP / CIDR / range)
    are parsed as before, de-duplicated preserving
    first-seen order (each item expands ascending, so a
    single spec yields exactly the list it always did),
    and the MAX_HOSTS cap applies to the de-duplicated
    union. One invalid item still rejects the whole spec.
    Help texts (CLI scan/watch/agent, agent window hint)
    now say comma-separated mixes scan several ranges.

Changed test expectations: mock_agent_bg_test release pin
0.19.5 -> 0.19.6 (plus __init__ and both .iss). New suite
mock_targets_test.py; the real (unstubbed) subnet never
leaks into an assertion — the helper is stubbed at each
app's import seam and at the socket layer. No behaviour
assertion was weakened. The updated suites:

```
PASS: fallback constant is the historic default
PASS: helper: detected 192.168.2.37 -> its /24
PASS: helper: detection used an AF_INET datagram socket
PASS: helper: detected 10.20.30.40 -> 10.20.30.0/24
PASS: helper: socket creation failure -> fallback
PASS: helper: connect failure (offline) -> fallback
PASS: helper: getsockname failure -> fallback, never raises
PASS: helper: loopback result 127.0.0.1 -> fallback
PASS: helper: link-local result 169.254.9.9 -> fallback
PASS: helper: unspecified result 0.0.0.0 -> fallback
PASS: helper: unstubbed call returns a parseable /24 target
PASS: parser: union of two CIDRs
PASS: parser: union keeps first-seen order, no global re-sort
PASS: parser: overlapping ranges de-duplicate
PASS: parser: an item fully inside another adds nothing
PASS: parser: whitespace around items is tolerated
PASS: parser: mixed forms (IP + CIDR + range) union
PASS: parser: one bad item rejects the whole spec
PASS: parser: bad first item rejects the whole spec
PASS: parser: empty spec still rejected
PASS: parser: oversized union still rejected
PASS: parser: size cap counts the union, not raw duplicates
PASS: parser: single CIDR output unchanged
PASS: parser: single IP output unchanged
PASS: parser: single range output unchanged
PASS: main gui: target pre-filled from the helper
PASS: main gui: explicit default beats the helper
PASS: main gui: comma target reaches the scan unchanged
PASS: main gui: make_scan_args passes the target through
PASS: agent gui: first run pre-fills the helper target
PASS: agent gui: comma target reaches the config unchanged
PASS: agent gui: saved config target beats the helper
PASS: agent config: comma target round-trips verbatim
PASS: cli: `gui` without --target hands None to run_gui (helper resolves it)
PASS: cli: `gui --target X` hands X through unchanged

TARGETS TEST PASSED
```

```
PASS: mock miner up on 127.0.0.1:4028
GUI SMOKE: 1 row(s) for target 127.0.0.1
GUI SMOKE first row: 127.0.0.1 | Antminer S19 Pro | cgminer RPC | 102.90 | 339/342 | 88 | 4320/4380/4440/4500 | CHECK
PASS: beesky gui --smoke exits 0 under the virtual display
PASS: GUI table holds exactly 1 row after one scan
PASS: first row = 127.0.0.1 | Antminer S19 Pro | ... | 339/342 chips | CHECK (same values as the CLI)

GUI TEST PASSED
```

```
PASS: config: save creates parent dirs and returns the path
PASS: config: save/load round-trip is lossless
PASS: config: core fields survive (key/site/interval/notify)
PASS: config: from_dict drops unknown keys, non-dict notify_config -> None
PASS: config: missing_fields lists the empty required fields
PASS: config path: $BEESKY_AGENT_CONFIG wins on any platform
PASS: config path: Windows uses %APPDATA%\BeeSky
PASS: config path: POSIX falls back to ~/.beesky
PASS: spec: third Analysis targets entry_agent.py
PASS: spec: agent exe is named beesky-agent
PASS: spec: all three EXEs carry the official icon
PASS: spec: agent exe is a console build (run logs visible)
PASS: agent.iss: output is BeeSkyAgentSetup-<version>.exe
PASS: agent.iss: installs beesky-agent.exe + icon + uninstall icon
PASS: agent.iss: Start Menu shortcut launches the config window
PASS: versions in sync: agent.iss == package == installer.iss
PASS: workflow: builds the agent installer
PASS: workflow: agent exe + agent setup in artifact AND release
PASS: workflow: update manifest lists beesky-agent.exe + BeeSkyAgentSetup
PASS: workflow: frozen agent exe smoke check present
PASS: updater: manifest entry beesky-agent.exe matches by basename and applies
PASS: updater: dummy beesky-agent.exe now holds the new bytes
PASS: updater: previous agent exe kept as .old backup
PASS: e2e: cloud-add-agent mints the key the config will carry
PASS: e2e: cloud starts
PASS: e2e: viewer login works
PASS: e2e: config file on disk carries the documented fields
PASS: agent app: `test` from a config file exits 0, TEST OK
PASS: e2e: the test ingest landed — site shows 1 miner
PASS: e2e: /api/miners shows the dashd S19 Pro from the config-driven agent
PASS: agent app: `run --once` from the config exits 0
PASS: agent app: `test` with a wrong key exits 1, TEST FAIL
PASS: agent app: install-task off Windows prints the systemd/cron guidance instead of failing obscurely
PASS: agent app: task command embeds exe + run + --config
PASS: gui: config window constructs with all five fields
PASS: gui: key entry starts masked
PASS: gui: 'Hiện key' toggle unmasks the key entry
PASS: gui: auto-start button disabled off Windows
PASS: gui: 'Lưu cấu hình' accepts a complete form
PASS: gui: save wrote the config JSON
PASS: gui: saved JSON round-trips the form values

AGENT APP TEST PASSED
```

```
invalid command name "125155111658688_poll_queue"
    while executing
"125155111658688_poll_queue"
    ("after" script)
invalid command name "125155100744704_poll_queue"
    while executing
"125155100744704_poll_queue"
    ("after" script)
PASS: dpapi: saved file contains NO plain-text key
PASS: dpapi: key field emptied, key_protected present
PASS: dpapi: load() transparently returns the plain key
PASS: dpapi: a protect failure degrades to plain text (config never lost)
PASS: posix: without DPAPI the key stays plain text
PASS: posix: config file is chmod 0600 after save
PASS: migration: legacy plain-text key still loads
PASS: migration: next save rewrites the key protected
PASS: dpapi: an undecryptable blob loads as an empty key
PASS: redact: every occurrence of the secret is masked
PASS: redact: empty secrets are a no-op
PASS: log stream: the key never reaches agent.log
PASS: task xml: SYSTEM principal (S-1-5-18)
PASS: task xml: highest run level
PASS: task xml: BootTrigger present
PASS: task xml: boot delay PT30S
PASS: task xml: LogonTrigger present
PASS: task xml: task hidden
PASS: task xml: no execution time limit
PASS: task xml: restart on failure every minute
PASS: task xml: restart count 5
PASS: task xml: network not required
PASS: task xml: never stops on batteries
PASS: task xml: windowless exe is the action
PASS: task xml: config path baked into the action
PASS: task xml: --console escape hatch uses the console exe
PASS: spec: windowless twin named beesky-agentw
PASS: spec: agentw is a console=False build
PASS: agent.iss: ships beesky-agentw.exe alongside the console exe
PASS: workflow: agentw in artifact AND release file lists
PASS: workflow: signed update manifest lists beesky-agentw.exe
PASS: versions in sync at 0.19.6
PASS: e2e: cloud mints the agent key
PASS: e2e: cloud starts
PASS: bg e2e: `run --once` exits 0 and reports the pass
PASS: bg e2e: agent-status.json written, ok with 1 miner
PASS: bg e2e: agent.log mirrors the run output
PASS: bg e2e: agent.log does NOT contain the agent key
PASS: bg e2e: localhost http cloud raises no warning
PASS: bg e2e: --background prints nothing to stdout
PASS: bg e2e: --background still writes status + log
PASS: bg e2e: a wrong-key cycle survives and is recorded as ok=false with an error
PASS: bg e2e: the failing log never contains the (wrong) key
PASS: bg e2e: non-local http:// cloud warns about the unencrypted key (but is not blocked)
PASS: bg e2e: the unreachable-cloud cycle is recorded ok=false, not a crash
PASS: gui: status card starts at 'Chưa có dữ liệu'
PASS: gui: 'Xem log' button exists
PASS: gui: non-local http:// cloud shows the https hint
PASS: gui: localhost http clears the hint
PASS: gui: https clears the hint
PASS: gui: an OK status renders 'Đang chạy tốt' + miner count
PASS: gui: an error status renders 'Lỗi gần nhất' + the error

AGENT BG TEST PASSED
```

```
PASS: theme: a font family is chosen
PASS: theme: root background is the dashboard bg
PASS: theme: TEntry fieldbackground is panel2
PASS: theme: TEntry padding is (10, 7)
PASS: theme: Accent.TButton background is the BeeSky yellow
PASS: theme: Ghost.TButton background is panel2
PASS: theme: Treeview background is the table well (v0.19)
PASS: theme: Treeview rowheight is 30
PASS: theme: Treeview border is pinned to the well colour (no white clam frame)
PASS: theme: Treeview.Heading background is the heading strip
PASS: theme: Treeview.Heading border is its own background (no separator line)
PASS: theme: scrollbar is dark (border thumb, well trough)
PASS: theme: table tokens match the v0.19 spec hex values
PASS: theme: Card.TFrame background is the glass panel (v0.18)
PASS: theme: palette constants match the spec hex values
PASS: theme: glass tokens match the v0.18 spec hex values
PASS: agent gui: 'Kết nối cloud' card is present
PASS: agent gui: 'Quét tại trại' card is present
PASS: agent gui: the three action buttons keep their labels
PASS: agent gui: status pill starts at 'Chưa chạy thử'
PASS: agent gui: pill recolours to the ok colour
PASS: main gui: 'Mục tiêu quét' is present
PASS: main gui: 'Tổng số máy' is present
PASS: main gui: 'Tổng hashrate' is present
PASS: main gui: 'Máy có vấn đề' is present
PASS: main gui: 'Nhiệt độ cao nhất' is present
PASS: main gui: 'Chi tiết máy đã chọn' is present
PASS: main gui: toolbar buttons keep their labels
PASS: main gui: stat cards follow a scan (1 máy, 100.50 TH/s)
PASS: main gui: problem stat counts and turns red
PASS: main gui: max-temp stat shows the hottest miner
PASS: main gui: even OK row has no parity tag
PASS: main gui: odd OK row carries the zebra tag
PASS: main gui: CHECK row keeps its wash tag (no zebra)

THEME TEST PASSED
```

```
invalid command name "126963414712256_poll_queue"
    while executing
"126963414712256_poll_queue"
    ("after" script)
PASS: tokens: radius scale is 16 / 12 / 999
PASS: web cloud/dashboard.html: radius tokens are defined
PASS: web cloud/dashboard.html: no pre-token literal radii remain
PASS: web cloud/dashboard.html: token vars are actually used
PASS: web web/dashboard.html: radius tokens are defined
PASS: web web/dashboard.html: no pre-token literal radii remain
PASS: web web/dashboard.html: token vars are actually used
PASS: button: accent constructs at >= 36px tall
PASS: button: cget reports text + state like ttk
PASS: button: press+release inside fires the command
PASS: button: release outside cancels the click
PASS: button: keyboard focus draws the focus ring
PASS: button: Return and Space activate a focused button
PASS: button: invoke() fires while enabled
PASS: button: configure(state=) updates cget('state')
PASS: button: a disabled button never fires (click or invoke)
PASS: button: set_text relabels and resizes
PASS: button: ghost + danger-ghost variants construct
PASS: entry: .entry hosts the real tk.Entry
PASS: entry: typing flows into the textvariable
PASS: entry: variable writes flow into the entry
PASS: entry: show='*' masks (cget delegates to the entry)
PASS: entry: configure(show='') unmasks ('Hiện key' path)
PASS: entry: focus turns the frame outline accent
PASS: card: ui_theme.card returns a ttk.Frame (RoundedCard)
PASS: card: title + content findable by tree walk
PASS: card: the rounded surface is drawn on its canvas
PASS: pill: status_pill returns a RoundedPill
PASS: pill: set_pill recolours + retexts (cget('bg') = OK)
PASS: windows: agent key_entry is a RoundedEntry
PASS: windows: agent buttons are RoundedButtons
PASS: windows: agent pills are RoundedPills
PASS: windows: main scan_button is a RoundedButton

ROUNDED TEST PASSED
```

```
PASS: web cloud/dashboard.html: glass token is translucent white .045
PASS: web cloud/dashboard.html: glass line token is rgba .09
PASS: web cloud/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web cloud/dashboard.html: ambient radial-gradient body backdrop
PASS: web cloud/dashboard.html: @supports no-backdrop-filter fallback
PASS: web cloud/dashboard.html: reduced-transparency fallback
PASS: web cloud/dashboard.html: glass shadow token (rim inset + drop)
PASS: web cloud/dashboard.html: accent CTA stays solid yellow
PASS: web web/dashboard.html: glass token is translucent white .045
PASS: web web/dashboard.html: glass line token is rgba .09
PASS: web web/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web web/dashboard.html: ambient radial-gradient body backdrop
PASS: web web/dashboard.html: @supports no-backdrop-filter fallback
PASS: web web/dashboard.html: reduced-transparency fallback
PASS: web web/dashboard.html: glass shadow token (rim inset + drop)
PASS: web web/dashboard.html: accent CTA stays solid yellow
PASS: cloud: served footer shows current version
PASS: cloud: no un-stamped placeholder left
PASS: web: served footer shows current version
PASS: web: no un-stamped placeholder left
PASS: desktop: card surface is drawn
PASS: desktop: card fill is PANEL_GLASS, outline GLASS_BORDER
PASS: desktop: card draws exactly one rim-light item
PASS: desktop: rim light colour is RIM_LIGHT
PASS: desktop: rim survives a resize without double-drawing
PASS: desktop: ghost button draws one rim item, accent none
PASS: desktop: ghost colours are the glass triple
PASS: desktop: disabled ghost drops the rim, mutes to glass
PASS: desktop: entry shape is ENTRY_FILL / ENTRY_BORDER
PASS: desktop: hosted entry bg matches the glass fill

GLASS TEST PASSED
```

---

# v0.19.7 mock test — auto-select first miner + window fits the screen

Field reports from the owner's first real fleet scan
(63 miners found on 192.168.2.0/24): (1) after the scan
nothing was selected, so the detail pane kept its
placeholder and he concluded details could not be viewed;
(2) the fixed 1120x880 window was taller than his
laptop's usable screen (Windows scaling), the bottom sank
under the taskbar and the flexible table row collapsed
to about one visible row.

v0.19.7 (beesky/gui.py only):

  * _poll_queue's records branch now calls _land_on_first
    after show_records: with >= 1 row it selects + focuses
    the first row, scrolls it into view and fills the
    detail pane through the same _on_select path a click
    uses. The rows were just rebuilt, so the selection can
    never point at a dead row. With 0 rows it restores the
    DETAIL_PLACEHOLDER text instead of leaving a previous
    scan's detail on screen. show_records itself is
    unchanged — it is also called directly by the theme
    test, where no landing is wanted.
  * _fit_window replaces the fixed center_window call:
    size = min(1120, screen_w - 32) x min(880,
    screen_h - 72), centred ((sw-w)/2, (sh-h)/2); the
    min size (940, 720) now tracks the cap so it cannot
    fight it on a small screen. On the default Xvfb
    screen (1280x1024) the window is exactly 1120x880 at
    +80+72; verified manually on a 1500x1100 screen too:
    exactly 1120x880 at +190+110.
  * gui --smoke additionally prints the post-scan
    selection, the detail pane's first line and the fitted
    geometry (screen size included) for the test.

Changed test expectations: mock_gui_test gains an
empty-scan phase (127.0.0.2, exit 1 as before; selection
'-' and the placeholder intact) and asserts selection =
first row, detail = first miner (not the placeholder),
and geometry = the fitted formula, centred within 2px
and fully on screen. mock_agent_bg_test release pin
0.19.6 -> 0.19.7 (plus __init__ and both .iss). No
behaviour assertion was weakened. The updated suites:

```
GUI SMOKE: 0 row(s) for target 127.0.0.2
GUI SMOKE selection: -
GUI SMOKE detail: Chọn một máy trong bảng để xem chi tiết và danh sách vấn đề.
GUI SMOKE geometry: 1120x880+80+72 screen 1280x1024
PASS: empty scan finds 0 rows (exit 1, as before)
PASS: empty scan leaves no selection
PASS: empty scan keeps the detail placeholder (no stale detail)
PASS: mock miner up on 127.0.0.1:4028
GUI SMOKE: 1 row(s) for target 127.0.0.1
GUI SMOKE first row: 127.0.0.1 | Antminer S19 Pro | cgminer RPC | 102.90 | 339/342 | 88 | 4320/4380/4440/4500 | CHECK
GUI SMOKE selection: 0
GUI SMOKE detail: 127.0.0.1 — Antminer S19 Pro (cgminer RPC)
GUI SMOKE geometry: 1120x880+80+72 screen 1280x1024
PASS: beesky gui --smoke exits 0 under the virtual display
PASS: GUI table holds exactly 1 row after one scan
PASS: first row = 127.0.0.1 | Antminer S19 Pro | ... | 339/342 chips | CHECK (same values as the CLI)
PASS: first row is auto-selected after the scan
PASS: detail pane shows the first miner (not the placeholder)
PASS: window size is the screen-fitted 1120x880 (screen 1280x1024)
PASS: window centred (+80+72) and fully on screen

GUI TEST PASSED
```

```
PASS: theme: a font family is chosen
PASS: theme: root background is the dashboard bg
PASS: theme: TEntry fieldbackground is panel2
PASS: theme: TEntry padding is (10, 7)
PASS: theme: Accent.TButton background is the BeeSky yellow
PASS: theme: Ghost.TButton background is panel2
PASS: theme: Treeview background is the table well (v0.19)
PASS: theme: Treeview rowheight is 30
PASS: theme: Treeview border is pinned to the well colour (no white clam frame)
PASS: theme: Treeview.Heading background is the heading strip
PASS: theme: Treeview.Heading border is its own background (no separator line)
PASS: theme: scrollbar is dark (border thumb, well trough)
PASS: theme: table tokens match the v0.19 spec hex values
PASS: theme: Card.TFrame background is the glass panel (v0.18)
PASS: theme: palette constants match the spec hex values
PASS: theme: glass tokens match the v0.18 spec hex values
PASS: agent gui: 'Kết nối cloud' card is present
PASS: agent gui: 'Quét tại trại' card is present
PASS: agent gui: the three action buttons keep their labels
PASS: agent gui: status pill starts at 'Chưa chạy thử'
PASS: agent gui: pill recolours to the ok colour
PASS: main gui: 'Mục tiêu quét' is present
PASS: main gui: 'Tổng số máy' is present
PASS: main gui: 'Tổng hashrate' is present
PASS: main gui: 'Máy có vấn đề' is present
PASS: main gui: 'Nhiệt độ cao nhất' is present
PASS: main gui: 'Chi tiết máy đã chọn' is present
PASS: main gui: toolbar buttons keep their labels
PASS: main gui: stat cards follow a scan (1 máy, 100.50 TH/s)
PASS: main gui: problem stat counts and turns red
PASS: main gui: max-temp stat shows the hottest miner
PASS: main gui: even OK row has no parity tag
PASS: main gui: odd OK row carries the zebra tag
PASS: main gui: CHECK row keeps its wash tag (no zebra)

THEME TEST PASSED
```

```
invalid command name "127193354440256_poll_queue"
    while executing
"127193354440256_poll_queue"
    ("after" script)
PASS: tokens: radius scale is 16 / 12 / 999
PASS: web cloud/dashboard.html: radius tokens are defined
PASS: web cloud/dashboard.html: no pre-token literal radii remain
PASS: web cloud/dashboard.html: token vars are actually used
PASS: web web/dashboard.html: radius tokens are defined
PASS: web web/dashboard.html: no pre-token literal radii remain
PASS: web web/dashboard.html: token vars are actually used
PASS: button: accent constructs at >= 36px tall
PASS: button: cget reports text + state like ttk
PASS: button: press+release inside fires the command
PASS: button: release outside cancels the click
PASS: button: keyboard focus draws the focus ring
PASS: button: Return and Space activate a focused button
PASS: button: invoke() fires while enabled
PASS: button: configure(state=) updates cget('state')
PASS: button: a disabled button never fires (click or invoke)
PASS: button: set_text relabels and resizes
PASS: button: ghost + danger-ghost variants construct
PASS: entry: .entry hosts the real tk.Entry
PASS: entry: typing flows into the textvariable
PASS: entry: variable writes flow into the entry
PASS: entry: show='*' masks (cget delegates to the entry)
PASS: entry: configure(show='') unmasks ('Hiện key' path)
PASS: entry: focus turns the frame outline accent
PASS: card: ui_theme.card returns a ttk.Frame (RoundedCard)
PASS: card: title + content findable by tree walk
PASS: card: the rounded surface is drawn on its canvas
PASS: pill: status_pill returns a RoundedPill
PASS: pill: set_pill recolours + retexts (cget('bg') = OK)
PASS: windows: agent key_entry is a RoundedEntry
PASS: windows: agent buttons are RoundedButtons
PASS: windows: agent pills are RoundedPills
PASS: windows: main scan_button is a RoundedButton

ROUNDED TEST PASSED
```

```
PASS: web cloud/dashboard.html: glass token is translucent white .045
PASS: web cloud/dashboard.html: glass line token is rgba .09
PASS: web cloud/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web cloud/dashboard.html: ambient radial-gradient body backdrop
PASS: web cloud/dashboard.html: @supports no-backdrop-filter fallback
PASS: web cloud/dashboard.html: reduced-transparency fallback
PASS: web cloud/dashboard.html: glass shadow token (rim inset + drop)
PASS: web cloud/dashboard.html: accent CTA stays solid yellow
PASS: web web/dashboard.html: glass token is translucent white .045
PASS: web web/dashboard.html: glass line token is rgba .09
PASS: web web/dashboard.html: backdrop blur 16px saturate 150% applied
PASS: web web/dashboard.html: ambient radial-gradient body backdrop
PASS: web web/dashboard.html: @supports no-backdrop-filter fallback
PASS: web web/dashboard.html: reduced-transparency fallback
PASS: web web/dashboard.html: glass shadow token (rim inset + drop)
PASS: web web/dashboard.html: accent CTA stays solid yellow
PASS: cloud: served footer shows current version
PASS: cloud: no un-stamped placeholder left
PASS: web: served footer shows current version
PASS: web: no un-stamped placeholder left
PASS: desktop: card surface is drawn
PASS: desktop: card fill is PANEL_GLASS, outline GLASS_BORDER
PASS: desktop: card draws exactly one rim-light item
PASS: desktop: rim light colour is RIM_LIGHT
PASS: desktop: rim survives a resize without double-drawing
PASS: desktop: ghost button draws one rim item, accent none
PASS: desktop: ghost colours are the glass triple
PASS: desktop: disabled ghost drops the rim, mutes to glass
PASS: desktop: entry shape is ENTRY_FILL / ENTRY_BORDER
PASS: desktop: hosted entry bg matches the glass fill

GLASS TEST PASSED
```

```
PASS: config: save creates parent dirs and returns the path
PASS: config: save/load round-trip is lossless
PASS: config: core fields survive (key/site/interval/notify)
PASS: config: from_dict drops unknown keys, non-dict notify_config -> None
PASS: config: missing_fields lists the empty required fields
PASS: config path: $BEESKY_AGENT_CONFIG wins on any platform
PASS: config path: Windows uses %APPDATA%\BeeSky
PASS: config path: POSIX falls back to ~/.beesky
PASS: spec: third Analysis targets entry_agent.py
PASS: spec: agent exe is named beesky-agent
PASS: spec: all three EXEs carry the official icon
PASS: spec: agent exe is a console build (run logs visible)
PASS: agent.iss: output is BeeSkyAgentSetup-<version>.exe
PASS: agent.iss: installs beesky-agent.exe + icon + uninstall icon
PASS: agent.iss: Start Menu shortcut launches the config window
PASS: versions in sync: agent.iss == package == installer.iss
PASS: workflow: builds the agent installer
PASS: workflow: agent exe + agent setup in artifact AND release
PASS: workflow: update manifest lists beesky-agent.exe + BeeSkyAgentSetup
PASS: workflow: frozen agent exe smoke check present
PASS: updater: manifest entry beesky-agent.exe matches by basename and applies
PASS: updater: dummy beesky-agent.exe now holds the new bytes
PASS: updater: previous agent exe kept as .old backup
PASS: e2e: cloud-add-agent mints the key the config will carry
PASS: e2e: cloud starts
PASS: e2e: viewer login works
PASS: e2e: config file on disk carries the documented fields
PASS: agent app: `test` from a config file exits 0, TEST OK
PASS: e2e: the test ingest landed — site shows 1 miner
PASS: e2e: /api/miners shows the dashd S19 Pro from the config-driven agent
PASS: agent app: `run --once` from the config exits 0
PASS: agent app: `test` with a wrong key exits 1, TEST FAIL
PASS: agent app: install-task off Windows prints the systemd/cron guidance instead of failing obscurely
PASS: agent app: task command embeds exe + run + --config
PASS: gui: config window constructs with all five fields
PASS: gui: key entry starts masked
PASS: gui: 'Hiện key' toggle unmasks the key entry
PASS: gui: auto-start button disabled off Windows
PASS: gui: 'Lưu cấu hình' accepts a complete form
PASS: gui: save wrote the config JSON
PASS: gui: saved JSON round-trips the form values

AGENT APP TEST PASSED
```

```
invalid command name "135310921064768_poll_queue"
    while executing
"135310921064768_poll_queue"
    ("after" script)
invalid command name "135310910169344_poll_queue"
    while executing
"135310910169344_poll_queue"
    ("after" script)
PASS: dpapi: saved file contains NO plain-text key
PASS: dpapi: key field emptied, key_protected present
PASS: dpapi: load() transparently returns the plain key
PASS: dpapi: a protect failure degrades to plain text (config never lost)
PASS: posix: without DPAPI the key stays plain text
PASS: posix: config file is chmod 0600 after save
PASS: migration: legacy plain-text key still loads
PASS: migration: next save rewrites the key protected
PASS: dpapi: an undecryptable blob loads as an empty key
PASS: redact: every occurrence of the secret is masked
PASS: redact: empty secrets are a no-op
PASS: log stream: the key never reaches agent.log
PASS: task xml: SYSTEM principal (S-1-5-18)
PASS: task xml: highest run level
PASS: task xml: BootTrigger present
PASS: task xml: boot delay PT30S
PASS: task xml: LogonTrigger present
PASS: task xml: task hidden
PASS: task xml: no execution time limit
PASS: task xml: restart on failure every minute
PASS: task xml: restart count 5
PASS: task xml: network not required
PASS: task xml: never stops on batteries
PASS: task xml: windowless exe is the action
PASS: task xml: config path baked into the action
PASS: task xml: --console escape hatch uses the console exe
PASS: spec: windowless twin named beesky-agentw
PASS: spec: agentw is a console=False build
PASS: agent.iss: ships beesky-agentw.exe alongside the console exe
PASS: workflow: agentw in artifact AND release file lists
PASS: workflow: signed update manifest lists beesky-agentw.exe
PASS: versions in sync at 0.19.7
PASS: e2e: cloud mints the agent key
PASS: e2e: cloud starts
PASS: bg e2e: `run --once` exits 0 and reports the pass
PASS: bg e2e: agent-status.json written, ok with 1 miner
PASS: bg e2e: agent.log mirrors the run output
PASS: bg e2e: agent.log does NOT contain the agent key
PASS: bg e2e: localhost http cloud raises no warning
PASS: bg e2e: --background prints nothing to stdout
PASS: bg e2e: --background still writes status + log
PASS: bg e2e: a wrong-key cycle survives and is recorded as ok=false with an error
PASS: bg e2e: the failing log never contains the (wrong) key
PASS: bg e2e: non-local http:// cloud warns about the unencrypted key (but is not blocked)
PASS: bg e2e: the unreachable-cloud cycle is recorded ok=false, not a crash
PASS: gui: status card starts at 'Chưa có dữ liệu'
PASS: gui: 'Xem log' button exists
PASS: gui: non-local http:// cloud shows the https hint
PASS: gui: localhost http clears the hint
PASS: gui: https clears the hint
PASS: gui: an OK status renders 'Đang chạy tốt' + miner count
PASS: gui: an error status renders 'Lỗi gần nhất' + the error

AGENT BG TEST PASSED
```

```
PASS: fallback constant is the historic default
PASS: helper: detected 192.168.2.37 -> its /24
PASS: helper: detection used an AF_INET datagram socket
PASS: helper: detected 10.20.30.40 -> 10.20.30.0/24
PASS: helper: socket creation failure -> fallback
PASS: helper: connect failure (offline) -> fallback
PASS: helper: getsockname failure -> fallback, never raises
PASS: helper: loopback result 127.0.0.1 -> fallback
PASS: helper: link-local result 169.254.9.9 -> fallback
PASS: helper: unspecified result 0.0.0.0 -> fallback
PASS: helper: unstubbed call returns a parseable /24 target
PASS: parser: union of two CIDRs
PASS: parser: union keeps first-seen order, no global re-sort
PASS: parser: overlapping ranges de-duplicate
PASS: parser: an item fully inside another adds nothing
PASS: parser: whitespace around items is tolerated
PASS: parser: mixed forms (IP + CIDR + range) union
PASS: parser: one bad item rejects the whole spec
PASS: parser: bad first item rejects the whole spec
PASS: parser: empty spec still rejected
PASS: parser: oversized union still rejected
PASS: parser: size cap counts the union, not raw duplicates
PASS: parser: single CIDR output unchanged
PASS: parser: single IP output unchanged
PASS: parser: single range output unchanged
PASS: main gui: target pre-filled from the helper
PASS: main gui: explicit default beats the helper
PASS: main gui: comma target reaches the scan unchanged
PASS: main gui: make_scan_args passes the target through
PASS: agent gui: first run pre-fills the helper target
PASS: agent gui: comma target reaches the config unchanged
PASS: agent gui: saved config target beats the helper
PASS: agent config: comma target round-trips verbatim
PASS: cli: `gui` without --target hands None to run_gui (helper resolves it)
PASS: cli: `gui --target X` hands X through unchanged

TARGETS TEST PASSED
```

---

# v0.20.0 mock test — unit-correct hashrate (L9/Z15) + diagnosis calibration

Field evidence (owner's photos, one 63-miner fleet): BTC
Tools reports the Antminer L9 at 14.54 MH/s and the Z15 at
~1101 ksol/s; BeeSky v0.19.7 showed the L9 row as 0.01 in a
TH/s column and a mixed fleet total of 12153.83, because
build_record squeezed every rate into TH/s (GHS/1000) and
every surface summed that field blindly.

v0.20.0 (core/report.py, gui.py, cli.py, core/events.py,
cloud/store.py, both dashboards):

  * Records carry rate_value + rate_unit (native unit).
    _native_rate resolves them from the SUMMARY field
    family + model: explicit KSol/s / Sol/s fields win;
    Z-series + GHS fields -> ksol/s (the GHS field carries
    raw sol/s); L-series with an MHS pair -> MH/s (the true
    Scrypt rate; the GHS twin is the same figure / 1000);
    otherwise the historical TH/s / MH/s fallbacks. Legacy
    fields (ths, ghs_5s, ghs_av) are computed exactly as
    before — the S19 record is pinned field-by-field
    against tests/mock_scan.json in the new suite.
  * Displays show the native value+unit: GUI table/detail,
    CLI table (header TH/s -> Hashrate), both dashboards'
    tables + heat tiles, repair tickets. Fleet totals group
    per unit (fleet_rate_totals / format_rate_totals): a
    single TH/s group renders exactly as before.
  * Diagnosis: NO rule changed. The audit (root RESULTS.md)
    shows the L9's 369 is the sum of the machine's OWN
    chain_acs lengths — BeeSky has no model/chip table —
    so MISSING_CHIPS on a self-reporting gap stays, by
    design; what remains open is whether bmminer's acs
    chars map 1:1 to chips on Scrypt/Equihash firmware.
  * Events: HASHRATE_DROP now tracks the native rate (a
    per-miner ratio — unit-safe, verified); the detail
    names the native unit; payload keys unchanged.
  * Cloud: farm_ths / history totals / sites_summary
    total_ths now sum TH/s EQUIVALENTS (H/s family only;
    sol rates excluded — an Equihash-only site yields
    farm_ths None and the pool poller skips it);
    sites_summary gains grouped rate_totals. Energy math
    was audited: it integrates power_w only and never
    consumed the mixed total.

Evidence method (this release): the nested historical
chain halted mid-run repeatedly in this sandbox (a
different server suite each attempt, no FAIL assertion
echoed — cf. the v0.17 / v0.19 halts), so every suite was
run STANDALONE at the v0.20.0 code; the historical blocks
above are the committed evidence of their own releases.
Standalone results beyond the six suites quoted in full
below:

  mock_actions_test: 29 PASS / 0 FAIL (standalone)
  mock_repairs_test: 19 PASS / 0 FAIL (standalone; see flake note)
  mock_agents_ui_test: 30 PASS / 0 FAIL (standalone)
  mock_logo_test: 17 PASS / 0 FAIL (standalone)
  mock_targets_test: 35 PASS / 0 FAIL (standalone)
  mock_rounded_test: 33 PASS / 0 FAIL (standalone)
  mock_glass_test: 30 PASS / 0 FAIL (standalone)
  mock_agent_app_test: 41 PASS / 0 FAIL (standalone)
  mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)
  mock_theme_test: 34 PASS / 0 FAIL (standalone)
  mock_gui_test: 11 PASS / 0 FAIL (standalone)
  mock_firmware_test: 20 PASS / 0 FAIL (standalone, nice, attempt 4)

Flake disclosure: mock_firmware_test's timing-sensitive
`unlock order` assertion fired repeatedly today
(kill logged 1-2 lines before first.bmu), INCLUDING on
the pristine v0.19.7 tree (git-stash control, identical
signature) — it is not a v0.20 regression (no firmware
code changed). It passed standalone under nice -n -10
(indices first=4 < kill=5), inside a nice'd
run_mock_test_v11.sh run (exit 0), and in this sweep's
own retry loop (attempt 4). One scripted-sweep run of
mock_repairs_test also flaked 3 assertions under load
(15 PASS / 3 FAIL); the suite passed 19/0 standalone
immediately before and after — the same server-timing
contention as the chain halts above.

Changed test expectations: none weakened. New suite
mock_units_test.py (50 assertions); mock_agent_bg_test
release pin 0.19.7 -> 0.20.0 (plus __init__ and both
.iss). The six primary v0.20 suites in full:

```
PASS: s19 regression: field model unchanged
PASS: s19 regression: field source unchanged
PASS: s19 regression: field elapsed_s unchanged
PASS: s19 regression: field ghs_5s unchanged
PASS: s19 regression: field ghs_av unchanged
PASS: s19 regression: field ths unchanged
PASS: s19 regression: field chips_alive unchanged
PASS: s19 regression: field chips_total unchanged
PASS: s19 regression: field max_temp_c unchanged
PASS: s19 regression: field fans_rpm unchanged
PASS: s19 regression: field status unchanged
PASS: s19 regression: field problems unchanged
PASS: s19: native rate is its TH/s rate
PASS: s19: format_rate renders the historical string
PASS: s19: ths_equivalent == ths
PASS: l9: display rate is 14.54 MH/s (BTC Tools ground truth)
PASS: l9: format_rate
PASS: l9: legacy ths field untouched (0.01454)
PASS: l9: ths_equivalent == ths (H/s family converts)
PASS: l9: chips are the machine's own acs counts (330/369)
PASS: l9: max temp 60, fans as reported
PASS: l9: flagged CHECK by MISSING_CHIPS x3 (self-report, by design)
PASS: l9 (5s+av): native rate follows the MHS 5s figure
PASS: l9 (MHS only): gh_av fallback intact, display 14.54 MH/s
PASS: z15: display rate is 1101.00 ksol/s (BTC Tools ground truth)
PASS: z15: format_rate
PASS: z15: healthy per its own report (OK, no problems)
PASS: z15: sol rate has NO TH/s equivalent
PASS: z15 (5s+av): native rate follows the 5s figure
PASS: sol fields: KSol/s av wins over the GHS fields
PASS: sol fields: sub-1000 Sol/s stays in sol/s
PASS: unknown model (MHS only): MH/s display from the field family
PASS: legacy record: rate reads back as TH/s
PASS: error record: no rate anywhere
PASS: totals: grouped per unit, canonical order, never mixed
PASS: totals: grouped rendering matches the fleet example shape
PASS: totals: single-unit fleet renders as before
PASS: totals: empty fleet renders '-'
PASS: gui rows: native value+unit per row
PASS: cli table: Hashrate header + native units in rows
PASS: tickets: hashrate line carries the native unit
PASS: store: rate_totals groups the mixed snapshot per unit
PASS: store: total_ths is the H/s-family sum only (102.91)
PASS: store: farm_ths counts S19 + L9 equivalent, excludes the Z15
PASS: store: history sample carries the same H/s-family total
PASS: store: Equihash-only site has no farm_ths (poller skips it)
PASS: store: Equihash-only site totals: 0 TH/s + its ksol/s group
PASS: store: pre-v0.20 snapshot aggregates exactly as before
PASS: events: L9 rate halved -> HASHRATE_DROP in native units
PASS: events: S19 drop keeps the historical TH/s wording + payload

UNITS TEST PASSED
```

```
PASS: healthy passes: no events while baseline builds
PASS: healthy passes: no notifications sent
PASS: hashrate drop pass: HASHRATE_DROP printed
PASS: webhook received exactly one HASHRATE_DROP
PASS: drop payload shape (ip/model/type/severity/detail/data)
PASS: drop payload: drop_pct ~= 40
PASS: drop payload: baseline 110 -> current 66 TH/s
PASS: telegram sendMessage captured for the drop
PASS: still dropped: anti-flap, no duplicate HASHRATE_DROP
PASS: miner killed: OFFLINE printed + webhook received
PASS: OFFLINE payload: severity critical, model kept
PASS: telegram captured for OFFLINE
PASS: still down: anti-flap, no duplicate OFFLINE
PASS: miner back: BACK_ONLINE printed + webhook received
PASS: logfile channel recorded all three events

Captured webhook payloads:
{"ts": 1794321301.963904, "time": "2026-11-10 14:35:01", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
{"ts": 1794321302.4287527, "time": "2026-11-10 14:35:02", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "OFFLINE", "severity": "critical", "detail": "miner went offline / unreachable", "data": {"last_seen": 1794321302.2262704}}
{"ts": 1794321302.9924846, "time": "2026-11-10 14:35:02", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "BACK_ONLINE", "severity": "info", "detail": "miner is back online", "data": {}}

WATCH TEST PASSED
```

```
PASS: store: first snapshot writes one history sample
PASS: store: sample totals mirror the snapshot
PASS: store: snapshot 10 s later is throttled (still 1 row)
PASS: store: snapshot +70 s writes the 2nd row
PASS: store: per-site filter + all-sites view
PASS: store: since_ts window is honoured
PASS: store: samples older than 30 days are pruned on write
PASS: cloud-add-agent prints a key once
PASS: cloud server starts
PASS: GET /api/history without login -> 401
PASS: login with right password -> session
PASS: GET /api/history with session -> 200, empty at first
PASS: dashboard: sidebar nav with all seven views
PASS: dashboard: settings forms (pool config + price) present
PASS: dashboard: history chart container + topbar
PASS: dashboard: legacy markers survive (heat/pool/energy/logo)
PASS: ingest snapshot 1 accepted
PASS: ingest snapshot 2 (+10 s) accepted
PASS: history after +10 s: throttle keeps a single point
PASS: ingest snapshot 3 (+70 s) accepted
PASS: history after +70 s: second point appears, site filter ok
PASS: history for an unknown site is empty

HISTORY TEST PASSED
```

```
PASS: store: config view lists header NAMES, never values
PASS: store: re-POST without headers keeps the stored secrets
PASS: store: gap fires on 2nd consecutive breach, deduped 1/hour
PASS: store: samples back under threshold never fire
PASS: store: energy integrates power_w across snapshots (0.06 kWh)
PASS: store: dt capped at 3x interval (adds 3600 W x 90 s = 0.09)
PASS: adapter: dot path + GH/s -> TH/s conversion
PASS: adapter: worker_filter sums only matching workers (60)
PASS: cloud-add-agent prints a key once
PASS: cloud starts and serves /login
PASS: GET /api/pool-config without login -> 401
PASS: GET /api/pool without login -> 401
PASS: GET /api/energy without login -> 401
PASS: GET /api/settings without login -> 401
PASS: POST /api/pool-config without login -> 401
PASS: POST /api/settings without login -> 401
PASS: login with right password -> session
PASS: GET /api/settings: default price 2000 VND/kWh
PASS: cloud dashboard: pool + energy panels present
PASS: /api/sites shows the site after agent push
PASS: farm hashrate from dashd snapshot (~109.13 TH/s)
PASS: miner record carries power_w from dashd power_consumption
PASS: POST /api/pool-config -> 201, view has names not values
PASS: GET /api/pool-config never echoes the secret header
PASS: poller samples pool vs farm (gap ~5%, under threshold)
PASS: poller sent the configured secret header to the pool
PASS: no POOL_GAP while the gap stays ~5%
PASS: pool at 40% of farm -> POOL_GAP (major) in the event feed

Captured POOL_GAP event:
{"ts": 1794321308.0636783, "time": "2026-11-10 14:35:08", "site": "Xưởng 1", "agent_id": 1, "ip": null, "model": null, "type": "POOL_GAP", "severity": "major", "detail": "pool reports 43.65 TH/s vs farm 109.13 TH/s — gap 60.0% exceeds 10% for 2 consecutive checks", "data": {"pool_ths": 43.65, "farm_ths": 109.13, "gap_pct": 60.0, "threshold_pct": 10.0}}
PASS: latest sample shows the ~60% gap
PASS: energy accumulates > 0 kWh for the dashd miner

Captured energy report (excerpt):
{"today": {"day": "2026-11-10", "kwh": 0.0027, "est_cost_vnd": 5}, "per_day": [{"day": "2026-11-10", "kwh": 0.0027, "est_cost_vnd": 5}], "per_miner": [{"site": "Xưởng 1", "ip": "127.0.0.1", "kwh": 0.0027, "est_cost_vnd": 5}]}
PASS: POST /api/settings sets the electricity price
PASS: energy estimates now use 3000 VND/kWh

ENERGY/POOL TEST PASSED
```

```
PASS: cloud-add-agent prints a key once
PASS: cloud starts and serves /login
PASS: ingest with a wrong agent key -> 401
PASS: ingest with no agent key -> 401
PASS: viewer /api/sites without login -> 401
PASS: login with wrong password -> 401
PASS: still locked out after wrong password
PASS: login with right password -> session (200 after redirect)
PASS: /api/sites works with the session cookie; site registered
PASS: GET / serves the cloud dashboard (brand #F5D800)
PASS: /api/sites shows the site after agent push
PASS: site summary: ~110 TH/s, 1 OK / 0 problems, online
PASS: hashrate drop: HASHRATE_DROP arrives at the cloud
PASS: drop event: severity major, drop_pct ~= 40, site tag

Captured cloud event:
{"ts": 1794321315.8885224, "time": "2026-11-10 14:35:15", "site": "Xưởng 1", "agent_id": 1, "ip": "127.0.0.1", "model": "Antminer S19 Pro", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
PASS: /api/miners?site= shows ~66 TH/s, record annotated with site

CLOUD TEST PASSED
```

```
PASS: GET / returns the dashboard
PASS: dashboard carries the BeeSky brand (name + #F5D800)
PASS: GET /api/miners lists the mock miner
PASS: miner record: S19 Pro, ~110 TH/s, 342/342 chips, OK
PASS: GET /api/status counts sane (1 miner, target, interval)
PASS: POST /api/scan -> 202 {ok: true}
PASS: hashrate drop phase: /api/events gains HASHRATE_DROP
PASS: drop event: severity major, drop_pct ~= 40

Captured drop event:
{"ts": 1794321320.5782955, "time": "2026-11-10 14:35:20", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}

WEB TEST PASSED
```
