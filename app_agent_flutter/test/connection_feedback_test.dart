import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:beesky_agent_app/agent_bridge.dart';
import 'package:beesky_agent_app/config_page.dart';
import 'package:beesky_agent_app/theme.dart';

class PendingBridge extends MockAgentBridge {
  final response = Completer<AgentConnection>();
  @override
  Future<AgentConnection> connectionInfo(
          {required String configPath,
          required String cloudUrl,
          required String? key}) =>
      response.future;
}

void main() {
  Future<void> pump(WidgetTester t, AgentBridge bridge) async {
    t.view.physicalSize = const Size(1100, 768);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.reset);
    await t.pumpWidget(MaterialApp(
        theme: buildBeeSkyTheme(),
        home: AgentConfigPage(bridge: bridge, store: MockConfigStore.demo())));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
  }

  testWidgets('connection never fails silently and its result is next to token',
      (t) async {
    final bridge = PendingBridge();
    await pump(t, bridge);
    await t.tap(find.text('Kiểm tra token'));
    await t.pump();
    expect(find.text('Đang kiểm tra…'), findsOneWidget);
    expect(find.text('Đang kiểm tra token với Mine…'), findsWidgets);
    bridge.response.completeError(
        const FormatException('Token đã thu hồi. Tạo token mới trên Mine.'));
    await t.pump();
    await t.pump(const Duration(milliseconds: 20));
    final inline = find.descendant(
        of: find.byKey(const ValueKey('agent-connection-feedback')),
        matching: find.text('Token đã thu hồi. Tạo token mới trên Mine.'));
    expect(inline, findsOneWidget);
    expect(t.getRect(inline).bottom, lessThan(768));
    await t.pumpWidget(const SizedBox.shrink());
  });
  testWidgets(
      '25 second timeout restores the check action with a visible error',
      (t) async {
    final bridge = PendingBridge();
    await pump(t, bridge);
    await t.tap(find.text('Kiểm tra token'));
    await t.pump();
    await t.pump(const Duration(seconds: 26));
    await t.pump();
    expect(find.text('Kiểm tra token'), findsOneWidget);
    expect(
        find.textContaining('Cloud chưa phản hồi sau 25 giây'), findsWidgets);
    expect(t.takeException(), isNull);
    await t.pumpWidget(const SizedBox.shrink());
  });
  testWidgets('reopening observes the independently running Agent', (t) async {
    final bridge = MockAgentBridge();
    await bridge.startAgent('mock/agent-config.json');
    await pump(t, bridge);
    expect(find.text('Dừng Agent'), findsOneWidget);
    expect(find.text('Agent đang dùng token đã lưu.'), findsOneWidget);
    expect(find.text('Chưa có dữ liệu mới'), findsOneWidget);
    await t.tap(find.text('Dừng Agent'));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
    expect(find.text('Bắt đầu Agent'), findsOneWidget);
    expect(find.text('Đã dừng'), findsOneWidget);
    await t.pumpWidget(const SizedBox.shrink());
  });
}
