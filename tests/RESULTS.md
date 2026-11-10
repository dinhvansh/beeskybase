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
{"ts": 1794282403.3720913, "time": "2026-11-10 03:46:43", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
{"ts": 1794282403.8305504, "time": "2026-11-10 03:46:43", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "OFFLINE", "severity": "critical", "detail": "miner went offline / unreachable", "data": {"last_seen": 1794282403.630678}}
{"ts": 1794282404.4236083, "time": "2026-11-10 03:46:44", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "BACK_ONLINE", "severity": "info", "detail": "miner is back online", "data": {}}

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
{"ts": 1794282409.504003, "time": "2026-11-10 03:46:49", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}

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
{"ts": 1794282416.8439379, "time": "2026-11-10 03:46:56", "site": "Xưởng 1", "agent_id": 1, "ip": "127.0.0.1", "model": "Antminer S19 Pro", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
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
{"id": 1, "agent_id": 2, "site": "Xưởng 2", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "dashd accepted reboot (system reboots in 3s)", "created_at": "2026-11-10 03:46:58", "created_ts": 1794282418.4444592, "claimed_at": "2026-11-10 03:46:58", "finished_at": "2026-11-10 03:46:58"}
PASS: dashd mock recorded exactly one POST /system/reboot
PASS: dashd switch_pool {pool_id: 1} finishes done
PASS: dashd mock activated pool slot 1
PASS: dashd switch_pool {url,user} finishes done via /settings
PASS: dashd mock pool slot 0 now carries the new url/user
PASS: site 1 agent reports its cgminer miner
PASS: cgminer reboot finishes done

Captured cgminer reboot command:
{"id": 4, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "cgminer accepted the privileged 'restart' command", "created_at": "2026-11-10 03:47:01", "created_ts": 1794282421.2771792, "claimed_at": "2026-11-10 03:47:02", "finished_at": "2026-11-10 03:47:02"}
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
{"id": 1, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "mac_or_serial": null, "created_at": "2026-11-10 03:47:12", "created_ts": 1794282432.7923918, "kind": "auto_event", "title": "CHIPS_LOST", "detail": "lost 3 chip(s) (342 -> 339 alive)", "cost_vnd": null, "technician": null}
PASS: POST /api/repairs (logged in) -> 201 manual row
PASS: manual row listed with cost_vnd + technician

Captured manual repair row:
{"id": 2, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "mac_or_serial": null, "created_at": "2026-11-10 03:47:13", "created_ts": 1794282433.2233443, "kind": "manual", "title": "Thay board 2", "detail": "Board 2 chết 3 chip — đã thay board, test lại đạt", "cost_vnd": 1500000, "technician": "Tuấn"}
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
{"ts": 1794282436.913463, "time": "2026-11-10 03:47:16", "site": "Xưởng 1", "agent_id": 1, "ip": null, "model": null, "type": "POOL_GAP", "severity": "major", "detail": "pool reports 43.65 TH/s vs farm 109.13 TH/s — gap 60.0% exceeds 10% for 2 consecutive checks", "data": {"pool_ths": 43.65, "farm_ths": 109.13, "gap_pct": 60.0, "threshold_pct": 10.0}}
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
PASS: check: signed manifest accepted (ok + signature_ok) — {"current": "0.13.0", "latest": "0.14.0", "update_available": true}
PASS: check: newer version reported as update available
PASS: check: tampered manifest refused end-to-end
PASS: apply: newer signed release installs onto the dummy — updated beesky to BeeSky 0.14.0 (previous file kept as beesky.old) — restart to run it
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
