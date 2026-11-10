# BeeSky Agent — app agent riêng tại trại (v0.14)

Từ v0.14, agent tại trại là **một app riêng** (`beesky-agent.exe`,
bộ cài `BeeSkyAgentSetup-<version>.exe`) thay vì chỉ là một lệnh con
của bộ công cụ chính. Máy PC ở trại chỉ cần cài đúng app này: mở lên,
điền cấu hình một lần trong cửa sổ, bấm chạy thử, bật tự khởi động —
xong, agent tự quét máy đào trong mạng trại và đẩy số liệu lên
BeeSky Cloud như trước (kiến trúc agent → cloud giữ nguyên, xem
`docs/cloud.md`).

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
4. **Bật tự khởi động**: bấm *Bật tự khởi động* — app tạo Windows
   Scheduled Task tên **BeeSky Agent** chạy `beesky-agent run` mỗi
   lần máy khởi động, để agent sống sót qua reboot / mất điện.
   - Tác vụ chạy lúc khởi động máy (ONSTART) thường cần quyền admin:
     nếu Windows báo lỗi, mở app bằng *Run as administrator* rồi bấm
     lại.
   - Muốn tắt: bấm lại nút đó (đổi thành *Tắt tự khởi động*), hoặc
     chạy `beesky-agent remove-task`.

Từ đây agent chạy nền vĩnh viễn. Muốn xem log: mở console chạy
`beesky-agent run` bằng tay (chính là lệnh tác vụ tự động chạy).

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

**Bảo mật**: key nằm dạng rõ trong file này — file cấu hình *chính
là* thông tin đăng nhập của agent (giống cách các agent farm khác
hoạt động). Cloud chỉ lưu bản băm SHA-256 và thu hồi key bất cứ lúc
nào được (trang Cài đặt của cloud); nhưng ai đọc được file này đều
giả danh agent được cho tới khi bị thu hồi. Để file trên đúng máy
trại, chỉ tài khoản chạy agent đọc được.

Mọi chế độ dòng lệnh đều ghi đè được từng trường của file, vd:

```
beesky-agent run --config C:\duong-dan\agent-config.json
beesky-agent test --site "Xưởng 2" --interval 60
beesky-agent run 192.168.1.0/24 --cloud https://... --key ... --site "Xưởng 1" --once
```

## Cập nhật

`beesky-agent.exe` tự cập nhật qua **cùng kênh đã ký** như
`beesky.exe` (xem `docs/updating.md`): bản phát hành kèm
`update-manifest.json` đã ký liệt kê cả `beesky-agent.exe` và
`BeeSkyAgentSetup-<version>.exe`; updater chọn đúng file trùng tên
exe đang chạy. Như agent dạng lệnh, mặc định agent app chỉ *báo* có
bản mới lên cloud (sự kiện `UPDATE_AVAILABLE`); muốn tự áp luôn thì
đặt `"auto_update": true` trong cấu hình (hoặc chạy agent với
`--auto-update`). Chủ trại cũng luôn cài đè được bằng bộ cài
`BeeSkyAgentSetup` mới — cấu hình nằm ngoài thư mục cài đặt nên
không mất.
