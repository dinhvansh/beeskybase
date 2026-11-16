import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:beesky_agent_app/agent_updates.dart';
import 'package:beesky_agent_app/agent_bridge.dart';
import 'package:beesky_agent_app/config_page.dart';
import 'package:beesky_agent_app/theme.dart';

class PendingUpdater extends MockAgentUpdater {
  final result = Completer<bool>();
  int calls = 0;
  @override
  Future<bool> prepare(String config, void Function(double?, String) progress) {
    calls++;
    progress(.5, 'Đang tải bản mới… 50%');
    return result.future;
  }
}

const newer = AgentUpdateInfo(
    ok: true, available: true, latest: '99.0.0', message: 'Có bản Agent mới.');

void main() {
  Future<void> open(WidgetTester t, AgentUpdater updater,
      {MockAgentBridge? bridge}) async {
    t.view.physicalSize = const Size(1100, 900);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.reset);
    await t.pumpWidget(MaterialApp(
        theme: buildBeeSkyTheme(),
        home: AgentConfigPage(
            updater: updater,
            bridge: bridge ?? MockAgentBridge(),
            store: MockConfigStore.demo())));
    await t.pump();
    await t.pump(const Duration(milliseconds: 1100));
    await t.pump();
  }

  testWidgets('new release is visible above the form without scrolling',
      (t) async {
    await open(t, MockAgentUpdater()..info = newer);
    expect(find.text('Agent 99.0.0 đã sẵn sàng.'), findsOneWidget);
    expect(t.getRect(find.text('Cập nhật Agent')).bottom, lessThan(200));
    await t.tap(find.text('Cập nhật Agent'));
    await t.pumpAndSettle();
    expect(find.text('Cập nhật Agent 99.0.0?'), findsOneWidget);
    await t.tap(find.text('Để sau'));
    await t.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
  });
  testWidgets(
      'download progress disables conflicting actions and failure restores them',
      (t) async {
    final updater = PendingUpdater()..info = newer;
    final bridge = MockAgentBridge()..running = true;
    await open(t, updater, bridge: bridge);
    await t.tap(find.text('Cập nhật Agent'));
    await t.pumpAndSettle();
    await t.tap(find.text('Cập nhật'));
    await t.pump();
    expect(updater.calls, 1);
    expect(
        t
            .widget<FilledButton>(
                find.widgetWithText(FilledButton, 'Dừng Agent'))
            .onPressed,
        isNull);
    expect(bridge.running, isTrue); // downloading never stops a worker
    expect(find.text('Đang tải bản mới… 50%'), findsWidgets);
    updater.result
        .completeError(const FormatException('Mạng bị ngắt. Thử lại sau.'));
    await t.pump();
    await t.pump();
    expect(find.text('Mạng bị ngắt. Thử lại sau.'), findsWidgets);
    expect(
        t
            .widget<FilledButton>(
                find.widgetWithText(FilledButton, 'Dừng Agent'))
            .onPressed,
        isNotNull);
    expect(bridge.running, isTrue);
  });
  testWidgets(
      'success hands off only after download and helper acknowledgement',
      (t) async {
    final updater = PendingUpdater()..info = newer;
    var ready = 0;
    await t.pumpWidget(MaterialApp(
        theme: buildBeeSkyTheme(),
        home: Scaffold(
            body: AgentUpdatePanel(
                updater: updater,
                config: 'fixture.json',
                enabled: true,
                onBusy: (_) {},
                onInfo: (_) {},
                onReady: () => ready++))));
    await t.pump(const Duration(milliseconds: 1100));
    await t.pump();
    await t.tap(find.text('Cập nhật ngay'));
    await t.pumpAndSettle();
    await t.tap(find.text('Cập nhật'));
    await t.pump();
    expect(ready, 0);
    updater.result.complete(true);
    await t.pump();
    await t.pump();
    expect(ready, 1);
    expect(
        find.text('Đã tải xong. Agent sẽ cập nhật và mở lại.'), findsOneWidget);
  });
  testWidgets(
      'uncertain runtime protects settings and offers a refresh instead of a second start',
      (t) async {
    final bridge = MockAgentBridge()..runtimeUncertain = true;
    await open(t, MockAgentUpdater(), bridge: bridge);
    expect(find.text('Chưa xác nhận trạng thái'), findsOneWidget);
    expect(find.text('Kiểm tra trạng thái'), findsOneWidget);
    expect(find.text('Bắt đầu Agent'), findsNothing);
    for (final field in t.widgetList<TextField>(find.byType(TextField))) {
      expect(field.readOnly, isTrue);
    }
    await t.tap(find.text('Kiểm tra trạng thái'));
    await t.pump();
    expect(bridge.running, isFalse);
    expect(bridge.connectionCalls, 0);
  });
  testWidgets(
      'failed automatic check remains retryable without claiming latest',
      (t) async {
    await open(
        t,
        MockAgentUpdater()
          ..info = const AgentUpdateInfo(
              ok: false,
              available: false,
              message: 'Không kiểm tra được bản mới. Thử lại sau.'));
    expect(
        find.text('Không kiểm tra được bản mới. Thử lại sau.'), findsOneWidget);
    expect(find.text('Agent đang dùng bản mới nhất.'), findsNothing);
    expect(find.text('Cập nhật Agent'), findsNothing);
    expect(
        t
            .widget<OutlinedButton>(
                find.widgetWithText(OutlinedButton, 'Kiểm tra bản mới'))
            .onPressed,
        isNotNull);
  });
}
