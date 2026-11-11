# BeeSky — ASIC miner LAN scanner & repair diagnostics

BeeSky is a small, dependency-free tool for ASIC repair shops. It scans a local
network for miners, reads their health over whichever API the firmware
exposes — the classic **cgminer RPC API (TCP 4028)**, the **VNish/HashCore
dashd HTTP API**, or **Bitmain stock web CGI** (digest auth) — and turns the
raw numbers into something a repair tech can act on: a status table and, for
every sick miner, a plain-text **repair ticket** (Vietnamese) with per-board
details and suggested checks.

Fleet tools (e.g. HashCore Toolkit) stop at generic dashboards and exports.
BeeSky's focus is the repair bench: *which board, how many chips down, how hot,
and what to check first.*

Pure **Python 3 standard library** — no pip installs, runs anywhere Python 3
does (Windows / macOS / Linux), fully offline, no analytics, no phone-home.

## Install on Windows (for users)

No Python, no admin rights, nothing to configure:

1. **Download `BeeSkySetup-<version>.exe`** — either from the repo's
   [Releases](../../releases) page, or from the latest
   **Actions → "Build Windows installer"** run (the `BeeSky-Windows`
   artifact contains the installer plus a bare `beesky.exe`).
2. **Run the installer.** It installs per-user into
   `%LocalAppData%\Programs\BeeSky`, adds `beesky` to your PATH, and
   puts a **BeeSky** shortcut in the Start Menu. (Windows SmartScreen
   may warn about an unsigned installer — the builds are produced by
   GitHub Actions from this repo's source; choose "More info → Run
   anyway".)
3. **Open "BeeSky" from the Start Menu** — a console opens, ready to go:

```bat
beesky scan 192.168.1.0/24
beesky scan 192.168.1.50 --tickets tickets\
beesky watch 192.168.1.0/24 --notify notify.json
```

An example notification config (`notify.example.json`) and this README
are copied into the install folder. Uninstall from Windows Settings →
Apps, like any other program.

## Usage (developers / from source)

```bash
# Scan one miner
python -m beesky scan 192.168.1.50

# Scan a subnet or an IP range
python -m beesky scan 192.168.1.0/24
python -m beesky scan 192.168.1.10-192.168.1.60

# Save machine-readable results and repair tickets
python -m beesky scan 192.168.1.0/24 --json out.json --tickets tickets/

# Watch a farm: repeated scans -> events -> notifications (webhook /
# Telegram / logfile). Ctrl-C to stop. --once runs a single pass; pair
# it with --state so successive invocations still detect changes.
python -m beesky watch 192.168.1.0/24 --interval 30 --notify notify.json
python -m beesky watch 192.168.1.50 --once --state state.json --notify notify.json

# Non-default credentials (stock web UI / dashd), non-standard ports
python -m beesky scan 192.168.1.0/24 --user root --password <pw> \
    --api-key <dashd-key> --http-port 80 --cgminer-port 4028
```

Example output (note the **Source** column — which adapter read the miner):

```
IP            | Model            | Source  | TH/s   | Chips   | MaxTemp | Fans                | Status
--------------+------------------+---------+--------+---------+---------+---------------------+-------
192.168.1.50  | Antminer S19 Pro | cgminer | 110.02 | 342/342 | 71      | 4320/4380/4440/4500 | OK
192.168.1.51  | Antminer S19 Pro | vnish   | 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK
192.168.1.52  | Antminer S19     | stock   | 95.10  | 342/342 | 70      | 4200/4260/4320/4380 | OK

Found 3 miner(s), 1 need(s) checking.
```

### What gets flagged (`Status = CHECK`)

- a chain (hashboard) missing chips — dead-chip positions are listed
- a chain reporting **0 chips** (board down / not detected)
- any chain temperature **≥ 85 °C**
- hashrate **0** while the miner has been running > 300 s

For each flagged miner, `--tickets <dir>` writes one `ticket-<ip>.txt` with the
problems, per-board chip/temp detail, and repair suggestions in Vietnamese.

### Watch mode & notifications

`watch` re-scans on an interval and diffs every miner against its own
history (`beesky/core/events.py`), emitting events: **OFFLINE**,
**BACK_ONLINE**, **HASHRATE_DROP** (vs the miner's rolling baseline),
**OVER_TEMP** (rise vs baseline, or ≥ 85 °C absolute), **CHIPS_LOST** and
**CHAIN_DOWN**. The design copies EMCD Monitoring's two layers: detection
is sensitive (> 5 % drop / > 5 °C rise already detects) while severity
follows their 3-step scales — 15/30/50 % and 10/20/30 °C →
warning/major/critical. A per-miner latch + cooldown (default 300 s)
stops repeat alerts while a condition persists.

Events are routed per type to channels (`beesky/core/notify.py`) from one
JSON config — see [`docs/notify.example.json`](docs/notify.example.json):

- **webhook** — the event POSTed as JSON to any URL. This is the channel
  EMCD lacks: point an OVER_TEMP webhook at a local controller (Home
  Assistant, relay box, smart PDU) and the farm can switch on extra
  exhaust fans or water-mist pumps by itself.
- **telegram** — Bot API `sendMessage` (token/chat from config or the
  `BEESKY_TELEGRAM_BOT_TOKEN` / `BEESKY_TELEGRAM_CHAT_ID` env vars).
- **logfile** — one JSON event per line, appended.

## How it works

Architecture mirrors the pattern used by mature fleet tools, kept minimal:

- **CLI core first** (`beesky/`): all logic lives in a scriptable core package;
  a GUI can be bolted on later without touching it.
- **Per-vendor adapters** (`beesky/core/`): the generic cgminer RPC client
  (`summary` / `stats` / `pools`); the VNish/HashCore **dashd** adapter,
  implemented against the firmware's own OpenAPI doc (`/api/v1/summary` +
  `/api/v1/boards` — per-chip grades included, so dead-chip *positions*
  survive); and the Bitmain **stock** adapter (web CGI + hand-rolled HTTP
  digest auth, stdlib only). WhatsMiner slots in beside them next.
- **Discovery**: for each host, walk the adapter chain in order — cgminer RPC
  **:4028** → dashd HTTP **:80** → stock CGI **:80** — and keep the first
  adapter that answers like a miner. Probing is threaded with bounded workers
  and short timeouts. HTTP adapters always connect directly (system proxy
  env vars are ignored — miners are LAN devices).
- **Normalised records** (`beesky/core/report.py`): every miner becomes one
  status record (JSON-friendly) plus a problems list; the CLI table, the JSON
  export, and the repair tickets are all rendered from that record.
- **Events + notifications** (`beesky/core/events.py`, `notify.py`): watch
  mode diffs successive records per miner (rolling-median baselines,
  latch + cooldown anti-flap, JSON-persistable state) and routes the
  resulting events to webhook / Telegram / logfile channels by per-type
  rules and minimum severity — EMCD's notification matrix, plus the
  webhook channel they don't have.

## Mock tests

Fake miners are included so the whole pipeline can be verified with no
hardware — a sick cgminer S19 Pro, a sick VNish S19 Pro, and a healthy
stock-firmware S19 behind digest auth:

```bash
bash tests/run_mock_test.sh      # v0.1: cgminer only -> tests/RESULTS.md
bash tests/run_mock_test_v2.sh   # v0.2: all three adapters, appends to RESULTS.md
bash tests/run_mock_test_v3.sh   # v0.3: full suite + watch story (healthy ->
                                 # hashrate -40% -> killed -> back), webhook
                                 # and Telegram captured by a local receiver
```

## Roadmap

- ~~v0.2 — VNish/HashCore dashd HTTP adapter (optional API-key/bearer auth)
  + Bitmain stock web adapter (digest auth); scan table gains a Source
  column.~~ **Done.**
- ~~v0.3 — watch mode: event engine (offline / hashrate drop / over-temp /
  chips lost / chain down) + notifications (webhook, Telegram, logfile)
  with EMCD-style severity scales.~~ **Done.**
- v0.4 — WhatsMiner (MicroBT API v2) adapter; scan history + before/after
  compare for repair verification; `devs` command for per-chain detail.
- Later — pool switch / reboot actions, signed self-update manifests,
  single-hashboard fixture tester integration.

## Layout

```
beesky/
  cli.py            # `python -m beesky scan ...` / `python -m beesky watch ...`
  core/
    cgminer.py      # cgminer RPC client (TCP 4028)
    dashd.py        # VNish/HashCore dashd HTTP API adapter (/api/v1)
    bitmain.py      # Bitmain stock web CGI adapter (digest auth)
    discover.py     # target parsing + threaded adapter-chain probing
    report.py       # status records, problem rules, repair tickets
    events.py       # watch-mode event engine (baselines, anti-flap, state)
    notify.py       # webhook / Telegram / logfile notification routing
docs/
  brand.md          # BeeSky brand palette + logo source
  notify.example.json  # watch/notify config example (EMCD-style matrix)
tests/
  mock_miner.py     # fake cgminer API server (S19 Pro sample data)
  mock_dashd.py     # fake VNish dashd server (api-doc-shaped S19 Pro)
  mock_bitmain.py   # fake stock-firmware server (digest auth, healthy S19)
  mock_watch_miner.py  # control-file-driven fake miner for the watch test
  mock_watch_test.py   # watch story driver: drop -> offline -> back online
  run_mock_test.sh  # v0.1 end-to-end mock test -> tests/RESULTS.md
  run_mock_test_v2.sh  # v0.2 three-adapter mock test (appends to RESULTS.md)
  run_mock_test_v3.sh  # v0.3 full suite + watch test (appends to RESULTS.md)
packaging/
  entry.py          # PyInstaller entry shim (hands argv to beesky.cli)
  beesky.spec       # PyInstaller single-file console exe build
  installer.iss     # Inno Setup per-user installer (no admin, PATH +
                    # Start Menu console shortcut, uninstaller)
  beesky.ico        # brand icon (from the VNish patch-test assets)
.github/workflows/
  build-windows.yml # windows-latest runner: PyInstaller + Inno Setup ->
                    # BeeSky-Windows artifact; Releases on v* tags
```

### Nhãn, nhóm làm mát và model máy

Xưởng 3D dùng model S21 Hydro/S19 Pro từ hai archive người dùng cung cấp; tải mỗi loại một lần và dùng chung hình học. Model chưa nhận diện dùng khối đơn giản. Trong chi tiết máy có thể chọn model hiển thị mà không sửa model máy báo về.

Mở **Nhãn & nhóm** để tạo nhóm theo bộ tản/đường nước, chọn nhiều máy (lọc riêng máy nước/máy gió), hoặc gắn nhãn từng máy. Bộ lọc và tìm kiếm hỗ trợ nhãn, tên nhóm, bộ tản và đường nước. Nhóm liên kết bằng ID máy, đi qua nhiều kệ/tầng trong một xưởng và giữ nguyên khi đổi vị trí. Xóa nhóm không xóa máy.

Dữ liệu nhóm, nhãn và bố trí hiện chỉ nằm trong phiên duyệt; tải lại trang sẽ mất thay đổi. Liên kết làm mát nhập thủ công, chưa kết nối backend hay điều khiển đường nước/bộ tản.

### Xưởng 3D và xoay kệ

Thanh chọn kệ luôn có **Xoay trái / Xoay phải** theo bước 90°, **Vị trí & tầng**, và hoàn tác. Bật **Bố trí kệ** để kéo trên sàn; R xoay kệ đang chọn khi canvas có focus. Kiểm tra va chạm và giới hạn sàn vẫn áp dụng.

**Toàn xưởng** hiển thị chung hai loại model máy trong nhà xưởng dạng cắt mái, với thông gió, bộ tản minh họa, ống cấp/hồi và lối đi. **Cận kệ** quay lại góc nhìn tập trung vào thiết bị. Thiết bị phụ trợ chỉ minh họa, không tự xác lập kết nối làm mát thực tế.

### Hiệu ứng hoạt động trong xưởng

Nút **Hiệu ứng: Bật/Tắt** điều khiển coin Bitcoin / `+ HASH` nổi lên, dòng hạt nước ở máy hydro và LED hoạt động. Máy offline không phát coin. Hiệu ứng theo máy khi đổi bố trí và theo bộ lọc đang dùng; coin/hash chỉ là trang trí, không phải số dư hay thu nhập thật.

Cảnh giới hạn 30 khung/giây, tối đa 27 sprite coin/hash, dừng vòng vẽ khi tắt hiệu ứng, ra ngoài vùng xem hoặc ẩn tab. Tôn trọng cài đặt giảm chuyển động của hệ thống. Dọn vòng hoạt ảnh và listener khi chuyển tầng, đổi cảnh hoặc đóng 3D.


### Sửa model và nhãn kệ

Model hydro loại bỏ phông nền studio đi kèm file gốc và quay mặt kết nối ra phía trước. Hai model giữ nhiều chi tiết hơn, sửa hướng mặt và triangulate khi chuyển đổi. Bỏ cánh quạt trang trí chồng lên quạt gốc. Nhãn kệ dùng lớp chữ trên màn hình, có tên, sức chứa và khu vực; giữ cỡ chữ khi zoom, theo vị trí kệ và giới hạn trong vùng xem.


### Xem nhiều tầng và công cụ gọn

Chọn **Tầng → Tất cả tầng · phối cảnh** để xem các tầng cùng lúc theo dạng tách tầng theo chiều cao, sàn trong suốt và đường viền riêng. Chọn một tầng để chỉnh vị trí; mở **Bố trí** tự trở về tầng đang chọn để thao tác an toàn. Nhãn bên trái là danh sách kệ luôn hiện trong cảnh, có thể cuộn; bấm tên để đưa camera tới kệ đó.

Mặc định chỉ hiện thanh chọn tầng và các nút Bố trí, Lọc & nhóm, Tùy chọn, Toàn màn hình. Góc nhìn gom vào một danh sách; công cụ quản lý tầng, xoay kệ và di chuyển máy chỉ xuất hiện khi mở Bố trí. Bộ lọc/nhóm chỉ xuất hiện khi cần.


Nhãn kệ hiện là bảng gắn phẳng lên tường sau, gồm tên kệ, sức chứa, tầng và khu vực; không còn danh sách nhãn nổi bên trái. Mỗi tầng có bảng riêng. Bấm bảng để tìm kệ trong chế độ khám phá.
