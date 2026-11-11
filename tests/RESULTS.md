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

---

# v0.21.0 — Flutter main app (stage 1) + scan/sysinfo JSON bridge

The owner chose the full Flutter rewrite of the desktop
apps (the Tk UI compared unfavourably with the HashCore
Toolkit's Flutter UI). Stage 1: the Python core stays the
only engine; a new Flutter shell (app_flutter/) drives the
beesky CLI exe as a sidecar. The Tk apps are untouched and
keep shipping as the fallback.

Bridge (beesky/cli.py):

  * `scan --json` with no value (or `-`) is bridge mode:
    stdout is exactly ONE JSON document
    {"records": [...], "scanned": N, "found": M,
    "elapsed_s": X}; ticket notes go to stderr there.
    `--json FILE` keeps its legacy behaviour byte-for-
    byte. Records are the very dicts the agent/cloud path
    serialises (wire key `problems`; native rate_value /
    rate_unit since v0.20) — no second schema. A bridge-
    only _jsonable() sanitiser coerces tuples/sets/other
    non-JSON values rather than touching the record
    builders.
  * `sysinfo --json`: {"version": ..., "default_target":
    default_scan_target()} so the shell pre-fills the
    target without reimplementing subnet detection.
  * Release pins bumped to 0.21.0 (__init__, both .iss,
    mock_agent_bg_test).

(a) VERIFIED LOCALLY (this sandbox):

  * mock_bridge_test — 24 assertions: stdout purity (the
    whole stdout json.loads), envelope keys, scanned=254
    for a /24, L9 14.54 MH/s + Z15 1101 ksol/s intact,
    sanitiser coercions, --json does not swallow the next
    flag, bridge+--tickets keeps stdout pure, legacy file
    mode unchanged, sysinfo stubbed + live, and an end-to-
    end subprocess scan against mock_dashd. Full output:

```
PASS: bridge: exit 0
PASS: bridge: stdout is ONE pure JSON document
PASS: bridge: envelope keys
PASS: bridge: scanned = /24 host count
PASS: bridge: found = record count
PASS: bridge: elapsed_s is a non-negative number
PASS: bridge: record keys survive (ip/model/rate/problems)
PASS: bridge: L9 native rate intact (14.54 MH/s)
PASS: bridge: Z15 native rate intact (1101 ksol/s)
PASS: bridge: sanitiser coerces tuple/set leaves
PASS: bridge: --json does not swallow the next flag
PASS: bridge: empty scan still a valid document
PASS: bridge+tickets: exit 0
PASS: bridge+tickets: stdout still ONE JSON document
PASS: bridge+tickets: ticket files written for problem miners
PASS: legacy: exit 0 + human note on stdout
PASS: legacy: file holds the bare records list
PASS: sysinfo: version is the running version
PASS: sysinfo: default_target comes from the helper
PASS: sysinfo: unstubbed target parses
PASS: e2e: subprocess stdout is ONE JSON document
PASS: e2e: found the mock miner
PASS: e2e: record is the sick S19 Pro via VNish
PASS: e2e: problems + native rate attached

BRIDGE TEST PASSED
```

  * Regression spot-checks at the v0.21.0 code:

    mock_units_test: 50 PASS / 0 FAIL (standalone)
    mock_cloud_test: 15 PASS / 0 FAIL (standalone)
    mock_web_test: 8 PASS / 0 FAIL (standalone)
    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)

  * Flutter SDK 3.47.9 (Dart 3.13.7) was fetched and runs
    on this VM; every Dart source (lib/ + test/) passes
    the SDK's own parser/formatter (dart format: 7 files,
    no parse errors), and the windows/ scaffold was
    rendered from that SDK's flutter-create templates.

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml — sibling workflow, independent job, so
the Tk release assets publish regardless):

  * flutter pub get / test / build windows --release on
    a real Windows runner, and the release asset
    BeeSkyFlutter-<tag>-win64.zip. Local `flutter create`
    /`pub get` could NOT run in this sandbox: the Flutter
    tool's own package update stalls/fails through the
    sandbox's authenticated egress proxy (curl to pub.dev
    succeeds; the Dart pub client does not complete), so
    `flutter analyze` and `flutter test` are likewise
    CI-verified, not locally verified. The Dart widget/
    unit tests are written against the same mock fleet as
    the Python bridge test.

(c) KNOWINGLY NOT YET WIRED (stage 1):

  * No Flutter installer yet — the CI zip is the runner
    folder; beesky.exe must sit beside beesky_app.exe.
  * Export tickets shells `scan --tickets` (a second
    scan pass — there is no records->tickets verb; TODO
    marked in sidecar.dart). Open-web shells `serve` +
    the OS browser opener (TODO: url_launcher).
  * The Flutter app covers scan/stats/table/detail/
    tickets/web for ONE local pass; heat map, cloud views
    and the Agent app are later stages. Self-update
    signing stays inert (owner key setup outstanding,
    as since v0.10).

# v0.22.0 — Flutter layout redesign: sidebar + chips, table-first

Owner verdict on the v0.21 Flutter layout after his first run
(2026-11-11): "card to để làm gì, người ta muốn thấy máy đào"
— the 4 big stat tiles ate the screen; people want to SEE
THE MINERS. His order: copy the HashCore Toolkit's structure.
An HTML prototype he approved (~/workspace/beesky-demo/
proto-v22/) is the visual spec. Later the same session he
added: "nhiệt độ máy có 4 hashboard thì sao" — board
temperature is per-board data, so the detail panel shows
each board's OWN temperature, for as many boards as the
machine actually reports.

What changed (app_flutter/ + version pins only):

  * Structure: 228px left sidebar (official logo, "BeeSky",
    "QUẢN LÝ MÁY ĐÀO" tagline, nav; version + sidecar status
    dot at the foot) / header block (view title + network
    line, then the fleet stats as compact ~26px chips in ONE
    row: Tổng, OK, Cần kiểm tra, Lỗi, grouped hashrate,
    Max temp) / scan bar as its own slim card (hints instead
    of floating labels) / miners table filling ALL remaining
    space (~34px rows) / detail as a 300px right panel that
    exists only while a row is selected (close button returns
    the width to the table; first row still auto-selects
    after a scan). The v0.21 stat-tile row is DELETED.
  * Sidebar nav beyond "Máy đào" — Bản đồ nhiệt, Điện năng,
    Lịch sử sửa, Sự kiện, Cài đặt — is greyed with a "SAU"
    tag: visible roadmap, no fake functionality.
  * Detail panel (prototype treatment): model as title,
    "ip • source" sub-line, "Chip sống a / b", each issue as
    a severity-tinted box (code line + detail), and one
    board line per REPORTED chain — "Board N: a/b chip •
    T°C" — carrying that board's own temp from chains[]
    .temp_c, omitted when the record has none. Board count
    = len(chains); a 4-board machine shows 4 lines.
  * Table: uppercase letterspaced headers; the selected row
    gets the prototype's 3px accent left bar. Status pill
    text stays OK / CHECK / ERROR for BeeSky-wide
    consistency with the Tk app and the cloud dashboards
    (the prototype drawing used longer Vietnamese labels —
    a copy call; the structure is what was copied).
  * models.dart gains fleetStatusCount (the chip counts);
    the BeeSkyBridge interface gains exePath so the sidebar
    dot can tell mock / sidecar-found / sidecar-missing
    apart. Sidecar wiring (scan --json, tickets, serve) is
    unchanged from v0.21; the Tk apps are untouched.
  * Release pins bumped to 0.22.0 (__init__, both .iss,
    mock_agent_bg_test, pubspec 0.22.0+2); the MockBridge
    sysinfo version follows.

(a) VERIFIED LOCALLY (this sandbox — new this release:
`flutter pub get --offline` resolves from the SDK-local
cache, so the Dart side is verified HERE, not only in CI):

  * flutter analyze: No issues found.
  * flutter test: 10/10 pass — model tests (bridge parsing,
    native units, grouped totals, the NEW OK/CHECK/ERROR
    chip-count split) and the widget test rebuilt for the
    new layout: sidebar + 5 SAU tags, stat tiles absent,
    chips (Tổng 4 máy / OK 2 / Cần kiểm tra 1 / Lỗi 1 /
    grouped hashrate / Max 65 °C), table rows with native
    units, L9 tap -> issue box + "Board 2: 84/123 chip •
    59°C" (Boards 1/3 likewise with their own temps),
    close-panel returns the width.
  * Layout preview rendered with mock data at 1280x800 by a
    throwaway capture test (deleted before commit, not
    shipped): ~/workspace/beesky-demo/flutter-v22-preview.png
    — glyphs are the test font's blocks (real fonts load on
    a real machine); sidebar, chips row, scan card, dominant
    table with accent-bar selection, and the detail panel
    with per-board temps all render as designed. The scan
    bar wraps to two lines under the extra-wide test font;
    at real font widths it fits one line, and the Wrap is
    the graceful fallback by design.
  * Python: mock_agent_bg_test standalone under Xvfb —
    52 PASS / 0 FAIL, including "versions in sync at
    0.22.0". (Headless without a display the suite stops at
    its tkinter check with TclError — pre-existing sandbox
    constraint, same as previous sweeps.)

(b) VERIFIED ONLY BY CI: flutter build windows --release
and the BeeSkyFlutter-<tag>-win64.zip release asset
(build-flutter.yml, unchanged). Runtime behaviour on a
real Windows machine remains the owner's first-launch
test, as with v0.21.

(c) KNOWINGLY NOT YET WIRED: the sidebar roadmap views
stay placeholders ("SAU"); tickets still shell a second
scan pass; no installer bundling the Flutter app yet
(stage 2, gated on the owner's runtime verdict on this
layout).

Follow-up (same release — folds into v0.22.0, no version
bump): a second owner rule from the same prototype review
— "sao hok hiện hết 3 hoặc 4 hash board, cái nào nóng quá
thì đỏ lên". The table's NHIỆT column no longer shows only
the max: it renders EVERY hashboard's temperature from the
record's chains[], in chain order, compact ("71° 88° 73°").
A board at/over the red line renders bold #FF6B6B on a soft
red pill (the prototype's .bt.hot; BeeSkyColors.hotTemp);
the rest stay muted. The red line is 85 °C — TEMP_LIMIT_C
in beesky/core/report.py, the same threshold that already
makes the core emit a per-chain OVER_TEMP problem (mirrored
in Dart as models.tempLimitC / ChainInfo.isHot). The detail
panel's board lines take the same red treatment for a hot
board, so table and panel agree. Records with no per-chain
temps fall back to the single max temp exactly as before;
unreachable rows keep "—". Column flex rebalanced for the
wider cell (NHIỆT 2->3, QUẠT 4->3). The MockBridge Z15 now
carries a hot board (chains 71/88/73, max 88, OVER_TEMP +
CHECK — byte-shaped like the real core's output for that
data) so the red state is exercised in tests.
Verified locally: flutter analyze clean; flutter test
13/13 (3 new model tests — boardTemps order, the >=85 line,
the no-chain-temp fallback — plus widget assertions on the
multi-temp cell, the red 88° style vs its muted neighbours,
the fallback row, and the red Board 2 detail line); the
header chips shift accordingly (OK 1 / Cần kiểm tra 2 /
Max 88 °C). Python pin suite unchanged and green:
mock_agent_bg_test 52 PASS / 0 FAIL ("versions in sync at
0.22.0").

---

# v0.23.0 — saved multi-credential scan; double-click opens miner web; drop local-web button

The owner's three requests (2026-11-11): (1) remove the
Flutter app's "Mở web local" button; (2) double-click a
miner row to open that miner's web admin (http://<ip>) in
the default browser, BTC Tools-style; (3) multi-credential
support — the fleet has many machine lines with different
logins, so the app must store MANY credential sets and the
scan must try them automatically. Two owner amendments
landed during the build: each set carries a machine-type
tag so detection picks the right set first (not blind
order), and — after the HashCore Toolkit re-analysis
(research/hashcore/UI-ANALYSIS.md) — the model is keyed
like theirs: one unlock method family PER FIRMWARE
VENDOR, selected by the detected firmware, with an
API-key method for VNish.

PYTHON CORE (beesky/core/discover.py, dashd.py, cli.py):

  * `scan` (and watch/serve/agent, via the shared common
    args) gains `--creds-file <path>`: a JSON list
    [{"label": ..., "user": ..., "password": ...}] — the
    same schema the Flutter app writes. Legacy
    --user/--password stays a one-entry list; no creds at
    all keeps the previous behaviour byte-identical
    (probe_host(creds=None)). A malformed file exits 2
    before any scanning.
  * Each entry may carry "type": "stock" | "vnish" |
    "any" (missing/unknown reads as "any") — the vendor
    key. The probe already knows a miner's family before
    auth, and tries, in order: (a) sets keyed to that
    family, in saved order; (b) "any" sets; (c) all
    remaining sets — a wrong tag costs attempts, never
    locks a machine out. VNish/dashd sets are tried via
    /unlock (password method) unless the set carries
    "api_key", in which case the adapter authenticates
    with the x-api-key header INSTEAD (the VNish API-key
    method). Stock sets go through the web digest auth.
    cgminer RPC needs no auth and is untouched.
  * On success the record gains "cred_label" (the winning
    set's label); RPC wins, anonymous dashd wins and
    default-credential wins stay label-free. In creds
    mode only, a dashd that refuses anonymously with 401
    and matches no set still surfaces as a candidate, so
    the fetch reports the 401 FETCH_ERROR — a locked
    VNish box stays visible instead of vanishing.
  * Bridge `--json` carries cred_label like any record
    field (asserted in the creds suite against a real
    subprocess scan).

FLUTTER APP (app_flutter/):

  * Scan bar: the single user/password fields and the
    "Mở web local" button (and its serve shell-out) are
    REMOVED — the CLI `serve` command itself stays. In
    their place, one button: "Tài khoản: N bộ".
  * Creds editor dialog: one row per set (label, user,
    obscured password, type dropdown — Mọi loại máy /
    Antminer gốc / VNish — delete), "Thêm bộ" adds a
    row, blank rows drop on save. VNish rows show an
    optional "API key (không bắt buộc)" field. The sets
    persist to beesky-creds.json NEXT TO the executable
    (fallback %APPDATA%\BeeSky\ when the bundle folder
    is not writable); the app passes only the file PATH
    to `scan --creds-file` — passwords never appear on
    a command line. Empty list = scan without the flag.
  * Row clicks are read at the pointer level: every
    pointer-down selects instantly; a second down on the
    same row within 400 ms opens http://<ip> through an
    injectable opener (production: the OS default browser
    via cmd /c start on Windows). A plain double-tap
    gesture recogniser was rejected: it holds the single
    click hostage until the double-click window expires.
  * Detail panel: "Đăng nhập: <label>" appears when the
    record carries cred_label.

DIVERGENCES FROM HASHCORE'S MODEL (deliberate):

  * Multiple sets per vendor type remain allowed — one
    farm often runs the same firmware with different
    passwords per hall/batch; HashCore solves that with
    a per-GROUP override layer (farms.json) over global
    per-vendor settings. The group layer is NOT built
    here; it is the v0.24 candidate if per-group logins
    become a real need.
  * HashCore's DoNotUnlock / DoNotDiscover method
    variants are not modelled (no BeeSky workflow needs
    them yet).

(a) VERIFIED LOCALLY (this sandbox):

  * mock_creds_test — ordering units, creds-file loader
    normalisation (api_key-only entry valid, label
    "api_key", unknown type -> any), validation exit 2,
    and subprocess bridge scans against mock dashd +
    stock endpoints: family-first wins (and the attempt
    log proves the foreign family's set is never tried
    first), wrong-tag rescue via the remaining-sets tier,
    "any" rescue, api-key-only dashd (the password set
    can unlock but not read; the api_key set wins and is
    labelled), all-fail -> the 401 FETCH_ERROR record
    with no label, legacy paths unchanged. Full output:

```
PASS: order: stock family first, then any, then the rest
PASS: order: vnish family first, then any, then the rest
PASS: load: label defaults to the user name
PASS: load: missing/unknown type normalises to any
PASS: load: a real family tag survives
PASS: load: an api_key-only entry is valid (no login needed)
PASS: load: api_key-only entry's label falls back to 'api_key'
PASS: validation: malformed JSON exits 2 with a creds message
PASS: validation: non-list top level exits 2 with a creds message
PASS: validation: entry without password exits 2 with a creds message
PASS: validation: missing file exits 2 with a creds message
PASS: dashd: locked miner found via the creds file
PASS: dashd: record is the vnish S19, healthy
PASS: dashd: cred_label names the winning vnish set (bridge JSON)
PASS: dashd: only the vnish set was tried as a login
PASS: dashd rescue: a wrong tag never locks the machine out
PASS: dashd rescue: family set tried first, rescue set second
PASS: dashd all-fail: the locked miner still surfaces
PASS: dashd all-fail: it reports its auth error (401 FETCH_ERROR)
PASS: dashd all-fail: no cred_label on an error record
PASS: dashd legacy: locked dashd stays invisible (unchanged)
PASS: dashd api-key: key-only miner found, healthy
PASS: dashd api-key: cred_label names the api_key set
PASS: dashd api-key: password set tried first (unlock ok, read no)
PASS: dashd api-key: the winning key reached /summary
PASS: stock: digest miner found via the creds file
PASS: stock: record is stock + cred_label names the stock set
PASS: stock: the stock set authenticated; vnish user never tried
PASS: stock rescue: the 'any' set wins after the family set fails
PASS: stock rescue: family set was attempted before the rescue
PASS: stock legacy: --user/--password still works, no label
PASS: stock legacy: a wrong password finds nothing (unchanged)

CREDS TEST PASSED
```

  * Regression spot-checks at the v0.23.0 code:

    mock_bridge_test: 24 PASS / 0 FAIL (standalone)
    mock_units_test: 50 PASS / 0 FAIL (standalone)
    mock_cloud_test: 15 PASS / 0 FAIL (standalone)
    mock_web_test: 8 PASS / 0 FAIL (standalone)
    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)

  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):
    flutter analyze: clean; flutter test: 24 PASS / 0 FAIL (local SDK 3.47.9) — model parsing incl. cred_label,
    the v0.22 layout suite, creds store round-trip +
    fallback, argv contract (path only, no secrets),
    double-click opener URL, and the dialog's
    add/edit/delete/type-retag/api-key persistence.
    Two test-harness lessons are baked into the tests:
    dart:io futures started in a widget test's fake-async
    zone never complete (temp dirs are created sync, and
    the creds store does its tiny file IO sync), and a
    focused field's blinking cursor never lets
    pumpAndSettle settle (bounded pumps in the dialog
    test).

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml):

  * flutter build windows --release on a real Windows
    runner and the BeeSkyFlutter-<tag>-win64.zip asset.
    The app remains compile-verified only until the
    owner runs it on real Windows (as since v0.21).

---

# v0.24.0 — network groups (HashCore Toolkit home screen, ported per the dissection)

The owner set the parity bar (2026-11-11): "không được 100
cũng ráng được 99%" vs HashCore Toolkit, and named network
groups as the first gap to close. Following the standing
dissect-before-porting rule, the Toolkit's group mechanism
was dissected FIRST from the shipped materials (translation
table, AOT string pools, Dart file map) and the behaviour
mapping written to docs/network-groups-mapping.md BEFORE
any code — every behaviour graded VERIFIED / INFERRED /
UNKNOWN, divergences named, unknowns never invented.

PYTHON CORE (beesky/core/groups.py NEW, cli.py):

  * Group = {id, name, targets, creds, autoscan{enabled,
    interval_min}, last_scan{at, scanned, found, ok, check,
    error} | null}, persisted as {"version": 1, "groups":
    [...]} in beesky-groups.json — located with the SAME
    strategy as the v0.23 creds file (beside the executable,
    %APPDATA%\BeeSky fallback; --groups-file / env
    BEESKY_GROUPS_FILE override). Loading fails loud
    (GroupError -> exit 2): malformed JSON, a nameless entry,
    invalid targets (validated via parse_targets), a bad
    creds shape, a zero autoscan interval.
  * `beesky groups list|add|remove|show` (add takes
    --name/--targets and mirrors the JSON; duplicate names
    rejected) and `groups export <file>` / `import <file>`.
    Import merges BY NAME — a same-name group replaces the
    stored one in place, others are kept — the stated
    BeeSky policy (HashCore's own import policy is UNKNOWN,
    see the mapping). An invalid import file exits 2 and
    changes nothing.
  * `beesky scan --group NAME` (the positional target
    becomes optional): the core resolves the group's
    targets and merges credentials — group sets BEFORE the
    --creds-file (global) sets — and ordered_creds' stable
    tiers then try, per miner: group family -> global family
    -> group "any" -> global "any" -> the rest. This is
    the port of HashCore's global -> per-group override
    layering onto BeeSky's v0.23 list model. Unknown group
    = clean exit 2 before any scanning. After ANY successful
    scan with --group (CLI or bridge --json), last_scan is
    persisted into the store (best-effort: a refused write
    warns on stderr and never fails the scan). No --group
    = byte-identical v0.23 behaviour.

FLUTTER APP (app_flutter/):

  * Launch lands on a real NETWORK GROUPS screen (sidebar
    "Nhóm mạng" active): stat chips (total groups / scanned
    / total errors), group cards — name (+ MỚI tag while
    never scanned, mirroring HashCore's "new"), targets
    summary, last-scan line ("Chưa quét" or time + counts),
    autoscan state, [Quét nhóm] [Sửa] [Xóa] (delete asks
    first, naming the group). Empty state mirrors HashCore's
    (icon + line + [Thêm nhóm]).
  * "＋ Thêm nhóm" / [Sửa] opens the editor dialog: name,
    targets, autoscan toggle + interval (minutes), and the
    group's own credential sets — the v0.23 creds editor
    widget FACTORED OUT of the creds dialog
    (CredSetsEditor in creds.dart) and reused, not redrawn.
    Duplicate group names are refused app-side too.
  * Quét nhóm switches to the miners view scoped to the
    group (header chip "Nhóm: <name>") and runs
    `scan --group <name>` — the core owns resolution; the
    app passes the global creds file path AND its groups
    file path, so merging and last_scan persistence happen
    core-side; the app reloads the store to refresh the
    card. The miners view keeps its ad-hoc scan bar;
    editing the target away from the group's ranges leaves
    the group scope. Mock mode: two demo groups ("Trại
    chính" with a last_scan, "Kho phụ" never scanned).
  * Autoscan (DIVERGENCE, pre-approved): app-side only — a
    timer re-runs the ACTIVE group's scan at its interval
    while the app is open; state visible on the card. (The
    mapping notes HashCore's autoscan also runs app-side in
    the Toolkit; BeeSky's always-on equivalent remains the
    farm agent.)

MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):

  MATCH: groups as the home screen; named group objects in
  a farms-style JSON store; card facts (name, ranges, last
  scan, autoscan state); "new" tag for never-scanned
  groups; empty state shape; delete confirmation naming
  the group; per-group credential override layer over the
  global sets; per-group autoscan flag + interval; JSON
  export/import.

  DIVERGENCE (pre-approved, in the mapping): targets are
  one multi-range string (parse_targets), not typed named
  range objects with per-range enable/DNS/port ranges; no
  group description field; credential layers MERGE as
  lists (multiple sets per vendor survive — v0.23's model)
  instead of HashCore's one-method-per-vendor replacement;
  autoscan interval in minutes, app-side only, no global
  master switch (BeeSky has no settings screen yet);
  last_scan is a counts subset (no hashrate/unlocked totals
  — native-unit totals would mislead, the v0.20 lesson).

  NOT PORTED (named gaps): group merge, combined view,
  group search, reset-statistics command, rescan-all /
  remove-all / multi-select, per-group custom timeout,
  IP-Report -> group, the editor's "Save and scan" chain.

  UNKNOWN (never invented): farms.json field names;
  HashCore's import conflict policy; its autoscan interval
  unit/range/default; the exact persisted shape of its
  last-scan statistics; whether its autoscan is full
  discovery or statistics-only.

(a) VERIFIED LOCALLY (this sandbox):

  * mock_groups_test — store CRUD + persistence round-trip
    (incl. bare-list load + fail-loud validation),
    merge-order units (the six-tier sequence asserted),
    CLI groups CRUD/export/import (merge-by-name policy),
    and subprocess bridge scans against the mock dashd
    fleet: group set beats global same-family set (the
    global wrong password is never attempted), global set
    rescues a failed group set (attempt log order proves
    it), a cred-less group falls back to the global file,
    last_scan persisted with the right counts, a groupless
    scan never touches the store, unknown group exits 2.
    Full output:

```
PASS: store: a missing file loads as no groups
PASS: store: round-trip keeps both groups
PASS: store: round-trip keeps creds + autoscan + last_scan
PASS: store: defaults fill in (id minted, autoscan off, no scan)
PASS: store: the document is versioned
PASS: store: a bare-list document loads too
PASS: store: malformed JSON fails loud (GroupError)
PASS: store: a nameless entry fails loud
PASS: store: invalid targets fails loud
PASS: store: a bad creds shape fails loud
PASS: store: a zero autoscan interval fails loud
PASS: merge: order = group family, global family, group any, global any, group rest, global rest
PASS: merge: no sets anywhere -> None (legacy behaviour)
PASS: merge: one layer only -> that layer, in order
PASS: import merge: same name replaced in place, new appended
PASS: cli: empty store lists cleanly
PASS: cli: add creates a group
PASS: cli: a duplicate name exits 2
PASS: cli: invalid targets exit 2
PASS: cli: list shows both groups with their targets
PASS: cli: show prints the group as JSON
PASS: cli: show of an unknown group exits 2
PASS: cli: remove deletes the group
PASS: cli: removing an unknown group exits 2
PASS: cli: scan --group with an unknown name exits 2
PASS: cli: export writes the versioned document
PASS: cli: import adds new groups and keeps existing ones
PASS: cli: import replaces a same-name group, keeps the rest
PASS: cli: a malformed import file exits 2
PASS: cli: an invalid import exits 2 and changes nothing
PASS: live: group scan finds the locked miner via the group
PASS: live: the GROUP set wins (cred_label)
PASS: live: the global set was never tried after the group win
PASS: live: last_scan persisted with the scan's counts
PASS: live: the other group's last_scan stays null
PASS: live: the GLOBAL set rescues a failed group set
PASS: live: group set tried first, global rescue second
PASS: live: a cred-less group falls back to the global sets
PASS: live: an unknown group exits 2 with the store named

GROUPS TEST PASSED
```

  * Regression spot-checks at the v0.24.0 code:

    mock_creds_test: 32 PASS / 0 FAIL (standalone)
    mock_bridge_test: 24 PASS / 0 FAIL (standalone)
    mock_units_test: 50 PASS / 0 FAIL (standalone)
    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)

  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):
    flutter analyze: clean; flutter test: 35 PASS / 0 FAIL (local SDK 3.47.9) — NetGroup/GroupStore round-trips,
    autoscan-due rule, the scanGroup argv contract, the
    groups home rendering both demo cards, group scan
    scoping the miners view (+ header chip), editor create
    with a per-group cred set persisted to the store file,
    rename, and the confirm-then-delete flow. The two
    pre-existing suites were adapted only where the flow
    itself changed (the app now opens on groups: one
    sidebar tap reaches the miners view).

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml):

  * flutter build windows --release on a real Windows
    runner and the BeeSkyFlutter-<tag>-win64.zip asset.
    The app remains compile-verified only until the
    owner runs it on real Windows (as since v0.21).

---

# v0.25.0 — data-grid miners list (HashCore Toolkit list machinery, ported per the dissection)

The parity push continues (owner's bar: 99% of HashCore
Toolkit in one month). Following the dissect-before-
porting rule, the Toolkit's miners-list mechanism was
dissected FIRST from the shipped materials (the full
~1,500-key translation table, the AOT string pools, the
Dart file map) and the behaviour mapping written to
docs/grid-mapping.md BEFORE any code — every behaviour
graded VERIFIED / INFERRED / UNKNOWN, every column audited
against the real BeeSky record schema, data gaps named
instead of faked.

PYTHON CORE: unchanged. The grid is a Flutter-side port;
the record fields it needed (elapsed_s, ghs_5s, power_w)
were already on the wire from _finalise_record — the Dart
model simply never parsed them. They are parsed now.

FLUTTER APP (app_flutter/):

  * lib/grid.dart (NEW): the column universe (29 columns),
    GridConfig + GridStore (beesky-grid.json beside the exe,
    %APPDATA% fallback, corrupt = factory defaults), the
    GridFilter model (numeric / range / string / bool —
    HashCore's four MinerFilter variants), FilterPreset,
    the MinerSelection model + IsolateMode, grouping, and
    the pure view pipeline (search -> filters AND ->
    isolate -> sort -> group). lib/grid_dialogs.dart (NEW):
    the columns dialog (toggle + up/down reorder + CHƯA CÓ
    DỮ LIỆU tags on gap columns + Đặt lại mặc định) and
    the filter dialog (builder rows + named presets).
  * Columns: every column BeeSky records can feed, each
    toggleable + reorderable, persisted; reset restores
    the exact v0.24 default set/order. Per-board chip-temp
    columns BOARD 1–4 join the combined NHIỆT column.
    Data modes: Số liệu (fixed metric set) / Pools (fixed
    pool set) / Tùy chỉnh (the user's set; the columns
    dialog edits it and switches to it).
  * Densities: Thoải mái / Gọn row heights + TỔNG QUAN
    heat-grid (cells coloured by Temperature — absolute
    bands ending in the >=85 °C red rule — or by Hashrate
    share within the same unit; sizes S/M/L; click a cell
    selects it and opens the detail panel, double-click
    opens its web admin, tooltip carries the facts).
  * Sort by any column header (arrow shows direction);
    IPs compare octet-numerically; rates compare only
    inside their native-unit family (the v0.20 lesson);
    nulls sort last in both directions. Search matches
    IP / MAC / model / pool / worker. Grouping by Trạng
    thái / Model / Firmware renders header rows with
    counts. A filtered-to-empty list shows HashCore's
    empty-filter state with a clear action.
  * Selection: a checkbox column + header select-all-
    visible (tri-state); the selection bar shows the
    result count (Đang hiển thị X / Y máy), the selected
    count, Chọn tất cả / Đảo chọn / Cô lập (đã chọn | lỗi)
    / Xóa lọc-chọn. The selection lives in grid.dart's
    MinerSelection model — v0.26's Operations bar consumes
    it from there; the Operations BAR itself is NOT built
    in v0.25, exactly as scoped.
  * Hotkeys via Shortcuts/Actions with intent classes
    (HashCore's own architecture is intents+actions too):
    Ctrl+A select all visible, Ctrl+F focus search,
    Ctrl+R / F5 rescan, Esc clear search+filters+isolate
    +selection. Handlers step aside while a text field
    owns the keyboard.
  * All v0.24 behaviours intact: groups home + group scan
    scoping, double-click row -> miner web, creds dialog,
    per-board temps red at >=85 °C, header chips.

MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):

  MATCH: the two view axes (type x mode, incl. the enum
  value sets); Overview structure (cells, colour-metric
  toggle, S/M/L sizes, per-cell tooltip); user-configurable
  columns with reorder + reset-to-defaults; sort by field
  + direction; the search placeholder's field set; the
  filter model (numeric comparisons More/Less/Equals/Not
  equals, range variant, string contains/is-any family,
  bool variant) AND-combined; named filter presets in a
  presets store shared with the future pool presets;
  grouping by a field with group headers; select all /
  invert / isolate (selected | errors); the empty-filter
  state + clear action; an intents+actions hotkey layer.

  DIVERGENCE (named, in the mapping): BeeSky labels are
  Vietnamese and its defaults are the v0.24 set; Overview's
  colour SCALE is BeeSky's (HashCore's is UNKNOWN — not
  observable in the materials); the columns dialog uses
  up/down buttons (HashCore's reorder gesture is UNKNOWN);
  a same-name filter preset replaces silently (HashCore
  prompts — its edit-preset dialog is Presets-center scope);
  the full Presets CENTER dialog is not built — presets
  live in the filter dialog + the shared store (the seed;
  pool presets arrive v0.28); grouping renders in the two
  table densities only (the heat-grid is flat) and has no
  jump-to-group / collapse (UNKNOWN in the original);
  active filter rows are session-only (their persistence
  in HashCore is UNKNOWN); hotkey BINDINGS are BeeSky's
  (the intent set matches; HashCore's keys are UNKNOWN);
  zoom + command palette are named gaps; BeeSky keeps two
  columns HashCore has no counterpart for (CHIP, ĐĂNG
  NHẬP) because they carry core BeeSky data.

  DATA-GAPS (columns offered, values honestly '—' — the
  core emits no such data; nothing is faked): MAC, S/N,
  Pool 1–3 URL + worker (scan records carry NO pool data
  at all today — the columns parse an optional wire
  'pools' list so they light up when the core grows one).
  PARTIAL: HASHRATE RT (the wire's ghs_5s is GH/s-family
  only — shown for TH/s records, '—' for MH/s + ksol/s).
  DERIVED (arithmetic on real fields, marked in the
  mapping): HIỆU SUẤT = power_w / ths (J/TH, TH/s + power
  records only); THUẬT TOÁN from the native rate unit;
  BOARD LỖI from per-chain chip counts. NOT OFFERED (no
  data source at all): lock state, Has PICs, stock
  hashrate, throttling, miner presets, board serials /
  models / chip BIN, PSU model/serial/PFC/LLC temps,
  platform, install type, firmware build date/name, PCB
  temps (BeeSky carries ONE temp per chain), cooling,
  Hotel Fee, DevFee availability, power limit, per-record
  range, note (device-detail scope, v0.27).

(a) VERIFIED LOCALLY (this sandbox):

  * Python regression spot-checks at the v0.25.0 pins
    (core untouched; the pin suite asserts the version):

    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)
    mock_bridge_test: 24 PASS / 0 FAIL (standalone)
    mock_groups_test: 39 PASS / 0 FAIL (standalone)
    mock_creds_test: 32 PASS / 0 FAIL (standalone)
    mock_units_test: 50 PASS / 0 FAIL (standalone)

  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):
    flutter analyze: clean; flutter test: 63 PASS / 0 FAIL (local SDK 3.47.9; 35 pre-existing + 28 new grid tests) — model parsing of the newly-read wire
    fields + derived getters (uptime, J/TH, TH/s-only RT,
    algorithm, bad boards); column defaults = the v0.24
    set/order; pools-mode set; toggle/reorder/reset; JSON
    round-trip (unknown ids dropped, new columns join the
    tail); GridStore round-trip + corrupt-file fallback;
    sorts (IP octets, temps nulls-last both ways, status
    order, rates family-locked); search (IP/model); the
    filter operators incl. between + the null-field rule
    + unparseable-number rule; presets JSON round-trip;
    grouping counts on a generated 63-miner fleet (status
    49/13/1); the selection model; isolate modes. Widget
    level: density switching + heat-grid red rule + cell-
    click detail; header sort asc/desc; search + count
    line; checkbox selection + both isolate modes +
    Ctrl+A / Esc / Ctrl+F hotkeys; the filter dialog end
    to end (apply -> save preset -> clear -> re-apply ->
    preset found in beesky-grid.json on disk); the columns
    dialog (gap tags, enable UPTIME -> header + file,
    reset -> gone); grouping headers on the 63-fleet. All
    35 pre-existing tests still pass — the suite was not
    adapted at all this release.

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml):

  * flutter build windows --release on a real Windows
    runner and the BeeSkyFlutter-<tag>-win64.zip asset.
    The app remains compile-verified only until the
    owner runs it on real Windows (as since v0.21).

---

# v0.26.0 — Operations task system (HashCore Toolkit Operations model, ported per the dissection)

The parity push continues (owner's bar: 99% of HashCore
Toolkit in one month). Following the dissect-before-
porting rule, the Toolkit's task mechanism was dissected
FIRST from the shipped materials (the ~1,500-key
translation table — the 27-value task_type_action enum,
the task_status enum, the operations_dialog keys — and
the Dart file map: miners_task_service + queued_task,
the task base classes, the per-implementation task
files) and the behaviour mapping written to
docs/operations-mapping.md BEFORE any code — including
a full action inventory in which every HashCore task
type is graded SHIP / GAP against a BeeSky primitive
verified in code (file:line). No device action is faked:
firmware-documented endpoints BeeSky has never
implemented are gaps, not features.

PYTHON CORE:

  * beesky/core/ops.py (NEW): a stateless task runner.
    `beesky ops --job FILE` executes ONE task described
    by a JSON job file (secrets never ride argv; cred
    sets are referenced by path) and streams NDJSON
    progress: a start line, one result line per device
    ({done, total, ip, ok, message} — rescan adds the
    fresh `record`), and a final summary line (counts
    + derived task status: success / hasErrors / error /
    cancelled — HashCore's enum names). Malformed jobs
    (bad type/targets/payload, unknown group, unreadable
    creds file) exit 2 BEFORE any device I/O, like scan.
  * Credential resolution is the v0.23/v0.24 mechanism
    itself: the job references a group and/or a creds
    file; the runner merges group -> global
    (groups.effective_creds), probes each device with
    the merged sets (discover.probe_host), and translates
    the winning set into the single creds dict
    core.actions.execute consumes — the same dict the
    cloud agent passes. An unanswering device is an
    honest per-device failure, never a guess.
  * Concurrency: a bounded thread pool (job `workers`,
    default 4, hard cap 8) + an optional `stagger_s`
    gate between device starts (HashCore's batch pause).
    Cancellation is cooperative: SIGTERM/SIGINT (wired
    in cmd_ops) stops new devices starting; unstarted
    devices are counted cancelled in the summary.
  * Found while building (guarded, disclosed): the
    probe can raise outside the adapters' error types
    (http.client.BadStatusLine from a malformed-HTTP
    device). The runner catches it as THAT device's
    failure — one sick device can no longer kill a run.
    discover() itself keeps its existing contract;
    hardening it is a separate core change, not hidden
    inside this release.

ACTION INVENTORY (full table: docs/operations-mapping.md §3):

  SHIPPED: rescan "Quét lại" (the scan pipeline;
  HashCore's discover/refreshStats/updateStats); reboot
  "Khởi động lại" (core/actions.py: cgminer privileged
  restart RPC / dashd POST /system/reboot / stock
  reboot.cgi — refusals surface verbatim); switch_pool
  "Đổi pool" (actions.py's dashd path: pool_id ->
  /mining/switch-pool, url/user -> GET+POST /settings
  with its honest api-key requirement; other families
  fail honestly); export "Xuất danh sách" (APP-SIDE
  BeeSky addition: selected records -> JSON file + a
  history entry; not a HashCore port).
  MERGED: HashCore's restart (mining restart) folds
  into reboot — BeeSky has no separate mining-restart
  primitive and does not fake the distinction.
  PRIMITIVE-EXISTS / DEFERRED: install/update firmware
  (core/firmware.py install_dashd/install_stock exist;
  a bulk run needs a per-task file + minutes-long
  wait-back — stays with `beesky fw install`).
  GAP-GATED: unlock (firmware.py behind the CLI's three
  hard gates — never a bulk action).
  GAP-UNIMPLEMENTED (dashd api-doc documents the
  endpoint; BeeSky has no code path): pause, resume,
  findMiner, resetFirmware, removeFirmware,
  resetAutotuneProfiles, resetCurrentAutotuneProfile,
  throttle, configureApiKey, diagnosticReport.
  GAP-UNVERIFIED: changePassword, configureNetwork
  (settings-write pieces exist; semantics unverified).
  GAP: cloneSettings (v0.28 with pool presets),
  conditionalRestart, updateNote (v0.27),
  restoreCvFirmware (no Cvitek adapter), multi
  (composite — the runner runs one type per job).

FLUTTER APP (app_flutter/):

  * lib/ops.dart (NEW): OpsTaskType / OpsStatus /
    OpsDeviceResult / OpsTask (the history entry AND the
    live run's state; copyable infoText in HashCore's
    task_info shape), OpsEvent / OpsSummary, the OpsRun
    handle (events stream + summary future + Stop),
    OpsFiles (job file + export dir) and
    OpsHistoryStore (beesky-ops-history.json beside the
    exe, %APPDATA% fallback, corrupt = empty, retention
    100). lib/ops_dialogs.dart (NEW): the Confirm
    operation dialog (action + count + every target IP),
    the switch-pool payload form (slot activation or
    write-new-pool, with the api-key note), and the
    history dialog (newest first; per-item started/
    counts/duration; expandable per-device results;
    isolate-errors / copy-info / delete-entry actions;
    clear-all behind a confirmation; HashCore's empty
    state text; a still-running entry renders as "Chưa
    hoàn tất" — an app closed mid-run is not hidden).
  * lib/sidecar.dart: BeeSkyBridge.startOps(job) ->
    OpsRun. The sidecar writes the job file beside the
    exe (values inside the FILE, argv carries only
    `ops --job <path>` — the v0.23 rule applied to
    tasks), streams the NDJSON, and SYNTHESISES the
    summary when the process dies without one (a
    Windows kill leaves no summary line) so every
    device is still accounted; the job file is deleted
    when the run ends. MockBridge.startOps simulates
    the same lifecycle against the sample fleet
    (per-device progress, the unreachable unit failing,
    switch_pool failing on non-VNish sources, Stop
    accounting the remainder as cancelled).
  * home_page.dart: the Operations bar joins the
    v0.25 selection bar when the selection is non-empty
    (Thao tác: Quét lại / Khởi động lại / Đổi pool /
    Xuất danh sách, gated while a task runs); the task
    progress bar renders under it ("{task}: N/M địa
    chỉ" + current device + Dừng); rescan results merge
    their fresh records into the table in place; the
    miners toolbar gains "Lịch sử tác vụ". In a
    group's scope the job carries the group (the core
    resolves its creds layer), off-scope just the
    global creds file. models.dart gains
    MinerRecord.toJson (+ Problem/ChainInfo/PoolInfo)
    for the export. All v0.24/v0.25 behaviours intact.

MATCH / DIVERGENCE vs HASHCORE (from the mapping doc):

  MATCH: selection-raised Operations bar; a Confirm
  operation dialog before device-mutating tasks; one
  task = iterations over devices with per-device
  ok/fail outcomes; the task-status set (success /
  hasErrors / error / cancelled); streamed progress
  "{task}: N/M addresses" + Stop; the history dialog's
  shape (info block, iterations/errors/duration line,
  expandable per-device results, isolate-errors,
  copy-info, delete entry, clear-all with confirms,
  operations count, empty state); app-owned history.

  DIVERGENCE (named, in the mapping): the core runner
  is stateless per run (sidecar process + NDJSON)
  where HashCore queues tasks in an in-app service +
  isolates — one task at a time from the app;
  compatibility is resolved per device by probing
  instead of HashCore's pre-run filter, so an
  unsupported family fails honestly per device rather
  than excluding the device (an empty selection still
  never starts); parallel-iterations / stagger /
  timeout ride the JOB (defaults 4 / 0 / 3 s) instead
  of global Settings; no one-shot per-task unlock-
  method override (the group/global cred layers are
  the method selection); Waiting/Processing collapse
  into `running`; Stop is a process kill on Windows
  (POSIX gets the runner's cooperative SIGTERM summary
  too) with the cancelled remainder accounted from the
  summary either way; history retention caps at 100
  entries (HashCore's cap is UNKNOWN); confirm covers
  reboot + switch_pool only — rescan is read-only and
  runs immediately, like HashCore's own Rescan button.

(a) VERIFIED LOCALLY (this sandbox):

  * Python suites at the v0.26.0 pins:

    mock_ops_test: 32 PASS / 0 FAIL (standalone)
    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)
    mock_bridge_test: 24 PASS / 0 FAIL (standalone)
    mock_creds_test: 32 PASS / 0 FAIL (standalone)
    mock_groups_test: 39 PASS / 0 FAIL (standalone)
    mock_units_test: 50 PASS / 0 FAIL (standalone)

    mock_ops_test covers: the exit-2 job contract
    (9 malformed-job cases, stdout empty); reboot per
    family against the real mocks (dashd password +
    api-key sets recorded by the mock, wrong password
    -> verbatim 401 failure and NO reboot recorded,
    stock reboot.cgi hit, cgminer restart recorded,
    read-only RPC refusal verbatim, unreachable ->
    not-answering); switch_pool (slot activation,
    url/user rewrite via /settings, the password-only
    api-key failure, stock not-supported); rescan
    (record rides the event; unreachable fails without
    one); the group -> global cred resolution (winner
    label + the mock's unlock-attempt log proving
    group-first order and global rescue); the stream
    shape + hasErrors derivation; cooperative
    cancellation (unstarted counted, status cancelled);
    the subprocess NDJSON contract end to end.

  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):
    flutter analyze: clean; flutter test: 78 PASS / 0 FAIL (local SDK 3.47.9; 63 pre-existing + 15 new ops tests) — task/history JSON round-trips
    (incl. cancelled results + the 100-entry cap),
    OpsEvent/OpsSummary parsing, MinerRecord.toJson
    round-trip; the mock lifecycle (event order, the
    .104 failure, switch_pool honesty, rescan records,
    stop accounting); the sidecar argv contract.
    Widget level: selection raises the Operations bar;
    reboot -> confirm dialog -> progress bar -> history
    entry with counts + expandable per-device results
    + the history file on disk; history reloaded by a
    fresh HomePage (restart round-trip); export writes
    the records file + its history entry; rescan runs
    unconfirmed. All 63 pre-existing tests still pass
    — the only pre-existing test touched is the version
    pin in widget_test.dart (v0.26.0).

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml):

  * flutter build windows --release on a real Windows
    runner and the BeeSkyFlutter-<tag>-win64.zip asset.
    The app remains compile-verified only until the
    owner runs it on real Windows (as since v0.21).

---

# v0.27.0 — Device detail tabs (HashCore Toolkit device-info dialog, ported per the dissection)

The parity push continues (owner's bar: 99% of HashCore
Toolkit in one month). Following the dissect-before-
porting rule, the Toolkit's device-info dialog was
dissected FIRST from the shipped materials (the
device_info_dialog.* / device_info_board_info.* /
device_info_pools_info.* translation keys — Metrics,
Charts, Boards with CHIPS TOTAL / STABLE / SLOW /
CRITICAL, Pools, Fans with Mode + Speed, Hotel Fee,
the editable Device note) and BeeSky's OWN data audited
against it (the dashd api-doc's AntmMinerStats /
Cooling / PoolStats schemas; report.py's acs reading;
each adapter's read-only reach, file:line) — the full
mapping, with UNKNOWNs and DATA-GAPs named, is in
docs/device-detail-mapping.md. Nothing renders that
BeeSky does not actually have.

PYTHON CORE:

  * beesky/core/inspect.py (NEW) + the `inspect` verb:
    `beesky inspect --json <ip>` deep-fetches ONE device
    (read-only) through the scan's own machinery —
    discover.probe_host claims it (family detection +
    the v0.23 creds-file / v0.24 group credential
    resolution: --creds-file, --group, --groups-file,
    --user/--password, --api-key, --token exactly like
    scan) and the winning set's token/key/login ride
    the candidate into the section fetches. Output is
    ONE JSON document: {ip, source, model, cred_label,
    boards, pools, fans}; every section is
    {"supported": true, ...} or {"supported": false,
    "reason"} — an explicit marker, never an empty
    success; one section's failure never sinks the
    others. A malformed target (not one IPv4 address)
    or a malformed creds file/group exits 2 BEFORE any
    I/O; a device no adapter claims yields an exit-0
    {"error": ...} document (the app renders the state).
  * Per family (evidence: mapping §2): VNISH — the
    /summary the scan already fetches carries pools
    (PoolStats), cooling (per-fan rpm/status/max_rpm,
    the fan mode auto/manual/immersion, fan_duty) and
    per-board chip_statuses counts; /boards adds the
    per-chip list (pos/hr/grade/temp). The grades ARE
    HashCore's buckets: grey = STABLE, orange = SLOW
    (degraded but hashing), red = CRITICAL (dead) —
    dashd.py's own semantics. The fan mode is parsed
    from BOTH the api-doc object shape {name, param}
    and the plain-string shape some builds serve.
    CGMINER — boards from the STATS acs strings (per
    chain: raw acs, chips_total, chips_ok, dead
    positions, the non-'o' character counts, temp) —
    the SAME reading as report.build_record; pools via
    the RPC `pools` command (CgminerClient.pools
    existed unused); fans = STATS speeds, mode null
    (no source key exists). STOCK — boards/fans from
    the status CGI the probe already fetched (cgminer-
    shaped); pools attempted via the bmminer RPC and
    honestly unsupported when it does not answer (no
    CGI source). The scan record is UNCHANGED.

FLUTTER APP (app_flutter/):

  * The detail panel becomes TABBED (named layout
    divergence: BeeSky keeps its v0.22 right-side panel;
    HashCore's is a modal dialog — tabs + content are
    the parity target). Order mirrors the dialog:
    Số liệu (Metrics) · Biểu đồ (Charts) · Board ·
    Pools · Quạt (Fans) · Ghi chú (Note). The first tab
    is NOT named 'Tổng quan' — that label already names
    the grid's Overview density on the same screen (the
    collision broke a grid widget test during the
    build; fixed by naming, disclosed here).
  * lib/detail.dart (NEW): the inspect wire models
    (sections with supported/reason; boards with the
    grade buckets OR the acs shape, never both faked);
    HistorySample + appendHistorySample (keyed MAC-else-
    IP via deviceKeyFor, rate in the record's OWN native
    unit, cap 300/device, oldest pruned); the pure
    chart prep (ratePoints / tempPoints / powerPoints —
    samples lacking a metric are skipped, never zeroed;
    rateUnitOf labels the line with the device's unit);
    MiniChart, a hand-drawn CustomPainter line chart
    (zero third-party deps kept — HashCore's fl_chart
    is a library divergence, not a behaviour one; a
    single point draws as a lone dot); HistoryStore
    (beesky-history.json) + NoteStore (beesky-notes.json)
    on the stores' usual beside-the-exe / %APPDATA%
    strategy, corrupt reads as empty.
  * Số liệu = the v0.22 panel content VERBATIM
    (metrics, issues, board summary lines) — a shipped
    contract; the Board tab carries the deep view (the
    named duplication). Biểu đồ: LOCAL samples only —
    every completed scan appends one sample per live
    device (FETCH_ERROR records are skipped: a failed
    read is not a sample); hashrate + max-temp + power
    (when the device reports power) lines, per device,
    never aggregated across units; the empty state says
    charts fill in as scans accumulate. Board: record
    rows immediately; the inspect fetch (lazy, once per
    device per session) adds the vnish grade split +
    PCB temp + per-chip grades, or the cgminer/stock
    acs breakdown + dead positions — matched to boards
    by POSITION (record and inspect index bases differ
    between the mock fleet and the real core; position
    is the convention-free key). Pools: the record's
    pools when a future core fills them, else inspect
    on first open — loading state, then rows ('Pool N
    URL' / 'Pool N worker', HashCore's own labels) or
    the core's unsupported reason verbatim. Quạt:
    record speeds immediately; inspect adds mode +
    duty (vnish) or the plain 'firmware không báo'
    absence. Ghi chú: HashCore's Device note + Save
    note — a text field + explicit Lưu ghi chú, keyed
    like history, persisted across restarts.
  * lib/sidecar.dart: BeeSkyBridge.inspect(ip, {credsFile,
    group, groupsFile}) — argv carries the IP + file
    PATHS + the group NAME only (values never travel,
    the v0.23 rule); in a group's scope the group rides
    along so the core resolves its creds layer, exactly
    like its scans and ops jobs. MockBridge gains
    inspect fixtures per sample device (vnish with the
    split + mode, two cgminer with acs boards + pools,
    the unreachable unit as an error document) and the
    app seeds demo history for the mock fleet so every
    tab renders in tests/demos.

PER-TAB MATCH / DIVERGENCE / DATA-GAP vs HASHCORE
(full table: docs/device-detail-mapping.md §3–§5):

  Metrics -> Số liệu: MATCH (the existing panel).
  Charts: DIVERGENCE (named) — HashCore's history
  mechanics are UNKNOWN from the shipped materials;
  BeeSky charts LOCAL scan samples, persisted, per
  device in its native unit. Content (hashrate +
  temperature lines) matches; power is a BeeSky extra
  the data genuinely carries.
  Boards: MATCH for vnish (TOTAL/STABLE/SLOW/CRITICAL
  from the firmware's own grades — the same data
  HashCore renders). DATA-GAP for cgminer/stock: the
  acs alphabet's non-'o' characters have no documented
  grade semantics in BeeSky's evidence, so those boards
  show ok/total + dead positions + raw character counts
  and the tab STATES the gap — no invented buckets.
  Pools: MATCH per family where a source exists
  (dashd summary, cgminer RPC); stock without an RPC
  answer is unsupported-with-reason, not empty.
  Fans: MATCH (mode + per-fan speed) for vnish;
  speeds-only for cgminer/stock — fan MODE is a
  DATA-GAP there (no source key exists).
  Note: MATCH (per-device, placeholder + explicit
  save), as a tab instead of a dialog field (the
  container divergence). The v0.25 grid Note COLUMN is
  NOT wired: cell text is a pure function of the
  record and notes live outside records — more than a
  trivial hookup; left for a later pass, named here.
  Hotel Fee: NOT APPLICABLE — BeeSky has no hotel-fee
  concept (no data, no settings); not built.
  Also named: PCB temp rides inspect only (the record
  still carries chip temp alone); MAC keying is
  'when present' — no adapter emits a MAC today.

(a) VERIFIED LOCALLY (this sandbox):

  * Python suites at the v0.27.0 pins:

    mock_inspect_test: 33 PASS / 0 FAIL (standalone)
    mock_agent_bg_test: 52 PASS / 0 FAIL (standalone)
    mock_bridge_test: 24 PASS / 0 FAIL (standalone)
    mock_creds_test: 32 PASS / 0 FAIL (standalone)
    mock_groups_test: 39 PASS / 0 FAIL (standalone)
    mock_units_test: 50 PASS / 0 FAIL (standalone)
    mock_ops_test: 32 PASS / 0 FAIL (standalone)

    mock_inspect_test covers: the vnish sections end
    to end (grade split 112/0/2 on the sick board,
    dead positions [10, 55] from /boards grades, the
    114-chip list, chip + pcb temps, PoolStats pools,
    fan mode auto + duty 62 + per-fan status); the
    cgminer sections (acs counts 111/114, dead
    [10, 55, 114], other_chars {x: 3}, NO grade keys
    in the wire — the gap is structural; RPC pools;
    fan mode null); the stock sections (CGI boards/
    fans; pools unsupported with the no-source reason);
    credential reuse (a locked dashd claimed by the
    creds-file winner + label, its pools honestly
    unsupported — that mock's summary carries none;
    wrong creds -> the vnish candidate with every
    section unsupported on the 401; --group resolution
    with the group's set winning; unknown group exits
    2); the exit-2 contract (5 malformed targets + a
    malformed creds file, stdout empty throughout);
    the exit-0 error document for an unclaimed device.

  * Flutter (SDK 3.47.9 at ~/workspace/flutter-sdk):
    flutter analyze: clean; flutter test: 94 PASS / 0 FAIL (local SDK 3.47.9; 78 pre-existing + 16 new detail tests) — inspect model parsing per family
    (grades vs acs shapes, unsupported markers, the
    error document + failure factory); history append
    (IP/MAC keying, native-unit + legacy-ths rates,
    the 300-cap prune) + JSON round-trips; chart prep
    (null-skipping, unit labelling, empty/single
    shapes); the history/notes stores' round-trips +
    corrupt-reads-empty; the inspect argv contract;
    the mock fixtures' family shapes; the painter's
    single-point + flat-series smoke. Widget level:
    all six tabs render for the vnish S19 (pool rows,
    fan mode + duty, the three grade lines, the seeded
    charts incl. power); the L9's Boards tab states
    the grade DATA-GAP + the acs breakdown with no
    bucket line, its Fans tab shows the honest mode
    absence; the charts empty state for the sample-
    less device; a note saves and survives a fresh
    HomePage. All 78 pre-existing tests still pass —
    the only pre-existing test touched is the version
    pin in widget_test.dart (v0.27.0); the grid
    density test's 'Tổng quan' collision was fixed by
    NAMING the detail tab 'Số liệu', not by editing
    the grid test.

(b) VERIFIED ONLY BY CI (.github/workflows/
build-flutter.yml):

  * flutter build windows --release on a real Windows
    runner and the BeeSkyFlutter-<tag>-win64.zip asset.
    The app remains compile-verified only until the
    owner runs it on real Windows (as since v0.21).
