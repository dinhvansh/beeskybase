# Mock test results

Fake miner: `tests/mock_miner.py` (Antminer S19 Pro sample — board 2 has
3 dead chips at positions 10/55/114, board 3 runs at 88 °C).

## Scanner output

```
IP        | Model            | TH/s   | Chips   | MaxTemp | Fans                | Status
----------+------------------+--------+---------+---------+---------------------+-------
127.0.0.1 | Antminer S19 Pro | 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK 

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
