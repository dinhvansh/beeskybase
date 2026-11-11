# BeeSky — MCP báo cáo

## Đã triển khai

Cloud hiện có `POST /mcp`, MCP Streamable HTTP, trả JSON, không mở luồng SSE. Đã kiểm tra bằng MCP Python SDK với `initialize`, `tools/list`, `tools/call`. Không cần thêm dependency để chạy server.

| Công cụ | Dữ liệu | Giới hạn |
| --- | --- | --- |
| `list_farms` | Tổng quan các trại có quyền | Không nhận tenant/site override |
| `list_miners` | Máy, trạng thái, nhiệt, hashrate và đơn vị gốc | Bắt buộc site, tối đa 200 dòng/trang, offset |
| `list_events` | Thời gian, máy, loại, mức độ sự kiện | Bắt buộc site, tối đa 200 sự kiện |
| `get_hashrate_history` | Mẫu hashrate TH/s | Bắt buộc site, 1–168 giờ, phân trang |
| `get_energy_report` | kWh theo ngày, tổng kWh, chi phí ước tính VND | Bắt buộc site, 1–31 ngày |

Nguồn: database cloud hiện tại, **không phải** dữ liệu mẫu trong `cloud-preview`. Thiết bị chưa gửi dữ liệu sẽ có kết quả rỗng. Các báo cáo có thời gian tạo; máy có thời điểm snapshot. TH/s lịch sử là nhóm hashrate tương thích của backend, không cộng sol/s với H/s. Điện năng phụ thuộc telemetry và ngày theo múi giờ server; chi phí dùng giá điện cấu hình hiện tại, không phải hóa đơn.

## Cấp quyền phía server

MCP luôn yêu cầu `Authorization: Bearer <reporting-token>`, ngay cả khi dashboard cũ đang ở chế độ mở. Không dùng khóa Agent, mật khẩu quản trị hay cookie browser làm quyền MCP.

Đặt `BEESKY_MCP_GRANTS_FILE` trỏ tới file JSON riêng **ngoài thư mục phục vụ web và ngoài Git**. File chỉ chứa hash SHA-256 của token, mã quyền, danh sách tên trại chính xác và hạn dùng Unix timestamp:

```json
[
  {
    "id": "reporting-owner-a",
    "token_sha256": "<64 ký tự hex SHA-256 của token>",
    "sites": ["Tên trại chính xác trong database"],
    "expires_at": 1800000000,
    "revoked": false
  }
]
```

Token phải là chuỗi ngẫu nhiên ít nhất 32 ký tự; nên sinh bằng `secrets.token_urlsafe(32)`. Chỉ giao token gốc cho ứng dụng AI được cho phép, lưu trong secret store của ứng dụng đó. Bảo vệ file grants bằng quyền filesystem của tài khoản chạy cloud. Token không nằm trong URL, frontend bundle hay localStorage.

Server đọc lại file mỗi request: đặt `revoked: true`, xóa dòng grant hoặc đổi hash sẽ thu hồi quyền ngay. Thiếu file, file lỗi, danh sách site rỗng, wildcard hoặc hết hạn đều từ chối truy cập. Cập nhật file bằng thay thế nguyên tử để tránh trạng thái ghi dở.

Cloud vẫn chạy bằng lệnh hiện có:

```text
python -m beesky cloud --host 127.0.0.1 --port 8788 --db beesky-cloud.db
```

Ứng dụng AI cấu hình URL `https://<cloud-của-bạn>/mcp`, transport Streamable HTTP và Bearer token riêng. Local development dùng `http://127.0.0.1:8788/mcp`. Cấu hình TLS ở reverse proxy khi đưa ra mạng; không mở quyền MCP qua dashboard cũ. Nếu client dùng OAuth tự động thì cần bổ sung authorization server ở giai đoạn tài khoản; hiện dùng token cấu hình sẵn, chưa có OAuth discovery.

## Bảo vệ đã có

- Chỉ có 5 công cụ đọc; không có reboot, thay pool, chạy workflow, SQL tùy ý hay gửi HTTP ra ngoài.
- Site được so khớp với allowlist server trước khi đọc dữ liệu. Thiếu site không được chuyển thành truy vấn tất cả trại.
- Projection chỉ trả các trường báo cáo; bỏ raw payload, mật khẩu, khóa Agent, hash khóa và detail tự do của sự kiện.
- Giới hạn body 32 KiB, payload báo cáo 1 MiB, tối đa 60 request/phút/grant/process. Truy vấn lỗi không tiết lộ SQL.
- Mặc định từ chối mọi header Origin; nếu có browser client hợp lệ, khai báo chính xác qua `BEESKY_MCP_ALLOWED_ORIGINS` (phân tách dấu phẩy). Không bật CORS wildcard.
- Log mỗi lần gọi tool: mã quyền, tên tool, thời gian, kết quả; không log token hoặc dữ liệu báo cáo. Đây là log tiến trình, chưa phải nhật ký bền vững trong database.
- Phản hồi `Cache-Control: no-store`. GET MCP trả 405; endpoint stateless không tạo session MCP.

## Giới hạn trước khi dùng nhiều khách hàng

Cloud cũ dùng một tài khoản quản trị và site dạng tên; **chưa có hệ thống tenant/account production**. Grants hiện do quản trị viên quản lý, chưa tự suy ra membership của người đăng ký. Khi làm backend nhiều khách hàng, phải chuyển sang tenant ID và farm ID ổn định, kiểm tra membership mỗi request, UI cấp/thu hồi quyền và audit bền vững. Không đổi tên hoặc tái sử dụng tên site đã được cấp quyền cho khách khác; phải thu hồi grant trước.

Rate limit hiện nằm trong process. Triển khai nhiều instance cần quota tập trung. Các hàm đọc hiện tải dữ liệu site rồi cắt trang; farm rất lớn cần phân trang ngay trong SQL. Rack/slot và lịch sử workflow trong prototype chưa lưu backend nên chưa được công bố qua MCP.

## Kiểm tra

```text
python -m unittest discover -s tests -p test_mcp_reporting.py -v
```

5 bài kiểm tra đã đạt: handshake/catalog/read; chặn khác trại/thiếu site/tham số thừa/lệnh ghi; hết hạn và thu hồi; Origin/version/body bounds và API cũ; kết nối qua MCP Python SDK chính thức. Bài SDK tự bỏ qua nếu máy chưa cài SDK.
