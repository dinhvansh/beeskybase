# Agent app — dissection & port mapping (v0.31.0, Flutter stage 2)

Stage 2 of the Flutter programme: the standalone **agent config app**
gets a Flutter face (`app_agent_flutter/`, exe `beesky_agent_app.exe`)
and the installers become unified. The port source is **our own Tk
agent app** (`beesky/agent_gui.py` + `beesky/agent_app.py` +
`beesky/agent_config.py`) — its behaviour is the spec, dissected
below from the source. The Python core is **not** restructured: the
agent machinery (config format, DPAPI storage, `agent-status.json`,
Scheduled-Task management) stays exactly as it is, and the Flutter
app drives the shipped `beesky-agent.exe` verbs for everything the
Tk window did in-process.

## 1. The Tk app's behaviour (the spec)

### 1.1 Window anatomy (`agent_gui.AgentConfigApp`)

- Title: `BeeSky Agent <version> — Cấu hình agent trại`. Header:
  logo (~40 px), "BeeSky Agent" / "Cấu hình agent tại trại", a
  version pill `v<version>` on the right.
- **Card "Kết nối cloud"**: `Cloud URL:` (with a live warning hint
  under it), `Agent key:` masked (`show="*"`) with a `Hiện key`
  checkbox toggle, `Tên trại:` (hint `vd Xưởng 1`), then the fixed
  note paragraph `_KEY_NOTE` (key is shown once by the cloud, lives
  only in this config file, DPAPI-protected on Windows; a lost key
  means revoke + re-issue on the cloud).
- **Card "Quét tại trại"**: `Dải IP quét:` (hint: ranges separated
  by commas), `Chu kỳ quét (giây):` (default `30`).
- **Card "Trạng thái chạy ngầm"**: a status pill + a text line +
  a `Xem log` button (see §1.4).
- **Actions row**: `Lưu cấu hình` (accent), `Chạy thử` (ghost),
  `Bật tự khởi động` / `Tắt tự khởi động` (ghost, label follows the
  task state), a test-result pill on the right (`Chưa chạy thử` →
  `Đang chạy thử…` → `Chạy thử: OK` / `Chạy thử: FAIL`), an
  auto-start hint line under the row, and a footer status line
  (initially `File cấu hình: <path>`).

### 1.2 Config fields & the file (`agent_config.AgentConfig`)

The form edits exactly five fields — `cloud_url`, `key`, `site`,
`target`, `interval`. Everything else in the file (`notify_config`,
`auto_update`, `timeout`, `workers`, `user`, `password`, `api_key`,
`token`, `http_port`, `cgminer_port`, `update_url`) is preserved
untouched: `current_config()` re-reads the on-disk config as the
base and overrides only the five form fields.

- Path (`default_config_path`): `$BEESKY_AGENT_CONFIG` →
  `%APPDATA%\BeeSky\agent-config.json` (Windows) →
  `~/.beesky/agent-config.json`.
- Load is tolerant (`from_dict`): unknown keys ignored, missing
  fields defaulted, scalars coerced (`interval`/`timeout` float,
  `workers`/ports int, `auto_update` bool, non-dict `notify_config`
  → null, null strings → `""`).
- **Key storage (core-owned, v0.16)**: the in-memory key is plain;
  `save()` on Windows writes it DPAPI-protected
  (`key_protected`, machine scope — the background task runs as
  SYSTEM) and empties `key`; without DPAPI (or if the protect call
  fails) it writes the plain `key` and clears `key_protected`. A
  `key_protected` blob that cannot be decrypted on this machine
  loads as an empty key (operator re-issues). When memory holds no
  plain key, `save()` keeps whatever blob the file already carries.
- On-disk format: indented JSON (2 spaces), dataclass field order,
  trailing newline; parent dir created on first save; permissions
  tightened best-effort (0600 POSIX / icacls owner+SYSTEM on
  Windows).
- Required fields (`missing_fields`, in fix order): `target`,
  `cloud_url`, `key`, `site`.

### 1.3 Load / save / validation behaviour

- **First run** (file does not exist): the target field is
  pre-filled with `default_scan_target()` (this machine's own /24;
  v0.19.6), everything else blank, interval `30`.
- **Load**: fields filled from the config; the interval renders as
  `30` when integral, else the raw float (`45.5`). A file that
  fails to parse leaves the fields blank and puts
  `Không đọc được cấu hình: <error>` on the status line. Success:
  `Đã nạp cấu hình từ <path> — sửa rồi Lưu, hoặc Chạy thử ngay.`
- **Save** (`current_config()` + `save_config()`):
  - interval must parse as a float → else
    `chu kỳ quét '<raw>' không phải số giây hợp lệ`; must be > 0 →
    else `chu kỳ quét phải lớn hơn 0 giây`. Either failure:
    `Chưa lưu được: <error>`, nothing written.
  - missing required fields → `Chưa lưu được — còn thiếu: <list>`.
  - success → `Đã lưu cấu hình vào <path> (HH:MM:SS). Agent chạy
    bằng: beesky-agent run`.

### 1.4 Background status card

Reads `agent-status.json` **next to the config file**
(`agent_app.read_status` — plain JSON, written atomically by the
running agent after every cycle: `{ts, time, ok, miners, error,
cloud_url, site}`):

- no file / unparseable → pill dim `Chưa có dữ liệu`, text
  `Agent chưa chạy vòng nào — trạng thái sẽ hiện ở đây sau vòng
  quét đầu tiên.`
- `ok` true → pill ok `Đang chạy tốt`, text
  `Vòng gần nhất OK lúc <time> — <miners> máy · trại <site> · cloud <cloud_url>`
- `ok` false → pill bad `Lỗi gần nhất`, text
  `Lỗi lúc <time>: <error | không rõ nguyên nhân>`
- The window polls the file's mtime every 100 ms and repaints only
  on change. `Xem log` opens `agent.log` (same folder) with the OS
  handler; missing log → status line
  `Chưa có file log tại <path> — agent chưa chạy.`

### 1.5 Test + auto-start (in-process in Tk)

- **Chạy thử**: builds the form config (interval validated first —
  a bad interval sets `Chạy thử thất bại: <error>` + FAIL pill),
  then `test_ingest(cfg)` on a worker thread: one real scan + one
  snapshot delivery. Verdicts: missing fields →
  `chưa đủ cấu hình — còn thiếu: <list>`; scan exception →
  `quét thất bại: <exc>`; delivered →
  `đã đẩy snapshot <n> máy lên <cloud_url> (site '<site>')`;
  refused → `cloud không nhận snapshot — kiểm tra Cloud URL, agent
  key và đường mạng từ trại`. The window's status line shows
  `OK [HH:MM:SS]: <verdict>` / `FAIL [HH:MM:SS]: <verdict>` and the
  pill follows. The button disables while testing.
- **Auto-start**: `task_installed()` = `schtasks /Query /TN
  "BeeSky Agent"` exit 0 (Windows only). Toggle calls
  `install_task(config_path)` (registers the v2 XML task: SYSTEM,
  boot+logon triggers, windowless `beesky-agentw.exe run --config
  <path>`) or `remove_task()`; the returned message goes to the
  status line and the button label refreshes. Off Windows the
  button is disabled with the hint
  `(Scheduled Task chỉ có trên Windows)`.

### 1.6 Cloud-URL hint

`insecure_cloud_warning`: an `http://` URL whose host is not
localhost / 127.0.0.1 / ::1 shows
`⚠ Cloud URL dùng http:// không mã hoá — agent key sẽ đi qua mạng
dạng rõ; nên dùng https:// cho cloud.` — recomputed on every edit.

## 2. The Pulse contrast (install-time pairing)

From `research/hashcore/pulse-win/FINDINGS.md` (VERIFIED there):
Pulse's Inno wizard has custom pages — *"Please enter the Agent
ID:"* / *"Please enter the Secret key:"* (both required) — and the
wizard itself then writes the agent config (YAML) into
`C:\ProgramData\pulse-agent\`. Pairing therefore happens **during
install**, not in a config app afterwards.

**What BeeSky's Inno scripts can do** (evidence: the two existing
`.iss` files + Inno Setup 6 capabilities): custom wizard pages with
labelled edits (incl. a password edit), a post-install step, and
arbitrary file writes from Pascal `[Code]`. So the same option is
implementable: an **optional** pairing page (Cloud URL + Agent key
+ Tên trại) that, when filled in, writes `agent-config.json` to
`%APPDATA%\BeeSky\` (the core's own default location) post-install.

**What it cannot/should not do** (named limits):
- The write is the core's *legacy plain-text* form — Inno has no
  DPAPI; the core migrates the key to a DPAPI blob on its next
  save, exactly as it does for a pre-v0.16 config. The page says so
  in plain text.
- It writes only when no config file exists yet (an upgrade must
  never clobber a configured farm PC).
- It cannot honour a `$BEESKY_AGENT_CONFIG` override (the
  installer cannot know it); such setups
...[truncated 9113 chars]