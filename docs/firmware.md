# Firmware — identify / install / unlock (v0.11)

> ⚠️ **THỬ NGHIỆM / EXPERIMENTAL.** Nhóm lệnh `beesky fw` nạp firmware
> vào máy đào thật. Luôn thử firmware mới bằng **boot thẻ SD trước**
> (SD-boot-first): bản SD chạy tốt rồi mới tính chuyện ghi NAND. Nếu
> nạp hỏng, đường khôi phục là **cài lại firmware gốc** (tải từ
> Bitmain) hoặc boot lại bằng thẻ SD gốc — chuẩn bị sẵn media khôi
> phục TRƯỚC khi chạy bất kỳ lệnh nào ở trang này. Hashboards không
> bị đụng tới bởi việc nạp firmware; phần có rủi ro là control board.

Nguồn sự thật của trang này: bản đồ API của chính firmware VNish
(`api-doc.json` trong rootfs VNish) cho đường dashd, và bản khôi phục
recipe unlock từ HashCore Toolkit 1.7.5
(`~/workspace/asic-os-s19pro/research/hashcore/UNLOCK-DEEP.md`, gói
nghiên cứu đi kèm repo nghiên cứu ASIC) cho đường unlock.

## 1. `fw identify <ip>` — máy này đang chạy firmware gì?

```bash
beesky fw identify 192.168.1.50
beesky fw identify 192.168.1.50 --ssh-key ~/.ssh/miner_ed25519
```

Probe theo chuỗi adapter quen thuộc (cgminer RPC → dashd → stock CGI).
Với máy stock, BeeSky đọc thêm `/cgi-bin/miner_type.cgi` (digest auth)
và — qua SSH — `cat /usr/bin/compile_time`. Kết luận in ra là một
trong bốn dòng:

| Kết luận | Ý nghĩa |
|---|---|
| `VNish/dashd — cài firmware qua API được` | Máy VNish/HashCore; dùng `fw install` đường API |
| `stock cũ / đã mở SSH` | Stock nhưng SSH vào được (compile_time đọc được) — thường cài thẳng qua web/SSH được |
| `stock khoá (cần unlock)` | Web trả lời nhưng SSH không vào — build stock bị khoá, muốn đổi firmware phải unlock (mục 3) |
| `không rõ` | Không đủ dữ kiện (vd máy này không có `ssh` client nên không kiểm tra được SSH) |

Thông tin SSH chỉ lấy từ cờ: `--ssh-user`, `--ssh-key`,
`--ssh-password-env <TÊN_BIẾN>` (mật khẩu nằm trong biến môi trường,
không bao giờ gõ thẳng lên dòng lệnh; đăng nhập bằng mật khẩu cần thêm
chương trình `sshpass` trên máy chạy BeeSky). Không có sẵn `ssh`
client thì các bước cần SSH sẽ báo rõ và dừng.

## 2. `fw install <ip> <file>` — cài firmware

```bash
beesky fw install 192.168.1.50 vnish-s19pro.tar.gz            # sẽ bắt gõ lại IP để xác nhận
beesky fw install 192.168.1.50 vnish-s19pro.tar.gz --yes      # bỏ qua xác nhận
beesky fw install 192.168.1.50 fw.tar.gz --wait-minutes 0     # không chờ máy lên lại
```

Trước khi gửi, BeeSky in kích thước + SHA-256 của file và (trừ khi có
`--yes`) bắt **gõ lại đúng IP đích** mới nạp. Đường nạp tự chọn theo
nguồn đã probe:

* **VNish/dashd** — endpoint có thật trong `api-doc.json`:
  `POST /api/v1/firmware/update`, `multipart/form-data`, field `file`
  (binary, bắt buộc) + field tuỳ chọn `keep_settings` (`"true"` /
  `"false"`, BeeSky: `--keep-settings true|false`). Auth: bearer JWT
  hoặc `x-api-key` (`--api-key` / `--token`; chỉ có mật khẩu web thì
  dùng `--dashd-password` để đổi lấy JWT qua `POST /api/v1/unlock`
  trước). Trả 200 kèm `{"after": N}` = máy reboot sau N giây.
* **Stock Bitmain** — multipart POST file lên `/cgi-bin/upgrade.cgi`
  sau digest auth (field `file` — đúng tên field của form nâng cấp
  stock). Máy tự kiểm tra chữ ký và reboot theo lịch của nó; build
  stock **đã khoá chữ ký sẽ từ chối** firmware lạ — đó là lúc cần mục 3
  (hoặc boot SD).

Sau khi nạp xong, BeeSky poll lại máy tối đa `--wait-minutes` phút
(mặc định 5) và báo khi máy trả lời lại (kèm source/model mới nếu
khác). `--wait-minutes 0` = nạp xong là xong, không chờ.

## 3. `fw unlock <ip>` — THỬ NGHIỆM: mở khoá máy stock bị khoá

Recipe này khôi phục ở mức bước (~85%) từ core Rust `btm-lib` của
HashCore Toolkit (`unlock_flow.rs`, `upgrade_race.rs` — xem
UNLOCK-DEEP.md). BeeSky chạy lại đúng trình tự đó, từng stage có kiểm
chứng, **dừng ngay ở stage đầu tiên thất bại**:

```
1. identify + version gate
   GET /cgi-bin/miner_type.cgi (digest)  +  SSH: cat /usr/bin/compile_time
2. upload update_first.bmu  ->  POST /cgi-bin/upgrade.cgi (multipart,
   boundary riêng "sshPayloadThenUpgradeCgiUnlockBoundary" như recipe)
   ĐỒNG THỜI — THE RACE: qua SSH, bắn lặp lại
   kill -9 $(pgrep -f 'openssl dgst -sha256 -verify /etc/bitmain-adv.pub')
   trong suốt lúc upload (tiến trình kiểm chữ ký bị giết giữa chừng
   thì upgrade được đi tiếp)
3. upload update_second.bmu ->  POST /cgi-bin/upgrade.cgi
4. poll marker thành công: GET /cgi-bin/patch_success.cgi -> 200
5. cleanup (best effort): rm /nvdata/update.log, rm -rf /tmp/tmpfw
   (việc khôi phục access files /etc/passwd, /etc/sudoers.dist,
   /config/passwd thuộc về payload theo recipe gốc)
```

### Ba cổng cứng (hard gates) — thiếu một là TỪ CHỐI trước mọi I/O mạng

1. Cờ `--experimental-unlock`;
2. Biến môi trường `BEESKY_ALLOW_UNLOCK=1`;
3. **Gõ lại đúng IP đích** khi được hỏi (không có `--yes` cho unlock).

```bash
BEESKY_ALLOW_UNLOCK=1 beesky fw unlock 192.168.1.50 \
    --payload-dir ./payload --experimental-unlock \
    --ssh-user root --ssh-key ~/.ssh/miner_ed25519
```

### Hai khoảng trống đã biết (đọc kỹ trước khi chạy thật)

* **Payload `.bmu` do người dùng tự cung cấp.** `update_first.bmu` /
  `update_second.bmu` nằm trong gói firmware của nhà sản xuất giải
  pháp unlock, **BeeSky không kèm sẵn file nào**, và định dạng
  container `.bmu` chưa khôi phục được. Thiếu file → lệnh báo rõ và
  dừng trước khi chạm vào máy.
* **Timing của race chưa khôi phục được.** Toolkit bắn kill vào đúng
  khoảnh khắc nào trong lúc upgrade thì chưa biết; BeeSky bắn lặp lại
  trong suốt cửa sổ upload, `--race-delay-ms` (mặc định 0) chỉnh độ
  trễ trước phát đầu tiên. **Lần chạy thật đầu tiên là một lần hiệu
  chuẩn (calibration)** — chạy trên máy bench, có sẵn SD/firmware gốc
  để khôi phục. Tương tự, cửa sổ phiên bản stock được hỗ trợ (version
  gate theo compile_time) chưa khôi phục được danh sách cụ thể:
  BeeSky in compile_time ra để đối chiếu và dừng nếu không đọc được,
  quyết định chạy tiếp thuộc về người vận hành qua cổng xác nhận.

## 4. Quy tắc an toàn

* SD-boot-first: firmware nào chưa boot SD thành công trên đúng model
  máy thì **không** nạp NAND.
* Một máy một lần, máy bench trước, trại sau.
* Chuẩn bị sẵn: file firmware gốc của Bitmain cho đúng model +
  thẻ SD boot được + nguồn điện ổn định trong lúc nạp.
* Unlock chỉ dành cho máy của chính mình/trong xưởng mình quản lý —
  nó vô hiệu hoá bước kiểm chữ ký của nhà sản xuất.
* Sau unlock/install, chạy `beesky scan` kiểm tra lại hashrate, chip
  và nhiệt độ trước khi trả máy về dàn.
