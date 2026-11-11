# BeeSky Cloud — Quy tắc thiết kế

Nguồn: **MASTER PROMPT — BEESKY MINING CLOUD / Full Application UI/UX Redesign — Modern Enterprise SaaS 2026**, do người dùng cung cấp. Các mục A–H dưới đây trích nguyên tắc và rút thành yêu cầu thực hiện; số mục trong ngoặc dẫn về master prompt. Mục I ghi riêng các yêu cầu bổ sung trong cuộc trò chuyện, không coi là trích dẫn từ master prompt.

Áp dụng cho mọi trang, component, trạng thái, dialog và lần sửa giao diện web cloud. Đây là quy tắc thực hiện, không phải xác nhận mọi hạng mục đã hoàn tất.

## A. Định hướng và mật độ (§2–3, §13)

> “Ưu tiên clarity hơn decoration.”
>
> “Compact nhưng không chật chội.”
>
> “Ưu tiên một giao diện rõ ràng, hiện đại, đồng bộ, hiệu năng tốt và dễ bảo trì hơn những hiệu ứng mang tính trình diễn.”

- Tối giản, chuyên nghiệp; ưu tiên giám sát, phát hiện lỗi, thao tác nhanh.
- Học nguyên tắc Linear / Vercel / Stripe / n8n; không sao chép nguyên mẫu.
- Tránh card quá lớn, khoảng trắng thừa, bo góc quá tròn, shadow dày, floating component không cần thiết.
- Không lạm dụng glass, blur, gradient, màu nhấn hoặc animation.
- Chọn bảng, danh sách, timeline, sơ đồ theo nghiệp vụ; không ép mọi trang thành cùng một kiểu card.

## B. Màu sắc, chữ và hình học (§4)

- Giữ logo và nhận diện BeeSky. Vàng dành cho thương hiệu và hành động chính.
- Healthy / Warning / Critical / Offline dùng màu ngữ nghĩa riêng; không dùng vàng cho mọi trạng thái.
- Light/Dark cùng hệ token ngữ nghĩa. Không hardcode màu theo từng component.
- Font Geist hoặc Inter; phân cấp rõ, weight 400/500/600/700.
- Số dùng tabular numbers; IP, định danh, log dùng monospace phù hợp.
- Spacing theo bội số 4px; radius 6/8/12px nhất quán theo loại component.
- Button/input có kích thước thống nhất. Focus rõ, nội dung quan trọng đạt tương phản WCAG AA.

Các màu light đề xuất trong master prompt:

| Vai trò | Màu đề xuất |
|---|---|
| Brand / hover | #FACC15 / #EAB308 |
| Text / secondary | #111827 / #64748B |
| Background / surface / border | #F8FAFC / #FFFFFF / #E2E8F0 |
| Success / warning / danger / info | #16A34A / #F59E0B / #DC2626 / #2563EB |

Đây là bảng đề xuất từ nguồn, cần kiểm tra tương phản và nhận diện trước khi áp dụng; không thay token hiện tại một cách máy móc.

## C. Component dùng chung (§7)

> “Ưu tiên tái sử dụng, tránh trùng lặp component.”

- Dùng chung Page Header, KPI, Status, Table, Filter Bar, **Search Input**, Drawer, Tabs, Dialog, Form Field, Date Range, Chart, Log, Timeline, Empty State, Alert, Notification, Breadcrumb và Action Menu.
- Có default, hover, focus, disabled, loading, error khi phù hợp.
- Một loại thao tác phải có cùng kiểu hiển thị và phản hồi trên các trang.
- Không thêm một input trần ngoài hệ component rồi coi là đã hoàn thiện.

## D. Điều hướng và phản hồi (§5)

- Sidebar thu gọn được; nhóm theo nghiệp vụ, icon đồng bộ, active state rõ.
- Topbar có breadcrumb, ngữ cảnh, tìm kiếm, thông báo, tài khoản, theme và hành động theo trang.
- Có loading, empty có hướng dẫn, error + retry, toast, xác nhận thao tác nguy hiểm và cảnh báo thay đổi chưa lưu.
- Có điều hướng bàn phím, responsive navigation; command palette khi phù hợp.
- Production bỏ thông báo demo/developer thừa; bản mẫu vẫn phải nhận biết được dữ liệu mẫu.

## E. Xưởng, rack, máy và nhiệt (§6B–E)

- Luồng đi sâu: **Farm → Rack → Miner**.
- Có tìm kiếm và bộ lọc; ưu tiên tìm và xử lý máy lỗi nhanh.
- Máy cần có IP, farm, rack, model, serial và các chỉ số được backend hỗ trợ.
- Chi tiết máy nhóm Hardware, Performance, Temperature, Network, Events, Maintenance, Actions.
- Heatmap có legend, ngưỡng, hotspot và thao tác mở máy liên quan.
- Không giả định backend có chỉ số chưa được cung cấp; hiển thị thiếu dữ liệu đúng nghĩa.
- Agent không được coi đang kết nối nếu heartbeat quá hạn theo backend.

## F. Dữ liệu và hợp đồng hệ thống (§6, §9)

- Giữ API contracts, authentication, authorization, business logic, persistence, workflow runtime, integrations và hành vi hiện hữu.
- Không mở rộng quyền qua thay đổi giao diện.
- Không hardcode dữ liệu giả trong component production; không thay metric thật bằng fake metric.
- Phân biệt kW (công suất) và kWh (điện năng); KPI cần đơn vị, thời điểm và trạng thái dữ liệu.
- Workflow giữ runtime: không tự thêm nhánh/action chưa hỗ trợ. Node phân biệt bằng icon, nhãn và nội dung, không chỉ bằng màu.
- Tận dụng stack hiện có; không tự migrate framework hoặc thêm thư viện lớn thiếu lý do.

## G. Responsive và khả năng truy cập (§4–5, §8)

| Kích thước | Yêu cầu |
|---|---|
| ≥1440px | Giám sát, dữ liệu nhiều |
| 1024–1439px | Laptop, gọn và thao tác nhanh |
| 768–1023px | Tablet, bố cục thích ứng |
| <768px | Ưu tiên trạng thái, cảnh báo, chi tiết máy và thao tác quan trọng |

- Không ép canvas workflow hay bảng phức tạp giữ nguyên bố cục desktop trên mobile.
- Không có tràn ngang ngoài ý muốn; bảng/sơ đồ rộng chỉ cuộn trong vùng của chúng.
- Nhãn, focus, tương phản, thao tác bàn phím phải được kiểm tra thực tế.

## H. Điều kiện trước khi báo hoàn tất (§10–12)

- Kiểm kê route và component liên quan; không bỏ màn phụ/dialog.
- Kiểm tra navigation/breadcrumb, form, filter, sort, pagination và API hiện hữu.
- Kiểm tra build, runtime/console, light/dark, responsive, accessibility và chức năng nghiệp vụ quan trọng.
- Lưu ảnh trước/sau; ghi kết quả test và giới hạn còn lại.
- Không nói “đã kiểm thử” cho thao tác mới chỉ viết code.

## I. Yêu cầu bổ sung đã chốt với người dùng

- Tập trung web cloud; tool quét và agent native làm sau.
- Tối ưu laptop 13–14 inch. Bỏ slogan/eyebrow/giới thiệu thừa chiếm chỗ.
- Dropdown/ComboBox dùng component tùy chỉnh đồng bộ, không dùng hình thức mặc định trình duyệt.
- Rack và nhiệt nằm trong **Xưởng của tôi**; không tách một mục heatmap độc lập.
- Bấm xưởng mở sơ đồ. Bấm “N cần kiểm tra” mở đúng xưởng, đúng danh sách lỗi, có IP và vị trí.
- Máy chưa xếp có search/filter và kéo thả vào ô trống; có cách bấm chọn vị trí thay thế.
- Rack đổi tên và khu/dãy được; không làm mất máy đã gắn.
- Tìm máy đã xếp theo IP/model/serial/tên rack; kết quả phải dẫn đến đúng rack/tầng/ô.
- Hiệu ứng 3D phải nhẹ, không giảm khả năng đọc nhiệt độ/IP hoặc che thao tác.

### Chuẩn Search Input áp dụng trong lần sửa này

- Hai phạm vi rõ: **Tìm máy trong rack** và **Tìm máy chưa xếp**. Không để người dùng hiểu nhầm phạm vi.
- Cùng một component: icon tìm bên trái, input, nút xóa có tên truy cập; một đường viền và một focus ring cho cả ô.
- Tắt dấu xóa/trang trí search mặc định của trình duyệt để tránh lồng hai bộ giao diện.
- Desktop cao 36px; mobile 40px, chữ nhập 16px. Radius 6px; dùng token màu hiện có.
- Từ khóa cập nhật kết quả không làm mất focus. Có số kết quả và trạng thái không tìm thấy.
- Tìm trong rack giữ sơ đồ vật lý, làm nổi ô khớp; bấm kết quả mở rack tương ứng và đưa focus tới vị trí máy.
- Search/filter không thay đổi dữ liệu, không chuyển máy, không tự gửi lệnh tới miner.

### Checklist cho mọi lần sửa tiếp theo

- [ ] Đọc file này và đối chiếu component đang có.
- [ ] Đúng vị trí chức năng, đúng ngữ cảnh xưởng.
- [ ] Dùng component/token chung; default/hover/focus/empty nhất quán.
- [ ] Không thêm tiêu đề hoặc hướng dẫn thừa.
- [ ] Thử bàn phím, sáng/tối và laptop 1366×768; kiểm tra mobile nếu bị ảnh hưởng.
- [ ] Thử thao tác chính, trường hợp không có kết quả và xóa lọc.
- [ ] Lưu ảnh thực tế; báo chính xác phần đã kiểm thử và giới hạn.

### Thuật ngữ giao diện

- Dùng **Xưởng** cho địa điểm vận hành trong menu, tiêu đề, biểu mẫu, dữ liệu mẫu và thông báo. Không dùng tên gọi cũ.
