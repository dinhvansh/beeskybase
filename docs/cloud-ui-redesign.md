# BeeSky Cloud — Báo cáo redesign

Ngày kiểm tra: 11/11/2026. Phạm vi: web cloud; công cụ quét cục bộ, desktop và Flutter được loại khỏi phạm vi theo yêu cầu trước.

## 1. Kiểm kê và kiến trúc thực tế

Có hai bề mặt khác nhau, chưa được ghép thành một sản phẩm nhiều tài khoản:

- `cloud-preview/`: HTML/CSS/JavaScript, hash routing, trạng thái trong bộ nhớ. React 19 + `@xyflow/react` 12 chỉ dùng cho canvas Workflow; esbuild đóng gói cục bộ. Không gọi API, không tạo tài khoản hoặc gửi lệnh thật.
- `beesky/cloud/dashboard.html`: dashboard thật, HTML có script nhúng, tải dữ liệu bằng API. `beesky/cloud/server.py` phục vụ bằng Python ThreadingHTTPServer. `beesky/cloud/store.py` lưu SQLite. Giữ dạng một file để tương thích bản đóng gói frozen.
- Biểu đồ SVG tự vẽ; không thêm thư viện chart hoặc UI framework lớn. State và routing hiện hữu được giữ lại.

### Route bản duyệt — đã kiểm kê 19/19

| Route | Màn hình / luồng | Nguồn |
|---|---|---|
| `#/overview` | Tổng quan | `cloud-preview/app.js` |
| `#/farms` | Danh sách trại / thêm trại | `cloud-preview/app.js` |
| `#/miners` | Bảng máy / chi tiết / xuất CSV | `cloud-preview/app.js` |
| `#/agents` | Agent / cấu hình / dải IP / thông tin kết nối | `cloud-preview/operations.js; flow-bridge.js` |
| `#/heatmap` | Farm → rack → tầng → slot / gán máy / gợi ý IP | `cloud-preview/racks.js` |
| `#/energy` | Điện năng / báo cáo | `cloud-preview/app.js` |
| `#/repairs` | Phiếu sửa / thêm phiếu mẫu | `cloud-preview/app.js` |
| `#/events` | Sự kiện | `cloud-preview/app.js` |
| `#/workflows` | Danh sách / React Flow / inspector / mô phỏng | `cloud-preview/operations.js; flow-bridge.js` |
| `#/activity` | Tác vụ / kết quả từng bước | `cloud-preview/operations.js; flow-bridge.js` |
| `#/members` | Thành viên / mời / vai trò / thu hồi | `cloud-preview/app.js` |
| `#/security` | Tài khoản / phiên / đổi mật khẩu / MFA mẫu | `cloud-preview/app.js` |
| `#/settings` | Tổ chức / múi giờ / giá điện | `cloud-preview/app.js` |
| `#/ai-reports` | AI & MCP / danh mục báo cáo | `cloud-preview/flow-bridge.js` |
| `#/login` | Đăng nhập mẫu | `cloud-preview/app.js` |
| `#/signup` | Đăng ký mẫu | `cloud-preview/app.js` |
| `#/verify` | Xác thực email mẫu | `cloud-preview/app.js` |
| `#/forgot` | Khôi phục mật khẩu mẫu | `cloud-preview/app.js` |
| `#/onboarding` | Tạo tổ chức / trại đầu tiên mẫu | `cloud-preview/app.js` |

### Dashboard thật — 7/7 mục và trang đăng nhập

Trang chính tại `/`, với hash `#/overview`, `#/miners`, `#/heatmap`, `#/energy`, `#/repairs`, `#/events`, `#/settings`. Agent và pool nằm trong Cài đặt; commands nằm dưới bảng máy. `/login` là trang mật khẩu quản trị; `/logout` kết thúc phiên rồi chuyển trang. Không có route HTTP `/dashboard`.

Các form thật: `agent-form`, `pool-config-form`, `price-form`, `repair-form`. Các ID thực tế đầy đủ và endpoint được lưu trong `route-inventory.json`. Chi tiết miner mới dùng dữ liệu trả về từ `/api/miners`, không tạo số liệu.

### Dữ liệu và hợp đồng giữ nguyên

API: sites, miners, events, commands, repairs, pool-config, pool, energy, settings, history, agents và revoke. GET vẫn đọc, POST vẫn ghi theo logic cũ. Adapter ComboBox giữ nguyên select ẩn, name, form values và sự kiện input/change. Trình điều khiển bảng giữ nguyên row và event handler; không thay API lọc theo trại.

Database vẫn có agents, snapshots, events, commands, repairs, pool_configs/pool_samples, energy_hours, settings và history_samples. Không migration schema trong redesign. MCP `/mcp` giữ quyền chỉ đọc và giới hạn trại hiện hữu.

## 2. Audit trước khi sửa

| Vấn đề | Thay đổi |
|---|---|
| Nền olive, màu hardcode rải rác, glass/blur ở cloud thật | Semantic tokens trung tính; bỏ hiệu ứng kính trên các surface chính |
| Eyebrow, khẩu hiệu, banner duyệt chiếm không gian | Header chỉ giữ tên và thao tác; thông tin bản mẫu chuyển vào workspace/menu, mobile có nhãn nhỏ |
| Sidebar rộng và thiếu chế độ thu gọn | Sidebar 208/224px, chế độ icon 64px, menu phủ trên mobile |
| Bảng khó tìm và không sắp xếp/phân trang | Tìm, sort, 25 dòng/trang, bật/tắt cột; giữ trang đã chọn khi API poll |
| Select native trên dashboard thật | Dùng lại ComboBox chung, có bàn phím, Esc, trạng thái disabled và tìm lựa chọn |
| Không có chi tiết máy thật | Dialog dùng record API, chia hiệu suất/nhiệt, phần cứng/mạng, dẫn tới lịch sử |
| Canvas màu riêng, node ít khác biệt | Đồng bộ theme, icon trigger/filter/action, inspector, nút sắp xếp lại |
| Chuyển trang có thể bỏ bản chỉnh sửa | Hộp thoại khi rời Workflow; cảnh báo đóng/reload tab khi đang chỉnh |
| Poll lỗi giữ dữ liệu cũ nhưng không giải thích | Banner lỗi và Thử lại; giữ snapshot cũ |
| Auth chưa có theme dễ truy cập | Nút theme trên auth/onboarding, trang quản trị theo cùng palette |

## 3. Design system và component specifications

### Tokens

Nguồn chuẩn: `cloud-preview/design-tokens.css`. Light: nền `#F6F7F9`, surface trắng, chữ `#18202E`, phụ `#5E697A`, border `#DCE1E8`. Dark: nền `#101113`, surface `#191B1F`, chữ `#F1F3F5`, phụ `#A4ABB8`, border `#30343B`. Vàng `#FACC15` dành cho logo/primary action; xanh dương dành cho biểu đồ, liên kết và focus. Trạng thái vận hành dùng green/amber/red riêng.

Font Inter variable được lưu cục bộ kèm license trong `cloud-preview/assets/fonts/`; không cần Google Fonts khi chạy. IP/code dùng Cascadia Code/Consolas. Số dùng tabular numerals. Khoảng cách theo 4px; radius 6px control, 8px panel, 12px dialog. Body 13px trên desktop; input mobile 16px.

### Các component dùng lại

| Component | Hành vi / trạng thái | Nguồn |
|---|---|---|
| App shell / page header | Breadcrumb, active route, menu thu gọn, mobile overlay | `app.js`, `enterprise.js`, `enterprise.css` |
| Command search / user menu | Ctrl/Cmd K, tìm trang/IP/model, kết quả bàn phím, đóng bằng Esc | `enterprise.js` |
| Theme switcher | Theo máy trước khi chọn; lưu lựa chọn; đồng bộ tab | `theme.js`, `design-tokens.css` |
| Button / input / form field | Hover, focus rõ, disabled; native validation giữ nguyên | `enterprise.css` |
| KPI / status / alert | Unit, label, màu semantic; thiếu dữ liệu giữ dấu trống/thông báo | `app.js`, template cloud |
| Data table | Search, sort/aria-sort, pagination, columns; giữ row handlers | `table-controls.js` |
| ComboBox | Trigger/listbox, keyboard, disabled, tìm >5 lựa chọn, phục hồi focus | `components.js`, `components.css` |
| Dialog / detail | Native dialog focus trap/Esc, tiêu đề, nút đóng, max-height và scroll | `app.js`, `dashboard.html` |
| Chart container / tabs | SVG responsive, phân biệt hashrate và kWh; mẫu được ghi rõ | `app.js`, dashboard thật |
| Rack / legend | Nhãn farm/rack/tầng/slot; ngưỡng nhiệt và trạng thái chữ | `racks.js`, `racks.css`, `enterprise.css` |
| Workflow node / inspector | Icon + loại + nhãn + số bước, lựa chọn, pan/zoom, auto-layout | `flow-editor/editor.jsx`, `flow-bridge.js` |
| Empty / loading / error / toast | Giải thích khi chưa có agent/dữ liệu; retry API; toast/role=status | CSS chung, template và logic cũ |

Chưa thêm các thao tác không có API như batch reboot, acknowledgement sự kiện, retry/cancel job, publish Workflow thật. Không tạo nút giả để làm đầy giao diện.

### Responsive

≥1440px: sidebar 224px, khoảng nội dung 32px. 1024–1439px: sidebar 192–208px, khoảng nội dung 16–24px. 768–1023px: sidebar icon. <768px: menu phủ; KPI 2 cột; thẻ 1 cột; bảng cuộn trong vùng riêng; rack cuộn trong vùng riêng; canvas ở trên inspector thay vì ép hai cột. Đã đo overview tại 390, 768, 1024, 1366, 1440px, không tràn ngang toàn trang. Có thêm kiểm tra mobile các trang nghiệp vụ và Workflow builder; xem JSON bằng chứng.

## 4. Kết quả xác minh

- Build React Flow/esbuild: PASS. Không có TypeScript trong stack hiện tại; kiểm tra cú pháp toàn bộ JS thêm/sửa và script nhúng: PASS.
- `mock_agents_ui_test.py`: PASS (30 kiểm tra, bao gồm auth, tạo/thu hồi key, ingest và template markers).
- `test_mcp_reporting.py`: PASS, 5 tests, bao gồm SDK MCP chính thức và chặn truy cập chéo trại.
- `mock_energy_pool_test.py`: PASS (sau khi bật Python UTF-8 cho subprocess trên Windows).
- `mock_actions_test.py`, `mock_repairs_test.py`, `mock_history_test.py`: PASS. Log của 3 bộ này đi kèm.
- Kiểm tra trình duyệt: 19/19 route sáng, 19/19 route tối mở được, không thấy tràn ngang ở viewport laptop thực tế; JSON route-checks lưu số đo.
- Thao tác UI đã xác minh: tìm S21 còn 2 dòng; sort nhiệt tăng dần bắt đầu 65°C; chọn Đắk Lắk còn 2 máy; mở miner detail; bảng API fixture 30 máy chuyển trang 2/2; chi tiết thật hiện giá trị API và “Chưa báo cáo” khi thiếu.
- Workflow: sửa tên và ngưỡng 85→86, lưu rồi đọc lại đúng. Canvas/inspector mobile đo scrollWidth=clientWidth=375px bên trong frame 390px.
- Kiểm thử không gửi lệnh tới máy đào thật. Fixture API nằm trong SQLite in-memory riêng và ghi rõ “Kiểm thử UI · Dữ liệu mô phỏng”. Bản cloud cho người dùng duyệt ở 8791 dùng database trống riêng.
- Không có lỗi JavaScript ứng dụng trong lần kiểm tra log; có cảnh báo từ extension Chrome bên ngoài ứng dụng. Chưa chạy audit WCAG tự động hoặc benchmark hàng nghìn máy, không coi đây là chứng nhận accessibility/performance.

## 5. Cách chạy / cập nhật

Trong repo:

```powershell
npm ci --prefix cloud-preview/flow-editor
npm run build --prefix cloud-preview/flow-editor
python tools/build_cloud_ui.py
python -m http.server 8790 --bind 127.0.0.1 --directory cloud-preview
```

Bản duyệt: `http://127.0.0.1:8790/#/overview`. Dashboard thật trong phiên review: `http://127.0.0.1:8791/` (database thử riêng, không có trại). Quy trình chạy cloud chính thức vẫn theo README, đặt mật khẩu cloud và HTTPS khi triển khai. Không sửa Docker/API/storage trong redesign.

`tools/build_cloud_ui.py` nhúng tokens, font, ComboBox và table controls vào các block có marker trong template thật; vì vậy không cần phục vụ thêm asset khi đóng gói. Chạy script này sau khi sửa component chung. Build React Flow đồng thời cập nhật hash cache của tất cả asset trong index preview.

## 6. Giới hạn còn lại — cần phân biệt rõ

1. Đăng ký, email, MFA, thành viên và phân quyền nhiều tổ chức ở bản duyệt vẫn là mô phỏng; tài khoản quản trị cloud thật vẫn dùng cơ chế hiện hữu. Chưa đủ điều kiện mở đăng ký SaaS công khai.
2. Workflow React Flow, bố trí rack và Agent setup ở bản duyệt chưa nối persistence/runtime thật. Không tự thêm branching hoặc action mới.
3. Chưa có trend công suất, expected hashrate, efficiency, firmware, serial, uptime đồng nhất cho mọi nguồn. Chi tiết thật chỉ hiển thị giá trị khi API có dữ liệu; không suy diễn metrics thiếu.
4. Bảng dùng phân trang phía client; chưa virtualize hàng nghìn row hoặc thêm server pagination vì API hiện tại chưa hỗ trợ hợp đồng đó.
5. Source cũ còn CSS nền cho những giao diện/biến thể legacy; enterprise layer và tokens là lớp trình bày đang áp dụng. Chưa viết lại toàn bộ frontend hoặc hợp nhất preview với dashboard thật.
6. Chưa thêm saved views, thông báo push, workflow publishing hoặc audit trail mới vì đây là thay đổi nghiệp vụ/backend ngoài phạm vi giữ nguyên hợp đồng.
7. Ảnh before được chụp từ bản sao source giao diện trước redesign trong phiên này. Ảnh API có fixture được ghi tên riêng, không phải số liệu trại của người dùng.

## 7. Bằng chứng

- `route-inventory.json`: danh sách route, form, module, endpoint lấy từ source.
- `route-checks.json`, `dark-route-checks.json`: kiểm tra các route tại viewport trình duyệt thực tế.
- `responsive-checks.json`: các số đo breakpoint đã hoàn tất.
- `production-route-checks.json`: 7/7 mục dashboard thật không tràn ngang. Cài đặt thật trong frame 390px: scrollWidth=375px.
- `GALLERY.html`: ảnh trước/sau và các trang sáng/tối. Ảnh là bằng chứng thị giác, không thay kiểm thử luồng.

Không commit, push hoặc triển khai ra Internet trong phiên này.
