import 'package:beesky_app/main.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'sidebar + chips layout: empty state first, scan fills the table, '
    'detail panel opens on the first row',
    (tester) async {
      // Desktop surface, HashCore-Toolkit-sized.
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(BeeSkyApp(bridge: MockBridge()));

      // Splash first (branding + progress), then the main window.
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
      await tester.pump(const Duration(milliseconds: 1000));
      await tester.pumpAndSettle();

      // Sidebar: brand + tagline, the active view, the roadmap views
      // greyed with a "SAU" tag each, version + mock status at the foot.
      expect(find.text('QUẢN LÝ MÁY ĐÀO'), findsOneWidget);
      expect(find.text('Bản đồ nhiệt'), findsOneWidget);
      expect(find.text('Điện năng'), findsOneWidget);
      expect(find.text('Lịch sử sửa'), findsOneWidget);
      expect(find.text('Sự kiện'), findsOneWidget);
      expect(find.text('Cài đặt'), findsOneWidget);
      expect(find.text('SAU'), findsNWidgets(5));
      expect(find.text('BeeSky v0.28.0'), findsOneWidget);
      expect(find.text('Ruột quét: dữ liệu mẫu'), findsOneWidget);

      // v0.24: the app OPENS on network groups (the HashCore home
      // screen) — the mock shell seeds two demo groups: the main
      // hall with a last-scan summary, the second hall never
      // scanned (MỚI tag, "Chưa quét").
      expect(find.text('Tổng 2 nhóm'), findsOneWidget);
      expect(find.text('Trại chính'), findsOneWidget);
      expect(find.text('Kho phụ'), findsOneWidget);
      expect(find.text('MỚI'), findsOneWidget);
      expect(find.text('Chưa quét'), findsOneWidget);
      expect(find.textContaining('4 máy • OK 1'), findsOneWidget);

      // The miners view is one sidebar click away.
      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();

      // v0.23 scan bar: the local-web button is GONE (a miner row
      // double-click opens the miner's own web instead), and the
      // single user/password pair is replaced by the saved-sets
      // button — mock mode seeds 3 demo sets.
      expect(find.text('Mở web local'), findsNothing);
      expect(find.text('Tài khoản: 3 bộ'), findsOneWidget);

      // The v0.21 stat tiles are GONE — stats live in header chips now.
      expect(find.text('Tổng số máy'), findsNothing);
      expect(find.text('Tổng hashrate'), findsNothing);
      expect(find.text('Máy có vấn đề'), findsNothing);
      expect(find.text('Nhiệt độ cao nhất'), findsNothing);

      // Empty state before the first scan, inside the table area.
      expect(find.text('Chưa quét'), findsOneWidget);
      expect(find.text('Tổng — máy'), findsOneWidget);

      // Target pre-filled from (mock) sysinfo: the farm subnet.
      final targetField = tester.widget<TextField>(
        find.byType(TextField).first,
      );
      expect(targetField.controller!.text, '192.168.2.0/24');

      // Scan via the scan bar's button (first "Quét ngay" in the tree;
      // the empty state carries the second one).
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();

      // Table filled with the mock fleet, native units intact.
      expect(find.text('192.168.2.101'), findsWidgets);
      expect(find.text('192.168.2.102'), findsOneWidget);
      expect(find.text('14.54 MH/s'), findsOneWidget);
      expect(find.text('1,101.00 ksol/s'), findsOneWidget);
      expect(find.text('330/369'), findsOneWidget);
      expect(find.text('ERROR'), findsOneWidget);

      // Header chips updated: 4 machines — 1 OK, 2 CHECK, 1 ERROR —
      // grouped hashrate, hottest board 88 °C (the Z15's hot board).
      expect(find.text('Tổng 4 máy'), findsOneWidget);
      expect(find.text('OK 1'), findsOneWidget);
      expect(find.text('Cần kiểm tra 2'), findsOneWidget);
      expect(find.text('Lỗi 1'), findsOneWidget);
      expect(
        find.text('110.50 TH/s · 14.54 MH/s · 1,101.00 ksol/s'),
        findsOneWidget,
      );
      expect(find.text('Max 88 °C'), findsOneWidget);

      // The NHIỆT column shows EVERY board's temp, in chain order —
      // the S19's three boards, the Z15's three boards.
      expect(find.text('61°'), findsOneWidget);
      expect(find.text('65°'), findsOneWidget);
      expect(find.text('63°'), findsOneWidget);
      expect(find.text('71°'), findsOneWidget);
      expect(find.text('73°'), findsOneWidget);
      // The board at/over 85 °C is bold red; its neighbours stay muted.
      final hot = tester.widget<Text>(find.text('88°'));
      expect(hot.style!.color, BeeSkyColors.hotTemp);
      expect(hot.style!.fontWeight, FontWeight.w800);
      final calm = tester.widget<Text>(find.text('71°'));
      expect(calm.style!.color, BeeSkyColors.muted);
      // The unreachable unit carries no temps at all — its row still
      // renders the max-temp fallback placeholder "—".
      final deadRow = find.ancestor(
        of: find.text('192.168.2.104'),
        matching: find.byType(InkWell),
      );
      expect(
        find.descendant(of: deadRow, matching: find.text('—')),
        findsWidgets,
      );

      // First row auto-selected (v0.19.7): the detail PANEL opened —
      // its sub line is "ip • source", unique to the panel.
      expect(find.text('192.168.2.101 • VNish'), findsOneWidget);
      expect(find.textContaining('Quét xong: tìm thấy 4 máy'), findsOneWidget);

      // The mock S19 authenticated with a saved set: the panel names
      // the winning login (v0.23 cred_label).
      expect(find.text('Đăng nhập'), findsOneWidget);
      expect(find.text('VNish trại A'), findsOneWidget);

      // Selecting the L9 shows its issue box and its boards, each
      // board line carrying that board's OWN temperature.
      await tester.tap(find.text('192.168.2.102'));
      await tester.pumpAndSettle();
      expect(find.textContaining('[MISSING_CHIPS]'), findsOneWidget);
      expect(find.text('330 / 369'), findsOneWidget);
      expect(find.text('Board 1: 123/123 chip • 57°C'), findsOneWidget);
      expect(find.text('Board 2: 84/123 chip • 59°C'), findsOneWidget);
      expect(find.text('Board 3: 123/123 chip • 58°C'), findsOneWidget);

      // Selecting the Z15: its OVER_TEMP box shows, and the hot
      // board's detail line takes the same red as the table pill —
      // table and panel agree on which board is over the line.
      await tester.tap(find.text('192.168.2.103'));
      await tester.pumpAndSettle();
      expect(find.text('192.168.2.103 • cgminer RPC'), findsOneWidget);
      expect(find.textContaining('[OVER_TEMP]'), findsOneWidget);
      expect(find.text('Board 1: 24/24 chip • 71°C'), findsOneWidget);
      expect(find.text('Board 3: 24/24 chip • 73°C'), findsOneWidget);
      final hotLine = tester.widget<Text>(
        find.text('Board 2: 24/24 chip • 88°C'),
      );
      expect(hotLine.style!.color, BeeSkyColors.hotTemp);

      // Closing the panel gives the table the full width again.
      await tester.tap(find.byIcon(Icons.close));
      await tester.pumpAndSettle();
      expect(find.textContaining('[MISSING_CHIPS]'), findsNothing);
      expect(find.text('192.168.2.102 • cgminer RPC'), findsNothing);
      expect(find.text('192.168.2.102'), findsOneWidget);
    },
  );
}
