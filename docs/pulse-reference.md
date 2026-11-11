# Đối chiếu HashCore Pulse và định hướng BeeSky Cloud

Ngày kiểm tra: 11/11/2026. Bản Pulse hiển thị v1.0.0a4.

## 1. Phạm vi kiểm chứng

Đã mở trực tiếp phiên Chrome người dùng đăng nhập. Dùng tab tham khảo riêng, giữ nguyên form automation đang mở của người dùng. Chỉ xem màn hình và thay lựa chọn trong form chưa lưu; không tạo agent/quy tắc, không gửi lệnh xuống máy, không thay cấu hình tài khoản.

Tài khoản Personal hiện không có máy và chưa có rule. Vì vậy không thể xác minh dữ liệu telemetry thực, chi tiết một máy đang chạy, tiến trình gửi lệnh hay kết quả automation thực tế. Không có quyền đọc mã nguồn/backend Pulse; “core giống Pulse” trong tài liệu này nghĩa là hành vi chức năng quan sát được và được mô tả công khai, không phải sao chép triển khai nội bộ.

## 2. Các màn hình đã xem trực tiếp

| Mục | Quan sát trên Pulse | Định hướng BeeSky |
|---|---|---|
| Dashboard /dashboard | Lọc thuật toán/khoảng thời gian; hashrate trung bình và realtime, số máy theo trạng thái, công suất và tỷ lệ dùng công suất, ước tính doanh thu/tiền điện | Dashboard gọn, giữ thông số hữu ích; phân biệt đo thực với ước tính, dữ liệu thiếu không biến thành số đo 0 |
| Miners /miners | All/Online/Offline; Metrics, Sort by, Filter. Bộ lọc model, firmware provider/version, platform, thuật toán, lock state, status, pool account, locate, service mode, scan task, filter preset | Danh sách là màn hình vận hành chính, bộ lọc lưu được, chọn nhiều máy, cột tùy chỉnh, thao tác theo khả năng firmware |
| Agents /agents | Agent dạng thẻ: IP nội bộ, số scan task, máy active/found, phiên bản, control mode; có nhóm All/Disabled/Removed | Mục Agent riêng theo trại; trạng thái kết nối tách trạng thái bật/tắt; không gom vào nút tạo mã ở trang Trại |
| New agent | Tên, mô tả, control mode; tạo agent là bước trước cấp thông tin kết nối | Thiết kế sẵn form và màn hình cấp mã nhưng ghi rõ chưa nối backend; không tạo mã giả như đã dùng được |
| Scan tasks /agents/{id} | Import, Export all, New task. Form có tên/mô tả, nhiều dải IP, Aggregate IP, tab Unlock configs theo nhóm xác thực thiết bị | Agent → tác vụ quét → dải IP và cấu hình xác thực. Đây là cấu hình cloud chuẩn bị trước; scanner triển khai sau |
| Automation /automation | All/Schedule/Condition; tên, scope, trigger, action, thông báo và bật rule | BeeSky dùng trình dựng workflow theo action thay cho form rule đơn |
| Schedule | Một lần/lặp lại, giờ, ngày trong tuần; diễn giải lịch theo timezone trại và lần chạy kế tiếp | Nút trigger lịch có lịch xem trước và timezone rõ ràng |
| Condition | Property gồm Chip Temperature, Hashrate Efficiency, Fan Duty, Status; toán tử/giá trị, thời gian duy trì, cooldown | Nút trigger/condition riêng, bộ đánh giá lưu trạng thái theo từng máy |
| Actions | Reboot, Restart, Pause mining, Resume mining, Pool config, Thermal control; Boards config xuất hiện với Condition | Mỗi action có form tham số riêng và kiểm tra khả năng máy/firmware |
| Thermal control | Auto, số quạt tối thiểu, nhiệt độ mục tiêu, giới hạn tốc độ quạt | Action làm mát có cấu hình thực tế; không chỉ một nhãn hoặc webhook |
| Activity | Active / Alert / History, bộ lọc thời gian | Trung tâm tác vụ chung cho thao tác tay và workflow, chi tiết đến từng máy/action |
| Firmware Suites /suites | Bộ firmware có nhà cung cấp, số model/platform/firmware và thời gian tạo/cập nhật | Thư viện firmware chuẩn bị cho giai đoạn điều khiển; cần ma trận tương thích và kiểm tra file |
| Space settings | Timezone, tiền tệ, giá điện, công suất trại, số máy mỗi lô và thời gian nghỉ giữa lô | Cấu hình cấp trại, áp dụng cho mọi đường gửi lệnh |

## 3. Nguyên tắc vận hành lấy từ tài liệu chính thức

- Một trại có nhiều agent; scan task thuộc agent; máy do agent phát hiện. Cấu trúc mạng này độc lập sơ đồ vật lý trại/khu/rack/tầng/ô của BeeSky. Nguồn: https://docs.hashcore.com/en/pulse/concepts/hierarchy
- Monitoring Only vẫn thu thập số liệu nhưng từ chối lệnh điều khiển; tạm dừng agent khác mất kết nối. Nguồn: https://docs.hashcore.com/en/pulse/agents/agent-modes
- Scope tính tại thời điểm trigger; loại máy service mode/locked; lịch một lần tự tắt sau chạy; lỗi một máy không chặn máy khác. Nguồn: https://docs.hashcore.com/en/pulse/automation/scheduled-automation
- Điều kiện phải giữ liên tục và cooldown tính từng máy; mất kết nối reset thời gian duy trì. Chỉ số nhiệt/hiệu suất/quạt chỉ xét máy online. Boards config chỉ dành cho condition trong Pulse. Nguồn: https://docs.hashcore.com/en/pulse/automation/automation-by-event
- Khả năng thao tác khác nhau theo firmware/nhà sản xuất; thao tác hàng loạt phải có kết quả bỏ qua cho máy không hỗ trợ. Nguồn: https://docs.hashcore.com/en/pulse/about/supported-devices
- Thao tác hàng loạt chạy theo lô; theo dõi kết quả riêng từng máy. Nguồn: https://docs.hashcore.com/en/pulse/workers/group-operations
- Vai trò và phạm vi trại được mô tả trong alpha4; chưa kiểm chứng UI Organization vì tài khoản đang ở Personal. Nguồn: https://docs.hashcore.com/en/pulse/whats-new/latest-release

## 4. Thiết kế workflow BeeSky theo yêu cầu đã chốt

### Giao diện

Danh sách workflow → mở trình dựng gồm các bước nối nhau:

Trigger → Phạm vi máy → Điều kiện/giữ liên tục → Action → Kết quả.

- Trigger: lịch một lần/lặp, thay đổi trạng thái hoặc chỉ số, máy mới. Phân biệt trigger theo dữ liệu online với sự kiện mất kết nối.
- Scope: trại bắt buộc; rack, model, firmware, tag/scan task hoặc danh sách máy. Xem trước số máy phù hợp; lúc chạy tính lại phạm vi với quyền hiện hành.
- Action là trung tâm cấu hình: Reboot; Restart mining process; Pause; Resume; Pool config; Thermal control; Boards config; Webhook/API. Các action mở đúng form của nó. Không yêu cầu URL webhook khi action chỉ điều khiển máy.
- Mỗi node có cấu hình, tóm tắt và trạng thái hợp lệ. Có bản nháp, bật/tạm dừng, sao chép, lịch sử, xem trước máy và mô phỏng. Mô phỏng không gửi lệnh, không giả HTTP 200 hay thành công thực tế.
- Giai đoạn đầu dùng chuỗi tuyến tính, không vòng lặp. Có thể thêm nhiều action tuần tự; lỗi thì dừng chuỗi của máy đó hoặc tiếp tục theo lựa chọn có giải thích. AND/OR hoặc nhánh chỉ đưa vào khi schema/executor thực sự hỗ trợ.
- Giao diện gọn theo màn laptop, component dùng chung. Không thêm banner/đoạn giới thiệu trang trí; tên màn hình nằm ở thanh điều hướng. Các thông tin chưa hoạt động ghi ngay tại chức năng liên quan.

### Bộ xử lý phía dưới: đặc tả đề xuất, chưa triển khai

Workflow version → scheduler/event evaluator → per-device eligibility → durable run/action jobs → hàng đợi theo trại/agent → agent thực hiện → ACK/result → Activity.

Cấu hình workflow và thao tác tay cùng dùng action registry + command dispatcher. Mỗi action khai báo schema tham số, capability, quyền cần thiết, thời hạn lệnh, điều kiện online và cách xử lý retry. Không gửi trực tiếp lệnh máy từ trình duyệt hoặc từ hình vẽ node.

- Lưu trạng thái hold/cooldown theo workflow version và device ID, không theo IP. Dữ liệu stale/unknown không xem như nhiệt độ hoặc hashrate bằng 0.
- Kiểm tra quyền organization/site tại lúc tạo và lúc thực thi; Monitoring Only/service/lock/capability phải được kiểm tra ở server và agent. Thu hồi quyền hoặc tạm dừng workflow phải chặn job chưa bắt đầu.
- Giới hạn tốc độ và số máy trong lô; giữ tuần tự các action xung đột trên cùng máy; không reboot cả trại cùng lúc. Ngăn các workflow lặp đối nghịch pause/resume.
- Lệnh có ID duy nhất, deadline và ACK. Retry phải theo action: không tự gửi lại reboot khi không biết lần trước đã chạy chưa; đánh dấu kết quả chưa xác định và đối chiếu trạng thái.
- Mỗi run có phiên bản cấu hình, nguồn trigger và phạm vi snapshot; mỗi máy/action có pending/running/succeeded/failed/skipped/unknown/cancelled. Tổng hợp phải giữ rõ số máy lỗi, không chỉ báo một màu thành công chung.
- Webhook là adapter outbound riêng có HMAC/SSRF protection và retry như mục 9 kế hoạch; không phải đường gửi lệnh máy. Bí mật mã hóa, không vào JSON workflow hoặc log.

### Ví dụ

Nhiệt chip ≥85°C liên tục 3 phút → máy trong Rack A01 thuộc trại Bình Thuận, còn online và cho phép điều khiển → Thermal control (cấu hình phù hợp firmware) → Webhook báo kết quả. Cooldown 30 phút/máy; máy không hỗ trợ được ghi skipped. Các con số chỉ là ví dụ cấu hình, chưa áp dụng lên máy thật.

## 5. Thứ tự cập nhật bản duyệt

1. Agent riêng: danh sách/chi tiết/trạng thái; form tạo agent; scan task và dải IP; giao diện cấp/thu hồi mã chưa nối backend.
2. Miners: bộ lọc, cột, chọn hàng loạt, chi tiết máy và trạng thái hỗ trợ action.
3. Workflow thay bản chỉ webhook: builder theo action, lịch/condition/scope, mô phỏng và xem trước.
4. Activity chung: run → action → máy; chỉ rõ mock, không tạo cảm giác đang điều khiển thật.
5. Preset pool và tham số trại; firmware suites ở giai đoạn sau.
6. Backend account/ownership bảo mật trước, rồi queue/dispatch và nối agent thật sau như phạm vi ban đầu.

Đây là bản tham khảo và đặc tả cập nhật; chưa thay giao diện workflow hiện tại sang builder hay triển khai thêm core/agent trong lần khảo sát này.


## Cập nhật bản duyệt: Agent, Workflow action và Tác vụ — 11/11/2026

Đã triển khai trong `cloud-preview/operations.js` và `operations.css`:

- Agent theo trại, chế độ giám sát/điều khiển, thêm/sửa cấu hình và dải IPv4 cho tác vụ quét. Mặc định agent mới chỉ giám sát. Chưa cấp mã kết nối thật.
- Workflow dạng chuỗi: kích hoạt → phạm vi trại/rack/model → nhiều action có thể thêm, bỏ, đổi thứ tự. Kích hoạt theo điều kiện, lịch hoặc phát hiện máy mới.
- Action: khởi động máy, khởi động trình đào, dừng/tiếp tục đào, đổi pool, làm mát, bật/tắt board, gửi API/Webhook HTTPS.
- Lưu bản nháp, mô phỏng chỉ số/thời gian giữ/cooldown; chi tiết từng máy và từng action tại Tác vụ. Action đầu chờ Agent thì các action sau chờ bước trước; không tạo kết quả thành công giả.
- Dropdown dùng component chung. Đã duyệt trên Chrome ở 1366×768 và 390×844; không tràn ngang tại các màn Agent và builder đã kiểm tra. Sidebar có vùng cuộn để tới các mục quản lý.
- Đã thử tạo/sửa Agent và dải IP; lưu workflow, đổi action/thứ tự, mô phỏng điều kiện đạt và chưa đủ thời gian. Đã sửa lỗi mất ngày mặc định khi đổi sang lịch tuần. Tài khoản mới có 0 Agent và 0 Workflow mẫu.

Giới hạn: toàn bộ cấu hình nằm trong bộ nhớ trang; tải lại sẽ khôi phục fixture. Chưa có xác thực, phân quyền server, cách ly tenant thực tế, hàng đợi, lịch thực thi, gửi webhook hoặc lệnh xuống máy. Đây là bản duyệt giao diện trước backend; không dùng để vận hành trại thật.

Bước tiếp theo sau duyệt: triển khai tài khoản/tenant và quyền theo trại ở server; lưu cấu hình; nhật ký thay đổi; giao thức Agent với mã riêng từng trại, thu hồi/luân chuyển mã; hàng đợi lệnh có thời hạn và xác nhận kết quả; webhook có chữ ký và chặn đích nội bộ/SSRF. Agent thực thi triển khai ở giai đoạn sau.
