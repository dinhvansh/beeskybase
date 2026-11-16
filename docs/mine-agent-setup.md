# Tải Scanner và kết nối Agent với Mine

1. Vào trang giới thiệu Mine, chọn **Tải tool scan cho Windows**. Bộ cài đầy đủ có Scanner và Agent; giữ thành phần Agent khi cài. Máy chỉ chạy giám sát có thể tải bộ Agent riêng.
2. Đăng nhập Cloud, mở **Agent**, chọn xưởng và bấm **Tạo token Agent**. Sao chép token đang hiện; token không thể xem lại từ danh sách.
3. Mở Scanner và chọn **Chế độ Agent**. Cả giao diện Flutter và giao diện Tk đều có lối vào này. Dán token, đặt Cloud URL (`https://mine.beeskybase.com`, hoặc địa chỉ Cloud local khi thử nghiệm) và bấm **Kiểm tra token**.
4. Phần mềm tự nhận agent, tổ chức và xưởng từ Cloud. Xưởng là thông tin chỉ đọc; token luôn bị giới hạn trong xưởng đã chọn trên web.
5. Nhập dải IP trên mạng được phép quét và chu kỳ quét, rồi bấm **Bắt đầu Agent**. Máy chạy Agent phải truy cập được miner trong LAN. Web Cloud không tự quét mạng.
6. Chỉ coi bản quét đã gửi thành công khi trạng thái Agent hoặc Cloud ghi nhận kết quả. Kiểm tra token chỉ đọc thông tin kết nối, không cập nhật heartbeat và không bắt đầu quét.

**Dừng Agent** dừng phiên do chính cửa sổ/phần mềm này mở. Có thể bật tự khởi động cùng Windows bằng Scheduled Task (đăng ký SYSTEM cần quyền quản trị). Mỗi file cấu hình chỉ có một vòng Agent chạy đồng thời; mở thêm từ app khi tác vụ đang chạy sẽ bị từ chối, tránh quét/gửi dữ liệu trùng.

Thu hồi token trên Cloud sẽ chặn cả kiểm tra kết nối và các lần gửi bản quét tiếp theo. Dữ liệu và vị trí máy đã nhận không bị xóa. Muốn đổi xưởng, tạo token của xưởng mới và cấu hình lại Agent.

## Đường dẫn tải

- `/downloads/scanner` trên domain Mine chuyển đến bộ cài đầy đủ chính thức trên GitHub Releases.
- `/downloads/agent` chuyển đến bộ cài Agent riêng.
- Bản 0.40.2 bổ sung Chế độ Agent trong Scanner và kiểm tra token với Cloud. ZIP Flutter Scanner cũng kèm cả engine Scanner và engine Agent.

## Kiểm tra

`python -m unittest tests.test_agent_connection` kiểm tra kết nối HTTP loopback, token sai, từ chối chuyển hướng mang token, bảo vệ khóa trong cấu hình và khóa chạy trùng.

`python cloud_service/manage.py test core.tests.test_ingest_placement.IngestTests` kiểm tra giới hạn token theo xưởng, thu hồi token, ingest và các đường dẫn tải.

Flutter kiểm tra giao diện bằng `flutter analyze` và `flutter test` trong từng thư mục `app_flutter` và `app_agent_flutter`. Các bài kiểm tra dùng dữ liệu tổng hợp, không quét thiết bị thật.

## Kết quả kiểm tra bản 0.40.2 — 15/11/2026

- 6 kiểm tra Python về kết nối, khóa chạy trùng và đường dẫn engine cho tác vụ tự khởi động: đạt.
- 11 kiểm tra backend về ingest, quyền theo token/xưởng và tải công cụ: đạt. CI PostgreSQL, hai ứng dụng Flutter và bộ cài Windows đều thành công tại tag `v0.40.2`.
- Luồng web với backend local thật: tạo/sao chép token, lấy đúng xưởng mà không tạo heartbeat, nhận bản quét, hiển thị máy và thu hồi token: đạt. Tài khoản/xưởng kiểm thử đã được xóa.
- Engine Agent thật quét một miner giả lập chỉ tại loopback `127.0.0.1`, rồi gửi thiết bị lên đúng xưởng trong Cloud local: đạt. Không dùng miner vật lý.
- Cửa sổ Tk vừa màn hình 1280×800, nút bắt đầu/lưu luôn hiện; trang tải và trang Agent đã kiểm tra ở desktop/mobile.
- Hai đường tải trên domain Mine trả đúng bộ cài 0.40.2, file tải trả HTTP 200; trang giới thiệu hiển thị bản mới và Cloud sẵn sàng.
