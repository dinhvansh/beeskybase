# BeeSky v0.39.0 — Cloud Light Redesign Mapping

Owner's master prompt: full desktop UI/UX redesign of the BeeSky Miner
Scanner Flutter app — "BeeSky Cloud Light × Linear × Modern Windows 11
Fluent UI". Redesign, not rebuild: ALL functionality, scanning logic,
APIs, data models and persistence preserved; Python core untouched
(zero core changes in this version).

## 1. Audit (Phase 1) — what exists

### App structure
- `app_flutter/` (main app, `beesky_app` 0.38.0+19, zero third-party
  Dart deps): 15 lib files, ~14,030 lines.
- `app_agent_flutter/` (agent config app): 5 lib files, same theme file
  copy (dark), same tokens.

### Screens / routes / dialogs (all in one `_HomePageState`,
`home_page.dart` 4,792 lines; no router — `_View` enum switches)
| View | Builder | Contents |
|---|---|---|
| groups | `_groupsColumn` / `_groupsHeader` / `_groupsContent` / `_groupCard` / `_combinedCard` | Header + "Thêm nhóm" + "Gộp nhóm", search, group cards (name/targets/last-scan/summary, Quét, edit/delete/creds/reset-stats), combined-mode card, empty state "Chưa có nhóm mạng", IP-Report panel |
| miners | `_minersColumn` / `_header` / `_scanBar` / `_gridToolbar` / `_selectionBar` / `_tableCard` / `_tableHeader` / `_tableRow` / `_detailPanel` | Title + status chips (Tổng/OK/Cần kiểm tra/Lỗi/hashrate/Max °C), scan bar (target, Quét ngay, Tài khoản, Xuất phiếu sửa), grid toolbar (search, Bộ lọc, Nhóm theo, Số liệu/Pools/Tùy chỉnh, Thoải mái/Gọn/Tổng quan, Cột, Lịch sử tác vụ, Trung tâm mẫu), selection bar (count, select/invert/isolate, ops: Quét lại/Khởi động lại/Đổi pool/Xuất), dense table (29 configurable columns, sort, checkbox select, pointer-level double-click → web UI), detail side panel 300px (6 tabs: Số liệu/Biểu đồ/Board/Pools/Quạt/Ghi chú) |
| heat | `_auxColumn` → `HeatMapView` (`views.dart`) | Per-miner temp cells, offline grey, problem red border, click → miners view |
| energy | `EnergyView` | Fleet ΣkW / est. kWh-day / cost-day, 7-day integration, per-day/per-device rows |
| repairs | `RepairsView` | Ticket .txt list, tap → full text |
| events | `EventsView` | Severity chip + VN type labels, cap 500 |
| settings | `SettingsView` (5 tabs) | Chung / Tài khoản / Thời gian chờ / Nhật ký / Nâng cao — only real persisted settings |
| splash | `SplashGate` (`main.dart`) | Logo + name + tagline + slim progress, ~0.9 s |
| command palette | `_CommandPaletteDialog` (Ctrl+K) | Real commands, top-level |
| dialogs | `groups.dart` `_GroupEditorDialog`, `creds.dart` `_CredsDialog` + `CredSetsEditor`, `ops_dialogs.dart`, `presets_dialogs.dart`, `grid_dialogs.dart` | Group create/edit (validation), credential sets, ops progress/history, presets center, columns/filters |

### State management & persistence
- Single `_HomePageState` holds all UI state; zoom scale via
  `MediaQuery.textScaler` (0.90–1.30, persisted in settings).
- Persistence: JSON stores beside the exe / `%APPDATA%\BeeSky`
  (groups, creds, grid, notes, history, events, settings, ops
  history). Bridge: `BeeSkyBridge` (`sidecar.dart`) spawns
  `beesky.exe` beside the app; mock bridge via `BEESKY_MOCK` env /
  `--dart-define` (canned fleet, used for screenshots/tests).
- Hotkeys (top-level, v0.34): Ctrl+K palette, Ctrl+=/-/0 zoom,
  Ctrl+A/F/R, F5, Esc (view-guarded to miners).

### Current theme (to be REPLACED)
- `theme.dart`: dark graphite — bg #0B0B0D, panel #15151A,
  border #26262E, accent #F5D800, text #F2F2F3, muted #9CA3AF,
  ok #34D399, warn #FBBF24, bad #F87171, hotTemp #FF6B6B,
  selectBg #3A3410; radii 16 cards / 12 widgets / pills.
  `GlassCard` = dark translucent panel + rim light + heavy shadow.
- `BeeSkyColors.*` referenced ~281× across lib; hardcoded dark
  literals: `views.dart` heat bands (#2C2C2C / #14532D / #4A5D23 /
  #7A5A12 / #8A4512 / #8A1F1A) + tile sub-text `0xD9FFFFFF`,
  `_statusChip` tints `0x26…`, `home_page.dart` temp amber
  `0xFFF59E0B` (already the prompt's Warning — kept).
- The approved prototype (`proto-v22/`) is itself DARK (HashCore
  anatomy); the prompt's Light direction OVERRIDES its colors while
  KEEPING its layout (sidebar 228→188, chips row, slim scan card,
  dense table, 300px detail panel). Cloud dashboard
  (`beesky/cloud/dashboard.html`) is also dark today — the prompt's
  color table is authoritative for the new Light language.

### Implemented vs planned
- ALL seven sidebar views are implemented (the old "SAU" tags are
  gone since v0.32). Nothing in the sidebar is a placeholder.
- No planned/unfinished modules to hide; the redesign keeps all
  seven views reachable, grouped: primary (Nhóm mạng, Máy đào),
  monitoring (Bản đồ nhiệt, Điện năng, Lịch sử sửa, Sự kiện),
  system (Cài đặt).

## 2. Token mapping (Phase 2) — dark → Cloud Light

Prompt table, applied 1:1. Same constant names kept where the
meaning survives so the ~281 call sites flip with the theme:

| Token (old → new) | Value |
|---|---|
| `bg` #0B0B0D → | `#F7F8F4` App Background |
| `panel` #15151A → | `#FFFFFF` Sidebar/Surface |
| `panel2` #1C1C22 → | `#F7F8F4` |
| `border` #26262E → | `#E0E5D9` |
| `panelGlass` #191920 → | `#FFFFFF` |
| `glassBorder` #34343E → | `#E0E5D9` |
| `rimLight` #3D3D4A → | `#FFFFFF` (rim removed) |
| `ghostFill` #22222B → | `#EFF2EA` |
| `entryFill` #1E1E26 → | `#FFFFFF` |
| `entryBorder` #30303C → | `#E0E5D9` |
| `tableWell` #121216 → | `#FFFFFF` |
| `tableHeading` #1D1D24 → | `#F7F8F4` |
| `tableZebra` #17171D → | `#FAFBF8` |
| `accent` #F5D800 → | `#FFE000` Brand Primary |
| `accentText` #141414 → | `#141414` (dark on yellow — unchanged) |
| `text` #F2F2F3 → | `#202A28` Text Primary |
| `muted` #9CA3AF → | `#7B8877` Text Secondary |
| `ok` #34D399 → | `#16A34A` Success |
| `warn` #FBBF24 → | `#F59E0B` Warning |
| `bad` #F87171 → | `#DC2626` Error |
| `hotTemp` #FF6B6B → | `#DC2626` |
| `selectBg` #3A3410 → | `#FFF1B7` Active Navigation |
| NEW `brandHover` | `#F5D200` |
| NEW `activeNav` | `#FFF1B7` |
| NEW `info` | `#2563EB` |
| NEW `surface` | `#FFFFFF` |
| NEW `accentInk` | `#7A5A00` — dark amber for small yellow-meaning text/icons on light (yellow #FFE000 text on white fails contrast; every accent-as-text call site moves to `accentInk`, accent stays for fills/borders only) |

Radii: `radiusCard` 16→12, `radiusWidget` 12→8, `radiusPill` 999
(prompt: cards 10–12, buttons 8–9, inputs 8). `GlassCard` restyled:
white surface, 1px `#E0E5D9` border, one soft shadow
(0 1px 2px rgba(32,42,40,.06)), no rim light, 12px corners.

Typography: `ThemeData.light`, `fontFamilyFallback: [Inter,
'Segoe UI', Roboto]` (no bundled font, no new deps — Segoe UI is
the Windows native face); titles 22px (page) / 16px (detail),
section 14–16px, body 12–14px, table labels 11px, tabular figures
(`FontFeature.tabularFigures`) for numeric cells, monospace
(`fontFamilyFallback: [Consolas, 'Courier New']`) for IPs.

## 3. Screen-by-screen change list (Phases 3–4)

- **Shell**: sidebar 228→188px, white, logo + "BeeSky / QUẢN LÝ
  MÁY ĐÀO"; section captions ("QUẢN LÝ", "THEO DÕI", "HỆ THỐNG");
  active item = `#FFF1B7` bg + `#202A28` text/icon (was accent
  13% tint + yellow text); inactive = muted text; hover = light
  fill. Topbar: breadcrumb row ("BeeSky / <page>") + connection
  pill (sidecar status, reused `_sidecarStatus`) at the right of
  the miners/groups headers. Footer: `_statusLine` → slim status
  bar (top border, readiness dot + status text + app version).
- **Headers**: page titles 20→22px, subtitle muted 12px, chips row
  unchanged in content (real data only).
- **Groups**: cards via restyled `GlassCard`; "MỚI" pill text →
  `accentInk`; empty state keeps "Chưa có nhóm mạng" +
  "Tạo nhóm mạng" (button already exists as "Thêm nhóm" in the
  header — the empty state adds its own primary action per the
  prompt).
- **Miners**: scan bar card white; table heading `#F7F8F4` with
  11px muted labels, sorted column → `accentInk` label + icon;
  selected row bg `#FFF1B7` + 3px `#FFE000` bar; zebra `#FAFBF8`;
  status chips: tint bg 15% of the new ok/warn/bad + same-color
  bold text (hardcoded `0x26…` tints updated to the new hues);
  `_segmented` / `_miniToggle` selected → `#FFF1B7` bg +
  `#202A28` text; overview selected cell border → `accentInk`.
- **Detail panel**: `GlassCard` white; tab pills active = yellow
  bg + dark text (unchanged — already correct on light).
- **Views (heat/energy/repairs/events/settings)**: `viewHeader`
  22px + breadcrumb; heat bands → pastel scale
  (<60 `#D1FAE5`, <70 `#FEF9C3`, <80 `#FDE68A`, <90 `#FED7AA`,
  ≥90 `#FECACA`, offline `#E5E7EB`, dark text on all); tile
  sub-text white 85% → dark 70%.
- **Dialogs**: no structural change; AlertDialog/Dialog surface
  follows the light theme; focused borders → `accentInk`;
  floating labels → `accentInk`.
- **Agent app** (`app_agent_flutter/`): same token file applied
  (its `theme.dart` is a copy); layout/behavior untouched.

## 4. Preservation list (hard constraints)
- DENSE + TABLE-FIRST; big stat cards BANNED (prompt agrees).
- Zero new third-party Dart deps; no framework migration.
- Python core untouched (mock sweep must stay green).
- Credential handling unchanged; no secrets in logs/UI.
- No invented data/API fields; no fake miner data or fabricated
  progress (scan states Ready/Starting/Scanning/Completed/Failed/
  Cancelled already real; splash progress is a timed hand-over,
  unchanged).
- All hotkeys, zoom, command palette, ops, presets, filters,
  grouping, selection, double-click-to-web-UI preserved.

## 5. Validation
- `flutter analyze` clean (both apps), `flutter test` green
  (main 159, agent 34 — counts updated if tests change).
- Python mock sweep green (`tests/run_mock_test_v38.sh`).
- 2x screenshots (Xvfb, mock bridge): Groups, Miners, Detail,
  Settings → `~/workspace/beesky-demo/redesign-v39/`.
- Known limits: no real-hardware/network verification (mock data
  only); Inter is a fallback name, not a bundled font (Segoe UI
  renders on Windows); `flutter build windows` cannot run on this
  Linux VM — Linux build + Xvfb render is the verification path.

## 6. Completion record (v0.39.0, 2026-11-12)

- Two tests broke mid-redesign and were fixed IN THE UI,
  not by weakening the tests: (1) widget_test expected
  "BeeSky v0.38.0" once — the new footer status bar
  duplicated the sidebar footer's version; version removed
  from the status bar. (2) detail_test note save — the
  taller header (breadcrumb) pushed the note tab's save
  button below the fold at 1280×800; fixed with a sticky
  save row at the panel bottom (only for the note tab) +
  header padding trimmed 16→12 / 12→10. Verified the
  note test passes on pristine HEAD (git stash -u) before
  concluding the redesign broke it.
- Logo subtitle 'QUẢN LÝ MÁY ĐÀO' clipped at the 188px
  sidebar on wide fonts (DejaVu on Linux): 10px/1.6 →
  9px/0 letter-spacing; verified full text in the shot.
- Screenshots: real Flutter render, Linux build
  (temporary local-only linux/ runner, removed before
  commit; default window 2560×1600 set in the runner),
  Xvfb :99, BEESKY_MOCK=1, XTest clicks + Ctrl+R hotkey,
  full-window 2560×1600 captures in
  ~/workspace/beesky-demo/redesign-v39/ (01-groups,
  02-miners, 03-detail, 04-settings + shoot*.py drivers).
  Toolchain needed first: ninja-build + clang +
  libgtk-3-dev via apt (libzstd1 downgraded hatch1 →
  archive build to unbreak the install). Screenshot
  driving note: click coordinates must be measured from
  full-res renders, never estimated from downscaled views
  (~50–60px error); button bands located by pixel scan.
- Version bumped 0.38.0 → 0.39.0 at all pin locations
  (core, both pubspecs +20/+10, both .iss, models,
  sidecar mock sysinfo, agent_config, pin suite).
- Final verification: analyze clean both apps; flutter
  test main 159/159, agent 34/34; mock sweep all 18
  suites green at established counts; screenshots
  verified (Groups / Miners filled by live mock scan /
  Detail ×2 states / Settings 5 tabs).
- Known minor notes (not fixed, pre-existing): Settings
  "Chung" fields sit close (floating label nearly touches
  the field above); mock S19 Pro detail title doubles
  "Pro". Inter is a fallback name, not a bundled font.

## 7. v0.39.1 — tab-label contrast fix (2026-11-12, owner catch)

- Owner: "hover mà chữ màu vàng có thấy chóa gì đâu".
  Cause: the bare TabBars (Settings 5 tabs, Presets center)
  had no labelColor, so they inherited
  colorScheme.primary = #FFE000 — selected tab and any
  hovered tab rendered yellow text on white (~1.6:1).
- Fix (theme.dart only): TabBarTheme labelColor =
  accentInk #7A5A00, unselectedLabelColor = muted,
  indicatorColor stays brand yellow (a fill), hover
  overlay = pale activeNav wash. Yellow is a fill/border
  color only, never small text on white (same rule the
  theme header already stated — the TabBar was the one
  leak). Agent app checked: no TabBar anywhere, no fix
  needed there.
- Regression test: views_test.dart 'tab bar contrast'
  pins the three theme values. Verified by real render:
  Linux build + Xvfb :99 + BEESKY_MOCK=1, re-shot
  04-settings + new 05-settings-hover (mouse over
  'Tài khoản', no click) — both readable, no yellow text.
  Note: the inner `beesky_app` X window must be resized
  to 2560x1600 itself (the parent window's configure
  does not resize it; it renders 1280x720 otherwise).
- Verification: analyze clean; flutter test main 160/160
  (159 + new test), agent 34/34. No Python touched, so
  no mock-sweep rerun. No version bump (v0.39.0 not
  released yet); fix folds into v0.39.0.

## 8. v0.39.2 — tab labels black, hover has no yellow (2026-11-12, owner feedback)

- Owner: "vẫn gớm — cho chữ đen, hover hok nhất thiết
  màu vàng". The v0.39.1 dark-amber label (#7A5A00)
  still looked off to him, and the pale-amber hover wash
  was yellow he never asked for.
- Fix (theme.dart only, same TabBarTheme): labelColor =
  text #202A28 (plain black), unselected stays muted,
  hover overlay = ghostFill #EFF2EA (neutral pale grey,
  zero yellow). Yellow survives only as the thin
  underline indicator under the selected tab.
- Regression test updated to pin labelColor = text and
  hover overlay = ghostFill. Re-rendered 04-settings +
  05-settings-hover from the real Linux build — labels
  black, hover grey, no yellow text/wash anywhere.
- Verification: analyze clean; flutter test main 160/160,
  agent 34/34. Still no version bump; folds into v0.39.0.

## 10. v0.39.4 — settings content width 860 → 1400 (2026-11-12, owner feedback)

- Owner: "sao m thu gọn còn có 1 góc z" — at 860px the
  page sat in one corner with most of the window empty.
- Fix (views.dart, one constant): content maxWidth 860 →
  1400, still left-aligned with the page header so title,
  tabs and cards share one left edge. At a laptop window
  (~1680, like the owner's reference shot) 1400 fills the
  content area like the reference; the 2-col rows still cap
  each input (~680px). No other layout change; all 5 tabs
  inherit it from the shared column.
- Verification: analyze clean; flutter test main 162/162,
  agent not re-run (untouched). Re-rendered 01-general +
  08-general-zoom from the real Linux build — cards now
  span to ~62% of the 2560 render (was ~33%). No version
  bump; folds into v0.39.0.

## 9. v0.39.3 — full Settings page redesign (2026-11-12, owner reference image)

- Owner sent a Settings mock (image-3.png): compact dense
  form, section cards, 2-col fields, labels above inputs,
  yellow active tab, yellow "Lưu thay đổi" bottom-right.
  Redid the whole Settings page (views.dart `_SettingsViewState`
  + compact form helpers), not just colors. Same design
  system on all 5 tabs; every existing field, validation
  range and save path preserved (docs/settings-mapping.md).
- Layout: content capped at 860px and LEFT-aligned with the
  page header (viewHeader's 18px inset) — title, tabs and
  cards share one left edge; first cut centered the column
  and left a 750px gap under the title, fixed before
  rendering. Compact icon TabBar (height 38, icons
  settings/person/timer/article/tune): active = pale-yellow
  `activeNav` pill + black text + yellow underline; labels
  black, hover = neutral ghostFill wash (v0.39.2 rulings
  kept). Labels above inputs (13px semibold), fields 40px
  tall, 13px text, 8px radius, thin theme borders; sections
  in GlassCard with 13px bold title + accentInk icon;
  2-col rows via `_twoCol` (stacks under 560px).
- Per tab: Chung = "Quét & điện" (target + price, 2-col)
  + "Giao diện & IP Report" (scale stepper 90–130% in a
  40px box + IP Report switch with Đang nghe/Đang tắt);
  Tài khoản = "Tài khoản máy đào" explainer + 2 link rows;
  Thời gian chờ = "Thời gian chờ" card (probe/request 2-col,
  stagger left + helper note right); Nhật ký = "Thư mục dữ
  liệu" (150px label col) + "Dọn dẹp" (2 clear buttons);
  Nâng cao = "Nâng cao" (scan/ops workers 2-col + helper)
  + "Giới thiệu" (app + ruột quét versions).
- Dirty-tracking (req. 8): `_baseline` = last saved
  settings; `_isDirty` compares all 9 fields (controllers
  + scale + ipReport); save disabled while clean, re-baselined
  after a successful save; `didUpdateWidget` adopts the
  parent's externally re-saved settings only while the form
  is clean (protects unsaved edits from zoom hotkeys);
  `AppSettings` gained value equality over all 9 fields.
  Button renamed "Lưu cài đặt" → "Lưu thay đổi". Footer:
  error text left, outlined "Khôi phục mặc định" + yellow
  "Lưu thay đổi" right. Restore-defaults fills factory
  `AppSettings()` into the form through the existing onSave
  path — nothing is persisted until Lưu thay đổi is tapped.
- Deliberately NOT added from the reference: "Lưu trữ /
  Thư mục dữ liệu" field, "Ngôn ngữ", "Chủ đề" — none exist
  in the app backend (req. 9). The Logs tab already shows
  the real data dir read-only; no language/theme setting
  exists to wire.
- Tests: 2 new regression tests (save disabled until the
  form changes, then disables again after saving;
  restore-defaults fills factory values without saving
  until Lưu thay đổi). Test quirk found: `tester.enterText`
  pumps only inside `showKeyboard` (before the text is
  set); `idle()` does not pump — a controller-listener
  `setState` needs an explicit `await tester.pump()`
  before tapping the save button. Added the pump + comment
  to the two affected tests.
- Render toolchain note: this VM was replaced since
  v0.39.2, wiping libgtk-3-dev/clang/ninja. The apt source
  lists a dead second mirror (mirror.cogentco.com) that
  stalls `apt-get update` for 10+ min; fix = drop it and
  use azure.archive.ubuntu.com only (+
  `Acquire::Languages=none` to skip the huge Translation
  files; update then takes ~20s). libzstd1 still needs the
  hatch1 → archive downgrade before libgtk-3-dev installs.
  Overlayfs quirk: an existing root-owned-by-nobody file
  under /etc/apt/sources.list.d/ cannot be truncated in
  place (Permission denied as root) — write a NEW file and
  delete the old one instead. Also: Xvfb tab clicks lag one
  step behind with a 1.2s settle — use 2.5s between click
  and screenshot, and verify each shot's active pill
  (measured pill x-ranges: Tài khoản 306–391, Thời gian chờ
  412–525, Nhật ký 543–615, Nâng cao 637–720).
- Verification: analyze clean; flutter test main 162/162
  (160 + 2 new), agent 34/34. Real Linux render (Xvfb :99,
  BEESKY_MOCK=1, inner window resized to 2560x1600): all 5
  tabs + dirty state (IP Report ON, "Lưu thay đổi" solid
  yellow) + tab-row and Chung content zooms (2x LANCZOS),
  all viewed, no overflow/clipping. Shots in
  ~/workspace/beesky-demo/redesign-v39/settings-v2/.
  No Python touched, so no mock-sweep rerun. No version
  bump; folds into v0.39.0.
