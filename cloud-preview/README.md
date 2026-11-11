# BeeSky Cloud — bản duyệt giao diện

Prototype local để duyệt trước khi triển khai backend nhiều khách hàng. Không phải hệ thống đăng nhập thật; không gửi email, không kết nối máy đào và không lưu mật khẩu. Dữ liệu và các thay đổi mẫu chỉ tồn tại trong bộ nhớ trang, tải lại sẽ khôi phục bản mẫu.

Chạy từ repository:

```text
python -m http.server 8790 --bind 127.0.0.1 --directory cloud-preview
```

Mở http://127.0.0.1:8790/#/overview hoặc http://127.0.0.1:8790/#/signup.

Các liên kết ở thanh trên cùng cho phép duyệt đăng nhập, đăng ký, tài khoản mới và dashboard mẫu. “Vào dashboard” khôi phục tổ chức và các xưởng mẫu sau khi đã thử onboarding.

Đã kiểm tra trên trình duyệt: đăng ký mẫu → màn xác thực → tạo xưởng đầu tiên; mời thành viên mẫu; dashboard desktop; menu mobile ở chiều rộng 390px và nội dung không tràn ngang. Kiểm tra cú pháp JavaScript bằng `node --check cloud-preview/app.js`.

Kế hoạch backend và các tiêu chí bảo mật: `docs/cloud-accounts-plan.md`. Phương án Django/PostgreSQL trong kế hoạch là đề xuất để triển khai sau khi duyệt, chưa thay stack cloud hiện tại.


## Cập nhật bản duyệt: Agent, Workflow action và Tác vụ — 11/11/2026

Đã triển khai trong `cloud-preview/operations.js` và `operations.css`:

- Agent theo xưởng, chế độ giám sát/điều khiển, thêm/sửa cấu hình và dải IPv4 cho tác vụ quét. Mặc định agent mới chỉ giám sát. Chưa cấp mã kết nối thật.
- Workflow dạng chuỗi: kích hoạt → phạm vi xưởng/rack/model → nhiều action có thể thêm, bỏ, đổi thứ tự. Kích hoạt theo điều kiện, lịch hoặc phát hiện máy mới.
- Action: khởi động máy, khởi động trình đào, dừng/tiếp tục đào, đổi pool, làm mát, bật/tắt board, gửi API/Webhook HTTPS.
- Lưu bản nháp, mô phỏng chỉ số/thời gian giữ/cooldown; chi tiết từng máy và từng action tại Tác vụ. Action đầu chờ Agent thì các action sau chờ bước trước; không tạo kết quả thành công giả.
- Dropdown dùng component chung. Đã duyệt trên Chrome ở 1366×768 và 390×844; không tràn ngang tại các màn Agent và builder đã kiểm tra. Sidebar có vùng cuộn để tới các mục quản lý.
- Đã thử tạo/sửa Agent và dải IP; lưu workflow, đổi action/thứ tự, mô phỏng điều kiện đạt và chưa đủ thời gian. Đã sửa lỗi mất ngày mặc định khi đổi sang lịch tuần. Tài khoản mới có 0 Agent và 0 Workflow mẫu.

Giới hạn: toàn bộ cấu hình nằm trong bộ nhớ trang; tải lại sẽ khôi phục fixture. Chưa có xác thực, phân quyền server, cách ly tenant thực tế, hàng đợi, lịch thực thi, gửi webhook hoặc lệnh xuống máy. Đây là bản duyệt giao diện trước backend; không dùng để vận hành xưởng thật.

Bước tiếp theo sau duyệt: triển khai tài khoản/tenant và quyền theo xưởng ở server; lưu cấu hình; nhật ký thay đổi; giao thức Agent với mã riêng từng xưởng, thu hồi/luân chuyển mã; hàng đợi lệnh có thời hạn và xác nhận kết quả; webhook có chữ ký và chặn đích nội bộ/SSRF. Agent thực thi triển khai ở giai đoạn sau.


## React Flow và MCP (cập nhật)

Workflow hiện dùng React 19 và @xyflow/react 12: canvas kéo khối, zoom/pan, khớp khung, sắp xếp lại, chọn khối để sửa bằng inspector; giữ schema và mô phỏng tuần tự cũ. Dây nối biểu diễn thứ tự action, chưa hỗ trợ nhánh tùy ý. Vị trí khối lưu cùng bản nháp trong bộ nhớ. Dropdown tiếp tục dùng component chung.

Source: `flow-editor/editor.jsx`, `flow-editor/editor.css`, bridge `flow-bridge.js`. Bundle JS/CSS đã có sẵn để server static chạy offline, không tải thư viện từ CDN. Build lại: `npm ci --prefix cloud-preview/flow-editor` rồi `npm run build --prefix cloud-preview/flow-editor`. Lệnh build tự cập nhật query hash asset trong index.html để tránh cache trộn phiên bản.

Mục AI & MCP trong bản duyệt mô tả trạng thái kết nối, chưa nối backend. Backend thật có endpoint MCP chỉ đọc tại `/mcp`; xem `docs/mcp-reporting.md`. Endpoint không được bật quyền mặc định, chưa thay thế hệ thống tenant cần triển khai.


## Giao diện sáng / tối

Nút mặt trăng / mặt trời ở thanh trên đổi theme cho dashboard, form, dialog, dropdown, rack và React Flow. Trang đăng nhập/đăng ký cũng có nút đổi theme. Mặc định theo hệ điều hành; sau khi chọn sẽ lưu `beesky-color-theme` trong localStorage, độc lập với dữ liệu tài khoản mẫu. Nếu browser không cho lưu thì vẫn đổi được theme trong phiên hiện tại. Đổi theme không remount canvas hoặc xóa form đang chỉnh.

Source: `theme.js` chạy trước paint, `theme.css` chứa token/override sáng; React Flow nhận sự kiện theme để đổi edge/background và colorMode. Đã kiểm tra Chrome 1366×768 và 390×844, lưu theme tối qua reload, dropdown sáng, rack sáng, đăng nhập sáng, đổi qua lại trong workflow đang sửa vẫn giữ ngưỡng nhập. Không ghi nhận lỗi console trong phiên kiểm tra cuối.
