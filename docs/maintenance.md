# Bảo trì định kỳ

## Sử dụng

1. Mở **Bảo trì định kỳ → Tạo lịch hằng tháng**. Chọn xưởng, phạm vi cả xưởng/kệ/nhóm đường nước/một máy; đặt người phụ trách, tháng bắt đầu và ngày hạn.
2. Chọn mẫu máy gió, máy nước hoặc điện; chỉnh checklist từng dòng. Có thể yêu cầu ảnh cho mỗi mục được áp dụng.
3. Phiếu tháng hiện tại được tạo ngay khi đến tháng bắt đầu. Các tháng tiếp theo tạo từ đầu tháng, với hạn theo ngày đã chọn. Ngày 29–31 được chặn về ngày cuối tháng phù hợp.
4. Mở phiếu, điền Đạt / Không đạt / Không áp dụng. Ghi số đo hoặc ghi chú vào từng mục. Không đạt phải mô tả lỗi; Không áp dụng phải có lý do.
5. Chụp/chọn ảnh trước–sau cho đúng hạng mục. Ảnh xem được ở kích thước lớn khi bấm vào hình. Bấm **Lưu nháp** để lưu checklist lên máy chủ.
6. Nếu có lỗi, **Tạo phiếu sửa từ lỗi** để chọn máy trong danh sách của phiếu. Phiếu sửa có liên kết ngược trong Lịch sử sửa chữa. Chi phí sửa ghi riêng, báo cáo không cộng lại vào tổng chi phí bảo trì.
7. **Gửi xác nhận** kiểm tra đủ checklist, ghi chú và ảnh bắt buộc. Phiếu chờ xác nhận khóa sửa checklist/ảnh. Người xác nhận có thể yêu cầu bổ sung với lý do hoặc xác nhận hoàn tất.
8. Lọc tháng/xưởng rồi mở **Báo cáo · In / lưu PDF**. Báo cáo chứa trạng thái, người thực hiện/xác nhận, chi phí, checklist, ảnh, máy trong phạm vi và lịch sử. Bấm In / Lưu PDF, chọn Save as PDF trong trình duyệt.

## Lưu trữ và tính toàn vẹn

- Các bảng `maintenance_schedules`, `maintenance_tickets`, `maintenance_photos` lưu cùng SQLite với dữ liệu cloud. Ảnh lưu dạng BLOB, không có thư mục ảnh công khai. Lấy ảnh qua API có cùng kiểm tra đăng nhập như các trang quản trị.
- Phiếu lưu bản chụp checklist, phiên bản mẫu và máy trong phạm vi theo bố trí đã lưu tại lúc tạo. Chỉnh mẫu/đổi vị trí máy sau đó không sửa phiếu cũ. Nhóm máy và danh sách khách cũng được đưa vào bản lưu bố trí.
- Phạm vi xưởng/kệ/nhóm là một checklist cho phạm vi đó. Cần kiểm tra riêng từng máy thì lập lịch với phạm vi **Một máy**.
- Phiếu hoàn tất khóa checklist/ảnh. Lịch sử ghi thời gian máy chủ và tên người nhập; đây là workspace quản trị chung, tên nhập thủ công, chưa phải chữ ký điện tử hoặc phân quyền duyệt theo tài khoản cá nhân.
- Mọi thay đổi phiếu/lịch có revision, ngăn cửa sổ/người dùng khác ghi đè âm thầm. Khi gặp xung đột, đọc lại bản máy chủ trước khi sửa tiếp.
- Nội dung checklist đang nhập có nháp cục bộ theo ID + revision. Chỉ phục hồi khi khớp phiên bản máy chủ, không tự ghi đè bản mới của người khác. Ảnh chỉ được lưu sau khi chọn và tải lên thành công; ảnh chưa tải không thuộc bản nháp cục bộ.
- Trình duyệt thu nhỏ ảnh về cạnh dài tối đa 1600px và mã hóa JPEG. Máy chủ nhận JPEG/PNG/WebP tối đa 4 MB, 8 ảnh/mục và 120 ảnh/phiếu. Thời gian trên ảnh là thời gian tải lên, không lấy EXIF hay khẳng định thời điểm chụp. HEIC cần chuyển JPEG trước khi tải.
- Sao lưu SQLite bao gồm cả ảnh. Khi sao lưu bằng cách chép file thủ công, dừng máy chủ trước; không đưa database/mã agent lên Git.

## Lịch máy chủ

`MaintenanceScheduler` chạy mỗi 60 giây trong cả `run_cloud_server` và `tools.serve_preview`, dùng ngày Việt Nam UTC+7. Mỗi cặp lịch/tháng có ràng buộc UNIQUE nên không tạo trùng khi khởi động lại. Nếu máy chủ dừng, khi chạy lại sẽ bù các tháng đã lỡ. Không thể tạo phiếu vào đúng thời điểm khi chính máy chủ đang tắt.

Tạm dừng lịch không xóa phiếu cũ. Tiếp tục sẽ bù các tháng chưa có phiếu. Sửa lịch/mẫu chỉ ảnh hưởng phiếu tạo sau đó. Ứng dụng chưa gửi thông báo lịch qua email/Telegram và chưa cài tự khởi động máy chủ cùng Windows.

## API

- `GET /api/maintenance?month=YYYY-MM&site=...`: lịch, phiếu, thống kê, mẫu checklist.
- `POST /api/maintenance/schedules`: tạo/sửa lịch với revision.
- `POST /api/maintenance/schedules/{id}/toggle`: tạm dừng/tiếp tục.
- `GET|POST /api/maintenance/tickets/{id}`: đọc phiếu; save/submit/approve/return.
- `POST /api/maintenance/tickets/{id}/photos`: ảnh base64 + itemId + before/after + revision.
- `POST /api/maintenance/tickets/{id}/photos/{photoId}/delete`: xóa ảnh ở phiếu còn chỉnh sửa.
- `GET /api/maintenance/photos/{photoId}`: dữ liệu ảnh, kiểm tra phiên người xem, nosniff, no-store.
- `POST /api/maintenance/tickets/{id}/repairs`: tạo phiếu sửa cho mục Không đạt và máy trong phạm vi.
- `GET /api/maintenance/report?month=YYYY-MM&site=...`: báo cáo HTML để in/PDF.

## Kiểm chứng

12 bài kiểm tra dịch vụ/API bao gồm cuối tháng và năm nhuận, bù tháng, không trùng phiếu, khóa phiếu, ảnh tồn tại qua lần mở lại SQLite, phạm vi site/máy, quyền xem ảnh, revision, liên kết sửa chữa và escape nội dung báo cáo. Kiểm tra trình duyệt đã đi hết luồng tạo lịch → lưu checklist → tải ảnh → tạo phiếu sửa → xác nhận → tải lại → xuất PDF, cùng giao diện điện thoại. Ảnh và phiếu kiểm tra nằm ở database tạm, không thêm vào hồ sơ người dùng.
