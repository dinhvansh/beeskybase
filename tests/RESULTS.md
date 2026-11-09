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
{"ts": 1794228167.9737449, "time": "2026-11-09 12:42:47", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
{"ts": 1794228168.4293294, "time": "2026-11-09 12:42:48", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "OFFLINE", "severity": "critical", "detail": "miner went offline / unreachable", "data": {"last_seen": 1794228168.2307932}}
{"ts": 1794228168.9808505, "time": "2026-11-09 12:42:48", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "BACK_ONLINE", "severity": "info", "detail": "miner is back online", "data": {}}

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
{"ts": 1794228174.054749, "time": "2026-11-09 12:42:54", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}

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
{"ts": 1794228181.3739717, "time": "2026-11-09 12:43:01", "site": "Xưởng 1", "agent_id": 1, "ip": "127.0.0.1", "model": "Antminer S19 Pro", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
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
{"id": 1, "agent_id": 2, "site": "Xưởng 2", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "dashd accepted reboot (system reboots in 3s)", "created_at": "2026-11-09 12:43:02", "created_ts": 1794228182.9425256, "claimed_at": "2026-11-09 12:43:03", "finished_at": "2026-11-09 12:43:03"}
PASS: dashd mock recorded exactly one POST /system/reboot
PASS: dashd switch_pool {pool_id: 1} finishes done
PASS: dashd mock activated pool slot 1
PASS: dashd switch_pool {url,user} finishes done via /settings
PASS: dashd mock pool slot 0 now carries the new url/user
PASS: site 1 agent reports its cgminer miner
PASS: cgminer reboot finishes done

Captured cgminer reboot command:
{"id": 4, "agent_id": 1, "site": "Xưởng 1", "ip": "127.0.0.1", "type": "reboot", "payload": {}, "status": "done", "result": "cgminer accepted the privileged 'restart' command", "created_at": "2026-11-09 12:43:05", "created_ts": 1794228185.778913, "claimed_at": "2026-11-09 12:43:06", "finished_at": "2026-11-09 12:43:06"}
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
