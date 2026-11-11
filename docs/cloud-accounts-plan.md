# Kế hoạch BeeSky Cloud — tài khoản riêng và quản lý nhiều trại

Ngày: 11/11/2026. Nguồn: dinhvansh/beeskybase, commit dcebb90 (v0.23.0).

## 1. Mục tiêu và điểm duyệt

Người dùng tự đăng ký, xác thực email, tạo tổ chức và trại. Mỗi tổ chức chỉ truy cập dữ liệu của mình. Chủ sở hữu có thể mời người khác với quyền phù hợp. Web cloud là phạm vi chính; công cụ quét, desktop và sửa agent để giai đoạn sau.

**Điểm dừng hiện tại:** hoàn thành kế hoạch và giao diện local dùng dữ liệu mẫu để chủ dự án duyệt. Chưa mở đăng ký thật, chưa gửi email, chưa thay backend production hoặc triển khai công khai. Sau khi duyệt giao diện mới triển khai các giai đoạn backend bên dưới.

## 2. Bản duyệt giao diện

- Bộ nhận diện BeeSky: logo chính thức trong repository, vàng #F5D800, bề mặt tối, trạng thái xanh/cam dùng đúng ngữ nghĩa.
- Desktop ưu tiên bảng và thông tin vận hành; mobile chuyển sidebar thành menu, bảng cuộn trong vùng riêng.
- Đăng nhập, đăng ký, xác thực email mô phỏng, quên mật khẩu.
- Tài khoản mới: tổ chức → trại đầu tiên → màn hình chờ dữ liệu.
- Tổng quan: chỉ trại của tổ chức; thống kê, biểu đồ theo thời gian, bất thường, danh sách trại.
- Máy đào: tìm IP/model, lọc trại/trạng thái, chi tiết máy, xuất CSV dữ liệu mẫu.
- Trại: thêm trại và xem bố cục tạo khóa kết nối.
- Thành viên: lời mời mẫu, thay vai trò, thu hồi quyền mẫu.
- Bảo mật: mật khẩu, phiên đăng nhập, bố cục MFA; các hành động được đánh dấu là mô phỏng.
- Các màn hình duy trì từ sản phẩm cũ: nhiệt độ, điện năng ước tính, lịch sử sửa, sự kiện.
- Mật khẩu nhập vào bản duyệt không được ghi file, localStorage hoặc gửi qua mạng. Dữ liệu mẫu chỉ sống trong bộ nhớ trang và mất khi tải lại.

Chủ dự án duyệt: phong cách/màu sắc; độ dày thông tin; thứ tự menu; luồng đăng ký; các trường tạo trại; quyền thành viên; mobile. Các thay đổi yêu cầu được cập nhật ngay trên cùng bản local.

## 3. Các quyết định kiến trúc đề xuất

Đây là phương án triển khai để duyệt, chưa thay đổi stack cloud hiện tại.

### Backend cloud

- Django bản LTS còn được hỗ trợ + Django REST Framework, PostgreSQL và migration có phiên bản. Dùng cơ chế auth/session/password/reset đã được kiểm chứng; Argon2id cho mật khẩu bằng thư viện được duy trì.
- Tách dịch vụ cloud khỏi gói scanner. Giữ hợp đồng ingest tại cổng tương thích để giai đoạn đầu không buộc sửa tool/agent.
- Frontend ban đầu có thể dùng Django template + module JavaScript tách file, giữ ít bước build. Bản duyệt HTML/CSS/JS là cơ sở giao diện; không tái sử dụng state mẫu làm auth.
- Dùng cookie phiên do server cấp. Không đưa access token vào localStorage. Ưu tiên web/API cùng domain, CSRF token cho thao tác ghi, kiểm tra Origin theo cấu hình.
- PostgreSQL là nguồn dữ liệu thật. Không dùng file JSON làm nơi lưu tài khoản hay quyền.
- Chưa cần microservices hoặc Redis ở bản đầu; tác vụ gửi mail/poll pool tách thành worker có retry, dùng hàng đợi theo database hoặc bổ sung broker khi có nhu cầu đo được.

### Mô hình quyền

User → Membership → Organization → Site → Agent / dữ liệu vận hành.

- Người đăng ký và xác thực email trở thành owner của một organization riêng.
- Owner: quản lý tổ chức, thành viên, trại, cấu hình và vận hành.
- Admin: vận hành trại, cấu hình, ghi phiếu sửa; không đổi chủ sở hữu hoặc nâng quyền bản thân.
- Viewer: chỉ đọc; mọi API ghi từ chối kể cả khi tự gọi trực tiếp.
- Các vai trò áp dụng toàn bộ trại trong một organization ở phiên bản đầu. Quyền riêng từng trại có thể thêm sau bằng site_memberships.
- UUID công khai giảm khả năng dò ID; không thay thế kiểm tra quyền.
- Mỗi endpoint bắt buộc lấy organization từ membership hợp lệ, lọc truy vấn trước khi đọc/ghi. Không tin organization_id/site_id do client gửi.
- Hệ thống quản trị nội bộ tách khỏi UI khách hàng; không tạo một tài khoản dùng chung có quyền vào tất cả trại.

### Bảng và ràng buộc

1. users: id, email chuẩn hóa unique, password hash, verified_at, status.
2. organizations: id, name, created_by, created_at.
3. memberships: user_id + organization_id unique; role/status; không cho xóa owner cuối cùng.
4. sites: id, organization_id, name, location, timezone, settings; tên unique trong tổ chức.
5. agents: id, site_id, key hash/prefix, revoked_at, last_heartbeat_at, last_snapshot_at; hỗ trợ xoay khóa.
6. snapshots/events/commands/repairs/pool_configs/pool_samples/energy/history: site_id bắt buộc, organization_id nếu cần để ràng buộc và truy vấn nhất quán.
7. sessions và email verification/reset/invitation tokens: hạn dùng, một lần, token ngẫu nhiên; chỉ lưu hash của token xác thực qua email.
8. audit_logs: actor_user_id hoặc agent_id, organization/site, action, target, result, request_id, timestamp; không chứa bí mật.

Giá điện hiện là setting chung toàn cloud phải chuyển thành setting của organization, có thể override theo site. Tên trại chỉ dùng hiển thị; loại bỏ quan hệ bằng chuỗi site. Lịch sử máy dùng định danh nội bộ thay vì chỉ IP; bước đầu vẫn nhận IP để tương thích nhưng không khẳng định IP là danh tính vĩnh viễn.

## 4. Giai đoạn triển khai và tiêu chí hoàn tất

### GĐ0 — Duyệt giao diện (hiện tại)

Sản phẩm: bản local, kế hoạch này, ảnh chụp desktop và kiểm tra bố cục/menu mobile, nhánh feat/cloud-accounts-preview. Không push hoặc deploy trong bước duyệt.

Hoàn tất khi các luồng mẫu đi được, không lỗi JavaScript quan trọng, bố cục desktop/mobile đọc được và người dùng duyệt hướng giao diện.

### GĐ1 — Nền tảng dữ liệu và cách ly tổ chức

- Tạo dịch vụ cloud mới, database PostgreSQL, migrations, môi trường local bằng Docker Compose.
- Tạo organizations/sites/memberships và lớp truy vấn bắt buộc phạm vi organization.
- Viết migration đọc SQLite: gán dữ liệu cũ cho organization legacy; lập báo cáo trùng tên trại và ánh xạ agent_id → site_id. Trùng tên không được tự hợp nhất gây mất dữ liệu.
- Sao lưu nguồn; chạy dry run; đối chiếu số lượng bản ghi, tổng dữ liệu quan trọng. Migration có thể chạy lại an toàn, không ghi đè dữ liệu đã nhập.
- Khóa ngoại/composite constraint bảo đảm dữ liệu không trỏ tới site của organization khác.

Gate: tài khoản A không đọc hoặc sửa trại B qua API hay truy vấn bỏ bộ lọc. Viewer bị từ chối mọi thao tác ghi. Dữ liệu legacy thuộc đúng owner được chỉ định.

### GĐ2 — Tài khoản và đăng ký

- Đăng ký email + mật khẩu, xác thực email, đăng nhập/đăng xuất, đặt lại mật khẩu, thu hồi phiên.
- Không tự động đăng nhập chỉ nhờ chưa xác thực email. Token email dùng một lần và có hạn. Đổi mật khẩu/reset phải vô hiệu các phiên theo chính sách.
- Phản hồi quên mật khẩu không tiết lộ email có tồn tại. Xác thực đường dẫn chuyển tiếp để không open redirect.
- Giới hạn tần suất theo IP và tài khoản cho đăng ký/login/resend/reset; không khóa vĩnh viễn tài khoản khi bị kẻ khác spam.
- SMTP thử bằng Mailpit ở local; chọn nhà cung cấp gửi email và domain sender trước khi bật Internet.
- MFA cho owner/admin trước khi cho phép lệnh tác động máy trong production; thiết kế recovery codes và quy trình khôi phục.

Gate: hết hạn/dùng lại token bị từ chối; cookie Secure ở production + HttpOnly + SameSite; CSRF và Origin kiểm tra đúng; không có token/mật khẩu trong log, URL không phù hợp hay localStorage.

### GĐ3 — Web quản lý trại và thành viên

- Nối UI đã duyệt với API thật; onboarding tạo organization/site trong transaction.
- Tạo/sửa trại, mời thành viên bằng token ngẫu nhiên, chấp nhận lời mời, đổi vai trò, thu hồi membership.
- Chỉ owner thay đổi quyền; owner cuối cùng được bảo vệ. Thu hồi membership có hiệu lực ngay ở API, không chỉ đổi UI.
- Bảng máy có tìm kiếm, lọc, phân trang; API có giới hạn kết quả, không tải toàn bộ fleet vô hạn.
- Hiển thị last_snapshot_at và trạng thái dữ liệu cũ; phân biệt heartbeat còn sống với snapshot bị ngừng cập nhật.

Gate: tài khoản mới bắt đầu với dữ liệu rỗng của chính mình; hai tổ chức có trại cùng tên hoạt động độc lập; không hiển thị mock data trong bản thật.

### GĐ4 — API vận hành và bảo vệ tích hợp

- Giữ tương thích đường ingest cần thiết; xác định site từ key đã xác thực, không từ tên site trong body. Key scoped từng site, chỉ cấp quyền ingest/nhận lệnh cần thiết.
- Schema validation cho từng record, giới hạn số miners/events, kích thước body, chu kỳ gửi và dung lượng theo organization.
- Deduplication/idempotency cho ingest và tạo lệnh; timestamps lệch quá mức bị xử lý theo chính sách. Giới hạn phạm vi IP máy đích đã được liên kết với trại.
- Lệnh vận hành kiểm tra role, site, target; lưu người yêu cầu; deadline và trạng thái rõ ràng. Lệnh chưa hoàn tất không được tự chạy lại vì mất báo cáo kết quả.
- Pool: phiên bản đầu ưu tiên danh sách provider/domain đã kiểm chứng; kiểm tra scheme HTTPS, chặn loopback/private/link-local/metadata, kiểm tra DNS và mọi redirect, outbound firewall, timeout/kích thước response. Không cho người dùng tự tạo đường gọi vào mạng máy chủ.
- Mã hóa bí mật API pool ở tầng ứng dụng; khóa mã hóa nằm ngoài database. Trả API chỉ có trạng thái đã cấu hình, không trả secret. Log được lọc bí mật.
- Chuẩn hóa đơn vị/thuật toán hashrate, tránh cộng các thuật toán không tương đương. Kiểm chứng lại chuyển đổi MH/s/GH/s/TH/s trước khi dùng cho đối soát pool và báo cáo.
- Audit log cho tạo/sửa/thu hồi trại, membership, khóa, cấu hình pool và lệnh máy.

Gate: các đường đọc/ghi cùng tuân thủ quyền; kiểm thử SSRF cả redirect/DNS; schema sai không gây lỗi 500 hay làm bẩn snapshot; báo cáo không nhầm đơn vị.

### GĐ5 — Triển khai và kiểm tra phát hành

- HTTPS reverse proxy, backend chỉ mở loopback/mạng riêng; fail closed nếu thiếu secret production. Không dùng mật khẩu quản trị chung làm lối vào khách hàng.
- Thêm security headers; CSP phù hợp sau khi tách script/style; không dùng wildcard CORS với credential.
- Container chạy user thường, pin dependency có lockfile; secrets ngoài image/repo; kiểm tra dependency và secret trong CI.
- Health/readiness kiểm tra API + database thật, không chỉ thấy trang login trả 302. Deploy chỉ sau khi toàn bộ CI và migration gate thành công.
- Sao lưu PostgreSQL có mã hóa, thử restore thực tế, thời hạn lưu và quy trình xóa theo organization. Giám sát lỗi, dung lượng, hàng đợi và tác vụ pool.
- SSH host key được pin từ fingerprint đã xác minh; không mặc định tin keyscan mỗi lần triển khai.
- Rollback ứng dụng tương thích migration; migration phá dữ liệu tách thành bước sau và cần bản sao lưu đã xác nhận.

Gate: kiểm thử bên dưới pass, restore thành công, không còn open mode, và chủ dự án duyệt staging trước khi public.

## 5. Ma trận kiểm thử bắt buộc

- A/B: list/detail/create/update/delete/export cho sites/miners/events/repairs/energy/history/pool/agents/commands/settings. Thử đổi ID, tên trại, organization trong URL, query, body và batch. GET không bộ lọc chỉ trả phạm vi A.
- Owner/admin/viewer: API trực tiếp và UI thống nhất; không cho đổi role để tự nâng quyền.
- Tên trại giống nhau giữa organizations, thay tên trại không mất lịch sử; nhiều agent trong một site không nhân đôi sai báo cáo.
- Membership bị thu hồi khi phiên đang mở phải mất quyền ngay. Agent key thu hồi/đổi không truy cập lại được.
- Verification/reset/invite token: sai, hết hạn, dùng lại, dùng cho tài khoản khác đều thất bại.
- CSRF, rate limit, session fixation/revocation, redirect, dữ liệu HTML độc hại, URL pool nội bộ/redirect/DNS.
- Ingest record lỗi, số âm/vô hạn, timestamp lệch, body quá lớn, retry trùng; không làm hỏng tổng hợp.
- Snapshot cũ không được hiển thị như dữ liệu đang cập nhật; biểu đồ/điện năng có múi giờ và ý nghĩa rõ ràng.
- Migration đối chiếu số lượng và dữ liệu trước/sau; backup/restore.
- Desktop 1440px, tablet 768px, mobile 390px; dùng bàn phím và modal có focus/đường thoát.

## 6. File dự kiến thay đổi trong repo

- cloud-preview/: prototype duyệt hiện tại, không được đưa lên production như một hệ thống auth.
- cloud_service/ (đề xuất): backend Django, API, accounts, organizations/sites, migrations và tests.
- cloud frontend templates/static: triển khai giao diện đã duyệt, tách JS/CSS theo chức năng.
- beesky/cloud/: giữ compatibility trong thời gian chuyển; tránh sửa tool/desktop ngoài phạm vi.
- Dockerfile cloud riêng + Compose PostgreSQL/Mailpit/reverse proxy profile; không áp đặt stack cloud mới lên gói scanner.
- .github/workflows/: CI test bảo mật/cách ly, migration check, build và deploy có gate.
- docs/: hướng dẫn local, mô hình quyền, migration, backup/restore, deploy; sửa tài liệu nói repo private đã lỗi thời.

## 7. Đầu vào cần trước khi chạy thật

Không cản bước duyệt UI: các lựa chọn có thể chốt sau khi duyệt. Trước production cần domain cloud, nhà cung cấp email/sender, máy chủ staging/production, tổ chức sở hữu dữ liệu cũ, chính sách lưu dữ liệu và chính sách MFA. Không yêu cầu gửi bí mật vào chat; cấu hình qua biến môi trường/secret manager phù hợp.

## 8. Bổ sung bố trí vật lý và bản đồ nhiệt theo rack

### Bản duyệt hiện tại
- Trại → khu/dãy → tủ/rack → tầng → vị trí máy. Tầng đánh số từ trên xuống, ô từ trái sang phải khi nhìn mặt trước.
- Tạo rack với số tầng và số ô mỗi tầng; lọc theo trại/rack; mỗi ô hiển thị IP, model, nhiệt độ hoặc trạng thái mất kết nối.
- Danh sách máy chưa xếp; gắn vào ô trống, chuyển máy giữa vị trí, bỏ gắn. Một máy chỉ có một vị trí; một vị trí chỉ chứa một máy.
- Gợi ý theo dải IPv4 chỉ lấy máy chưa xếp và ô trống trong cùng trại; xem trước từng máy → tầng/ô rồi xác nhận áp dụng.
- Đã kiểm tra trực tiếp luồng gắn máy, chuyển máy, tạo rack, xem trước/áp dụng dải IP và đổi trại. Đây là dữ liệu mẫu trong bộ nhớ, tải lại trang sẽ khôi phục mẫu; chưa kết nối máy đào thật.

### Mô hình lưu trữ đề xuất cho giai đoạn backend
- zones: organization_id, site_id, tên khu/dãy.
- racks: organization_id, site_id, zone_id, tên, số tầng, số ô, hướng đánh số. Tên rack duy nhất trong một trại.
- rack_slots: rack_id, tầng, cột; duy nhất theo rack/tầng/cột.
- miner_devices: ID ổn định của máy trong organization/site; lưu các danh tính được xác minh (serial/MAC khi thiết bị cung cấp), model và trạng thái đối chiếu.
- placements: device_id, slot_id; ràng buộc duy nhất cho máy và ô đang sử dụng. Dùng transaction và khóa phù hợp khi chuyển máy hoặc áp dụng hàng loạt để tránh hai người chiếm cùng ô.
- placement_history: máy, vị trí cũ/mới, người thực hiện, thời điểm, lý do; lưu dấu vết gắn/chuyển/thay máy.
- scan_observations: dữ liệu quét, IP hiện tại, định danh báo về, telemetry và thời điểm. Tách dữ liệu quan sát khỏi vị trí vật lý.

### Quy tắc kết nối dữ liệu quét sau khi duyệt giao diện
1. Lần đầu không tự biết máy nằm ở rack nào. Máy vào danh sách chưa xếp, người quản lý gắn thủ công hoặc xác nhận gợi ý theo dải IP.
2. Quét lại cập nhật telemetry của cùng thiết bị theo danh tính đã xác minh; đổi IP không làm đổi vị trí. Mất kết nối vẫn giữ ô, hiển thị trạng thái offline và lần thấy cuối.
3. Không coi IP là danh tính chắc chắn. Khi thiếu serial/MAC, trùng định danh hoặc IP được dùng bởi máy thay thế, yêu cầu đối chiếu; không tự gán lịch sử/vị trí cho máy mới.
4. Dải IP là gợi ý có phạm vi từng trại. Không tự chuyển máy đã xếp hoặc ghi đè ô có máy. Hiển thị phần dư nếu rack không đủ chỗ.
5. Chuyển thủ công và thay máy phải có lịch sử. Việc kết nối scanner/agent triển khai sau, giữ phạm vi hiện tại ở web cloud.

### Bảo mật và kiểm thử bổ sung
- Mọi thao tác rack/slot/device/placement phải kiểm tra organization, quyền trại và mối quan hệ cùng trại ở phía server. Không tin site_id/rack_id do trình duyệt gửi.
- Viewer chỉ xem; owner/admin được sửa trong phạm vi được cấp. Không được dùng giao diện ẩn nút để thay cho kiểm tra API.
- Kiểm thử hai tổ chức A/B, hai trại dùng cùng dải IP; thay ID trong API; hai người gắn cùng một ô; gắn trùng một máy; lỗi giữa batch phải rollback.
- Kiểm thử quét lại, IP đổi, máy mất kết nối, máy thay thế cùng IP, trùng/thiếu định danh, gợi ý hết ô và không ghi đè vị trí đã có.
- Đưa migration/schema vào GĐ1; API bố trí và giao diện đã duyệt vào GĐ3; nối observations với ingest vào GĐ4. Chưa triển khai nhận dạng/quét thật ở bản duyệt.

## 9. Workflow sự kiện gửi API / webhook

### Phạm vi bản duyệt
- Mục Workflow: tạo/sửa/bật/tạm dừng quy tắc, chọn trại, sự kiện (nhiệt độ cao/offline/máy mới/hashrate giảm), ngưỡng, khoảng nghỉ và URL HTTPS nhận POST JSON.
- Thử sự kiện mẫu, phân biệt đạt/chưa đạt điều kiện, xem payload có site/device/rack/shelf/slot và lịch sử chạy trong phiên. Không gửi HTTP, không lưu bí mật, chưa thực thi cooldown/retry thật.
- Đã kiểm tra tạo workflow và mô phỏng nhiệt độ 88°C đạt ngưỡng 85°C, 70°C bị bỏ qua. Payload vị trí lấy từ sơ đồ rack hiện tại.

### Thiết kế triển khai backend sau duyệt
- Nguồn sự kiện là thay đổi trạng thái đã xác minh từ ingest, không phụ thuộc trình duyệt đang mở. Dùng transactional outbox để ghi sự kiện cùng dữ liệu; worker nền đọc và tạo delivery theo workflow có quyền trong cùng organization/site.
- Tables: workflows, webhook_endpoints, event_outbox, workflow_runs, webhook_deliveries, delivery_attempts. Ghi phiên bản cấu hình khi chạy; ràng buộc duy nhất event_id/workflow_id; có giới hạn lưu và phân trang theo tenant.
- API đề xuất: /api/workflows (list/create), /api/workflows/{id} (get/update/archive), /api/workflows/{id}/test (mô phỏng mặc định), /api/workflow-runs và /api/deliveries/{id}/retry. Kiểm tra quyền từng request; owner/admin cấu hình; viewer chỉ đọc theo phạm vi. Gửi thử thật là thao tác riêng có xác nhận địa chỉ và dữ liệu sẽ gửi.
- POST application/json với schema_version, event_id, type, occurred_at, site, device, placement, measurement. Chỉ gửi trường cần thiết, không gửi mật khẩu/agent keys. Snapshot vị trí tại thời điểm sự kiện; máy chưa xếp có placement=null.
- Chống lặp theo workflow/device/event; cooldown; hysteresis và phục hồi để tránh rung ngưỡng; offline tính theo last_seen và khoảng trễ cấu hình; không tạo máy mới từ mọi lần quét lại. Hashrate giảm phải có đường cơ sở và cửa sổ thời gian rõ ràng.
- Worker dùng HTTPS, timeout, giới hạn body/response và số kết nối; không theo redirect. Chặn loopback/private/link-local/reserved IPv4/IPv6 và cloud metadata, kiểm tra DNS và IP thực tế khi kết nối để chống DNS rebinding. URL query có thể là bí mật của n8n/Power Automate: mã hóa khi lưu, che khi hiển thị/log/export. Không cho cấu hình header tùy ý tác động Host/proxy.
- HMAC SHA-256 trên timestamp + raw body, có key ID, timestamp và delivery ID; secret sinh ở server, hiển thị một lần và có rotation. Nơi nhận kiểm tra chữ ký, thời gian và chống replay; Idempotency-Key cho delivery ổn định qua retry. Delivery theo at-least-once, nơi nhận cần khử trùng.
- Retry có backoff/jitter, giới hạn số lần; chỉ retry timeout/lỗi mạng/429/5xx, tôn trọng Retry-After có giới hạn; 4xx còn lại ghi thất bại. Tách hàng đợi lỗi cuối để xem và gửi lại có audit. Tạm dừng/thu hồi quyền phải ngăn gửi các job chưa thực hiện.
- Lịch sử hiển thị queued/sending/delivered/failed/skipped, mã HTTP thật và từng attempt; log response được giới hạn, lọc bí mật và escape. Giới hạn số workflow, tần suất test/retry và quota outbound theo organization.
- Kiểm thử tenant A/B, quyền bị thu hồi, SSRF/DNS/redirect/IPv6, chữ ký và replay, timeout, 429/500, trùng sự kiện, cooldown/hysteresis, worker restart, giao hàng lặp và tạm dừng trước khi gửi.
- Đặt schema/outbox vào GĐ1, UI/API workflow vào GĐ3, worker/ingest/outbound safeguards vào GĐ4. Scanner/agent vẫn để sau.


## 10. Đối chiếu Pulse và mở rộng automation theo action (11/11/2026)

Đã xem trực tiếp Pulse alpha4 trong Chrome người dùng đăng nhập. Xem docs/pulse-reference.md và bản outputs/THAM-KHAO-PULSE.md để biết các màn đã xác minh và giới hạn. Không có máy thật trong tài khoản để kiểm chứng thực thi.

Yêu cầu đã chốt: core hành vi tham khảo Pulse; giao diện automation BeeSky dùng workflow theo action. Mục 9 chỉ là thiết kế adapter webhook, không còn đại diện toàn bộ automation.

- Thêm mục Agent riêng theo trại, có scan tasks, control mode, trạng thái kết nối và cấp/thu hồi mã. Không giấu cấu hình Agent trong hướng dẫn ở trang Trại. Scanner/agent chạy thật vẫn để sau.
- Builder: trigger lịch/sự kiện → scope → condition + hold → các action tuyến tính → kết quả. Action gồm reboot/restart/pause/resume/pool/thermal/board/webhook; mỗi loại có schema/form/capability riêng.
- Core: workflow versions, scheduler + evaluator theo từng máy, eligibility, durable jobs, queue/dispatch dùng chung thao tác tay, ACK và kết quả từng máy/action. Có cooldown/hold, loại stale/service/locked/monitor-only/unsupported, phân lô, TTL, khóa tránh xung đột và retry phù hợp từng action.
- Activity riêng cho active/attention/history; mô phỏng không tạo success thật; mọi đường đọc/ghi kiểm tra tenant/site/role.
- Bổ sung schema và permission vào GĐ1; UI Agent/Miners/Workflow/Activity vào GĐ3; executor/dispatcher/ingest vào GĐ4. Bản duyệt hiện tại chưa được đổi thành executor thật.


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


## Cập nhật: React Flow và MCP báo cáo — 11/11/2026

- Trình thiết kế Workflow đã chuyển sang React Flow thật (`@xyflow/react`), cấu hình khối ở inspector. Có kéo khối, zoom/pan, vừa khung, sắp xếp lại, thêm/bỏ/đổi thứ tự action. Dây nối thể hiện thứ tự chạy; chưa cho tạo nhánh tùy ý. Giữ schema, kiểm tra dữ liệu và mô phỏng cũ. Cấu hình/vị trí chỉ nằm trong bộ nhớ bản duyệt.
- Đã kiểm tra trên Chrome ở 1366×768 và 390×844, không tràn ngang trang; 4 khối và 3 dây nối trong workflow mẫu. Thử thay nhiệt độ mục tiêu, chuyển khối, thêm/bỏ action, lưu và kéo khối; console bản build cuối không ghi nhận lỗi trong phiên kiểm tra.
- Có mục AI & MCP trong sidebar. Backend cloud cũ được thêm endpoint `POST /mcp` chỉ đọc với 5 tool báo cáo. Đã đạt 5 bài kiểm tra gồm kết nối qua MCP Python SDK chính thức, chặn ngoài phạm vi trại, hạn dùng/thu hồi khóa, giới hạn request và kiểm tra API cũ.
- MCP mặc định không cấp quyền. Chưa nối prototype với backend, chưa cấp khóa thực tế cho ứng dụng AI. Grants hiện do quản trị viên cấu hình theo tên site; chưa thay thế tenant/account production. Thiết kế tài khoản phải gắn grant với tenant/farm ID và kiểm tra membership mỗi request. Chi tiết cấu hình và giới hạn ở `docs/mcp-reporting.md`.
