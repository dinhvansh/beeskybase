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
{"ts": 1794219346.5572197, "time": "2026-11-09 10:15:46", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "HASHRATE_DROP", "severity": "major", "detail": "hashrate dropped 40.0% vs baseline (110.00 -> 66.00 TH/s)", "data": {"baseline_ths": 110.0, "current_ths": 66.0, "drop_pct": 40.0}}
{"ts": 1794219346.9761698, "time": "2026-11-09 10:15:46", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "OFFLINE", "severity": "critical", "detail": "miner went offline / unreachable", "data": {"last_seen": 1794219346.8004332}}
{"ts": 1794219347.5016665, "time": "2026-11-09 10:15:47", "ip": "127.0.0.1", "model": "Antminer S19 Pro", "source": "cgminer", "type": "BACK_ONLINE", "severity": "info", "detail": "miner is back online", "data": {}}

WATCH TEST PASSED
```
