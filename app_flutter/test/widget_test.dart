import 'package:beesky_app/main.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('empty state first, scan fills the table and auto-selects', (
    tester,
  ) async {
    // The desktop layout needs a desktop-sized surface.
    tester.view.physicalSize = const Size(1500, 950);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(BeeSkyApp(bridge: MockBridge()));

    // Splash first (branding + progress), then the main window.
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 1000));
    await tester.pumpAndSettle();

    // Empty state before the first scan — the Toolkit detail.
    expect(find.text('Chưa quét'), findsOneWidget);
    expect(find.text('Tổng số máy'), findsOneWidget);

    // Target pre-filled from (mock) sysinfo: the farm subnet.
    final targetField = tester.widget<TextField>(find.byType(TextField).first);
    expect(targetField.controller!.text, '192.168.2.0/24');

    // Scan via the empty state's button.
    await tester.tap(find.text('Quét ngay').first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();

    // Table filled with the mock fleet, native units intact.
    expect(find.text('192.168.2.101'), findsWidgets);
    expect(find.text('192.168.2.102'), findsOneWidget);
    expect(find.text('14.54 MH/s'), findsWidgets);
    expect(find.text('1,101.00 ksol/s'), findsOneWidget);
    expect(find.text('330/369'), findsOneWidget);
    expect(find.text('ERROR'), findsOneWidget);

    // Stat tiles updated: 4 machines, 2 with problems.
    expect(find.text('4'), findsWidgets);
    expect(find.text('2'), findsWidgets);

    // First row auto-selected (v0.19.7): the detail panel shows it.
    expect(find.text('192.168.2.101 — Antminer S19 Pro'), findsOneWidget);
    expect(find.textContaining('Quét xong: tìm thấy 4 máy'), findsOneWidget);

    // Selecting the L9 shows its issue in the detail panel.
    await tester.tap(find.text('192.168.2.102'));
    await tester.pumpAndSettle();
    expect(find.textContaining('[MISSING_CHIPS]'), findsOneWidget);
    expect(find.text('Board 2: 84/123 chip, nhiệt 59 °C'), findsOneWidget);
  });
}
