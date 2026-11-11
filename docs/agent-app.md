# BeeSky Agent — app agent riêng tại trại (v0.14, chạy ngầm + bảo mật v0.16)

> **v0.31 — bản Flutter + bộ cài hợp nhất:** cửa sổ cấu hình có thêm
> bản Flutter (`beesky_agent_app.exe`, shortcut *BeeSky Agent
> (Flutter)*) — cùng file cấu hình, cùng trạng thái chạy ngầm, nút
> *Chạy thử* / *Bật tự khởi động* gọi đúng các lệnh của
> `beesky-agent.exe` bên dưới; cửa sổ gốc trong tài liệu này vẫn
> đi kèm làm bản dự phòng. Bộ cài chính `BeeSkySetup` nay gồm cả
> agent (mục cài đặt *BeeSky Agent*, thư mục con `agent\`), và cả
> hai bộ cài đều có **trang ghép nối tuỳ chọn lúc cài đặt** (Cloud
> URL + Agent key + Tên trại — để trống thì cấu hình sau trong app
> như bình thường; trang chỉ hiện khi máy chưa có file cấu hình).
> Một khác biệt đã biết của bản Flutter: key đang lưu dạng DPAPI
> thì ô key hiện trống kèm ghi chú "để trống để giữ nguyên, nhập
> mới để thay" (bản gốc giải mã và hiện key). Chi tiết đối chiếu:
> `docs/agent-app-mapping.md`.

Từ v0.14, agent tại trại là **một app riêng** (`beesky-agent.exe`,
bộ cài `BeeSkyAgentSetup-<version>.exe`) thay vì chỉ là một lệnh con
của bộ công cụ chính. Máy PC ở trại chỉ cần cài đúng app này: mở lên,
điền cấu hình một lần trong cửa sổ, bấm chạy thử, bật tự khởi động —
xong, agent tự quét máy đào trong mạng trại và đẩy số liệu lên
BeeSky Cloud như trước (kiến trúc agent → cloud giữ nguyên, xem
`docs/cloud.md`).

Từ **v0.16** agent chạy **ngầm thật sự**: bộ cài kèm thêm
`beesky-agentw.exe` — bản *không cửa sổ console* của cùng một agent —
và đó là file tác vụ tự khởi động trỏ vào. Không còn cảnh cửa sổ đen
bị ai đó tắt nhầm là agent chết theo; tác vụ chạy bằng SYSTEM, ẩn,
và tự khởi động lại agent khi nó lỗi. Key trong file cấu hình được
Windows mã hoá (DPAPI) thay vì nằm dạng rõ — chi tiết ở mục *Bảo
mật* bên dưới.

Lệnh `beesky agent ...` trong bản chính vẫn chạy bình thường cho ai
quen dòng lệnh; hai đường dùng chung một lõi, cùng định dạng ingest,
cùng kênh cập nhật đã ký.

## Cài đặt tại trại — 4 bước

1. **Cài** `BeeSkyAgentSetup-<version>.exe` (cài per-user, không cần
   quyền admin). Mở **BeeSky Agent** từ Start Menu / desktop — cửa
   sổ cấu hình hiện ra.
2. **Điền cấu hình** (key lấy từ trang **Cài đặt** của cloud, mục
   *Agent & trại* → *Tạo agent* — cloud hiện sẵn cả dòng lệnh mẫu):
   - *Dải IP quét*: dải chứa máy đào, vd `192.168.1.10-192.168.1.60`
     hoặc `192.168.1.0/24`.
   - *Cloud URL*: địa chỉ cloud, vd `https://cloud.example.com`.
   - *Agent key*: key cloud vừa cấp (chỉ hiện **một lần** lúc tạo).
   - *Tên trại*: phải trùng tên đã đăng ký trên cloud, vd `Xưởng 1`.
   - *Chu kỳ quét*: mặc định 30 giây.
   Bấm **Lưu cấu hình**.
3. **Chạy thử**: bấm *Chạy thử* — app quét thật một vòng và đẩy
   snapshot lên cloud. Dòng trạng thái hiện `OK` kèm giờ và số máy
   đã đẩy, hoặc `FAIL` kèm lý do (sai URL, sai key, mất mạng…).
   Sang cloud kiểm tra: trại phải xuất hiện trong *Tổng quan*.
4. **Bật tự khởi động**: bấm *Bật tự khởi động* — app đăng ký
   Windows Scheduled Task tên **BeeSky Agent** (đăng ký bằng XML,
   không phải lệnh schtasks rút gọn):
   - chạy bằng **SYSTEM**, mức quyền cao nhất;
   - kích hoạt khi **khởi động máy** (trễ 30 giây) **và** khi có
     người **đăng nhập**;
   - trỏ vào **`beesky-agentw.exe run`** — bản chạy ngầm, **không
     cửa sổ console**, tác vụ ở chế độ ẩn;
   - **tự khởi động lại khi lỗi**: mỗi 1 phút, tối đa 5 lần; không
     bị giới hạn thời gian chạy, không dừng vì pin/rút sạc.
   - Đăng ký tác vụ SYSTEM cần quyền admin: nếu Windows báo lỗi, mở
     app bằng *Run as administrator* rồi bấm lại.
   - Muốn tắt: bấm lại nút đó (đổi thành *Tắt tự khởi động*), hoặc
     chạy `beesky-agent remove-task`.
   - Gỡ lỗi tại trại mà cần thấy log trực tiếp: đăng ký lại tác vụ
     trỏ vào bản console bằng `beesky-agent install-task --console`.

Từ đây agent chạy nền vĩnh viễn — không cửa sổ nào để tắt nhầm.

## Agent chạy ngầm: log và trạng thái ở đâu

Hai file nằm **cạnh file cấu hình** (`%APPDATA%\BeeSky\` trên
Windows):

| File | Nội dung |
|---|---|
| `agent.log` | Toàn bộ output của agent (quét, đẩy số liệu, lỗi…). Tự xoay khi vượt ~1 MB (bản cũ thành `agent.log.old`). Key của agent **không bao giờ** xuất hiện trong log — mọi dòng đều được lọc key trước khi ghi. |
| `agent-status.json` | Trạng thái vòng quét gần nhất, ghi lại sau **mỗi** vòng: `{ts, time, ok, miners, error, cloud_url, site}`. Ghi kiểu nguyên tử (file tạm + thay thế) nên đọc lúc nào cũng trọn vẹn. |

Cửa sổ cấu hình có thẻ **Trạng thái chạy ngầm** đọc
`agent-status.json`: báo *Đang chạy tốt* (giờ vòng OK gần nhất + số
máy) hoặc *Lỗi gần nhất* kèm nội dung lỗi, và nút **Xem log** mở
`agent.log`. Bản thân cửa sổ không cần mở để agent chạy — nó chỉ là
nơi cấu hình + xem trạng thái.

Chạy bằng tay vẫn được như cũ: `beesky-agent run` (console, thấy
log trực tiếp — output đồng thời vẫn ghi vào `agent.log`), hoặc
`beesky-agent run --background` để ép chế độ ngầm trên bản console.
Chạy thẳng `beesky-agentw.exe` (không tham số) cũng là chạy ngầm
theo cấu hình mặc định.

## Cấu hình nằm ở đâu

Một file JSON duy nhất:

| Hệ điều hành | Đường dẫn |
|---|---|
| Windows | `%APPDATA%\BeeSky\agent-config.json` |
| Linux/macOS | `~/.beesky/agent-config.json` |
| Ghi đè | biến môi trường `BEESKY_AGENT_CONFIG`, hoặc cờ `--config FILE` |

Nội dung tối thiểu:

```json
{
  "target": "192.168.1.10-192.168.1.60",
  "cloud_url": "https://cloud.example.com",
  "key": "<agent key>",
  "site": "Xưởng 1",
  "interval": 30,
  "notify_config": null,
  "auto_update": false
}
```

- `notify_config`: cấu hình kênh cảnh báo **tại trại** (Telegram /
  webhook — cùng định dạng file `--notify` của lệnh `beesky agent`,
  xem `docs/notify.example.json`). Để `null` nếu chỉ cần cloud.
- `auto_update`: xem mục Cập nhật bên dưới.
- Các trường phụ (ít dùng): `timeout`, `workers`, `user`, `password`
  (mật khẩu web firmware gốc), `api_key`, `token` (dashd/VNish),
  `http_port`, `cgminer_port`, `update_url` — mặc định trùng với
  dòng lệnh `beesky agent`.

**Bảo mật** (v0.16): file cấu hình *là* thông tin đăng nhập của
agent, nên key được bảo vệ theo hệ điều hành:

- **Windows — DPAPI**: key lưu trong trường `key_protected` (mã hoá
  bằng Windows DPAPI, phạm vi *toàn máy* — `key` để trống). Phạm vi
  toàn máy là bắt buộc vì tác vụ chạy ngầm bằng SYSTEM. Ý nghĩa:
  file bị chép sang máy khác thì **không giải mã được**; nhưng
  admin của chính máy đó vẫn giải mã được — DPAPI chống lộ file ra
  ngoài, không chống người đã nắm máy. File cấu hình cũ (key dạng
  rõ) tự được nâng cấp sang dạng bảo vệ ở lần Lưu tiếp theo. Nếu
  DPAPI lỗi lúc lưu, app quay về lưu dạng rõ thay vì mất cấu hình.
- **Linux/macOS**: key vẫn dạng rõ, nhưng file được `chmod 0600`
  sau mỗi lần lưu (Windows cũng siết ACL chỉ còn tài khoản hiện tại
  + SYSTEM, theo kiểu best-effort).
- Cloud chỉ lưu bản băm SHA-256 của key và thu hồi key bất cứ lúc
  nào được (trang Cài đặt của cloud). Mang file cấu hình sang máy
  khác: key bảo vệ bằng DPAPI sẽ không đọc được ở máy mới — tạo
  agent mới trên cloud và dán key mới.

**Nên dùng https cho cloud**: nếu *Cloud URL* là `http://` trỏ ra
ngoài máy/mạng nội bộ, agent key sẽ đi qua mạng **dạng rõ**. Agent
vẫn chạy (cloud trong LAN nội bộ dùng http là chấp nhận được),
nhưng sẽ ghi một dòng CẢNH BÁO vào log mỗi lần chạy, và cửa sổ cấu
hình hiện gợi ý tương tự ngay dưới ô Cloud URL.

Mọi chế độ dòng lệnh đều ghi đè được từng trường của file, vd:

```
beesky-agent run --config C:\duong-dan\agent-config.json
beesky-agent test --site "Xưởng 2" --interval 60
beesky-agent run 192.168.1.0/24 --cloud https://... --key ... --site "Xưởng 1" --once
```

## Cập nhật

`beesky-agent.exe` tự cập nhật qua **cùng kênh đã ký** như
`beesky.exe` (xem `docs/updating.md`): bản phát hành kèm
`update-manifest.json` đã ký liệt kê cả `beesky-agent.exe`,
`beesky-agentw.exe` (từ v0.16 — chính tiến trình chạy ngầm là tiến
trình cần tự cập nhật nhất) và `BeeSkyAgentSetup-<version>.exe`;
updater chọn đúng file trùng tên exe đang chạy. Như agent dạng
lệnh, mặc định agent app chỉ *báo* có bản mới lên cloud (sự kiện
`UPDATE_AVAILABLE`); muốn tự áp luôn thì đặt `"auto_update": true`
trong cấu hình (hoặc chạy agent với `--auto-update`). Chủ trại
cũng luôn cài đè được bằng bộ cài `BeeSkyAgentSetup` mới — cấu
hình nằm ngoài thư mục cài đặt nên không mất.

**Kiểm tra file tải về**: mỗi bản phát hành công bố SHA-256 của
từng file trong `update-manifest.json` (file này được ký bằng
khoá của chủ dự án — xem `docs/updating.md`). Trước khi cài, đối
chiếu hash của bộ cài vừa tải với giá trị trong manifest, ví dụ
PowerShell: `Get-FileHash .\BeeSkyAgentSetup-<version>.exe` rồi so
với mục `BeeSkyAgentSetup-<version>.exe` trong manifest của đúng
tag phát hành đó. Hash lệch = file không nguyên vẹn, đừng cài.
