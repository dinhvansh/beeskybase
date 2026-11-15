import 'package:beesky_app/main.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('laptop rail keeps scan data and display controls usable',
      (tester) async {
    tester.view.physicalSize = const Size(1024, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(BeeSkyApp(bridge: MockBridge()));
    await tester.pumpAndSettle();
    expect(find.byTooltip('Mở rộng menu'), findsOneWidget);
    await tester.tap(find.byTooltip('Máy đào'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Quét ngay').first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 750));
    await tester.pumpAndSettle();
    expect(find.text('192.168.2.101'), findsWidgets);
    await tester.tap(find.text('Hiển thị'));
    await tester.pumpAndSettle();
    expect(find.text('Cột'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('Ẩn hiển thị'));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Mở rộng menu'));
    await tester.pumpAndSettle();
    expect(find.text('MINE SCANNER'), findsOneWidget);
    expect(find.text('192.168.2.101'), findsWidgets);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('Agent start stays visible on a short laptop window',
      (tester) async {
    tester.view.physicalSize = const Size(1024, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(BeeSkyApp(bridge: MockBridge()));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Chế độ Agent'));
    await tester.pumpAndSettle();
    expect(find.text('Token Agent:'), findsOneWidget);
    final start = find.text('Bắt đầu Agent');
    expect(start, findsOneWidget);
    expect(tester.getRect(start).bottom, lessThan(640));
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
