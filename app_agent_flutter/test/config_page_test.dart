import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:beesky_agent_app/agent_bridge.dart';
import 'package:beesky_agent_app/agent_config.dart';
import 'package:beesky_agent_app/config_page.dart';
import 'package:beesky_agent_app/theme.dart';

Future<void> _pumpPage(
  WidgetTester tester, {
  required AgentBridge bridge,
  required AgentConfigStore store,
}) async {
  // A realistic window (the runner opens at 780x840): the default
  // 800x600 test surface leaves the actions row below the fold of
  // the scroll view, where taps cannot land.
  tester.view.physicalSize = const Size(1100, 900);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(
    theme: buildBeeSkyTheme(),
    home: AgentConfigPage(bridge: bridge, store: store),
  ));
  // Let the async init (sysinfo / task probe / load) land.
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 50));
}

TextField _field(WidgetTester tester, int index) =>
    tester.widget<TextField>(find.byType(TextField).at(index));
// Field order in the tree: 0 cloud, 1 key, 2 site, 3 target, 4 interval.

void main() {
  testWidgets(
      'fixed destination is readonly; invalid token cannot start a scan',
      (tester) async {
    final bridge = MockAgentBridge()..connectionError = 'Token đã thu hồi.';
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);
    expect(_field(tester, 2).readOnly, isTrue);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Chạy thử'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
    expect(bridge.testCalls, 0);
    expect(find.text('Token đã thu hồi.'), findsWidgets);
  });

  testWidgets(
      'Agent mode confirms token then starts and stops the real bridge contract',
      (tester) async {
    final bridge = MockAgentBridge()
      ..connection =
          const AgentConnection('Agent A', 'Xưởng server', 'Tổ chức A');
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);
    await tester.tap(find.widgetWithText(FilledButton, 'Bắt đầu Agent'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
    expect(bridge.connectionCalls, 1);
    expect(bridge.running, isTrue);
    expect(AgentConfig.decode(store.savedRaw!).site, 'Xưởng server');
    await tester.tap(find.widgetWithText(FilledButton, 'Dừng Agent'));
    await tester.pump();
    expect(bridge.running, isFalse);
  });
  testWidgets('renders the Tk window: header, cards, fixture values',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(find.text('BeeSky Agent'), findsOneWidget);
    expect(find.text('Kết nối xưởng với Mine'), findsOneWidget);
    expect(find.text('v$agentAppVersion'), findsOneWidget);
    expect(find.text('Kết nối cloud'), findsOneWidget);
    expect(find.text('Quét tại xưởng'), findsOneWidget);
    expect(find.text('Trạng thái chạy ngầm'), findsOneWidget);

    expect(_field(tester, 0).controller!.text, 'https://mine.beeskybase.com');
    expect(_field(tester, 1).controller!.text, 'demo-agent-key');
    expect(_field(tester, 2).controller!.text, 'Trại Demo');
    expect(_field(tester, 3).controller!.text, '192.168.1.10-192.168.1.60');
    expect(_field(tester, 4).controller!.text, '30');

    // Status card derives from the fixture status (ok, 2 miners).
    expect(find.text('Đã dừng'), findsOneWidget);
    expect(find.textContaining('Vòng quét gần nhất'), findsWidgets);
    // Footer: the loaded-config line, as in Tk.
    expect(find.textContaining('Đã nạp cấu hình.'), findsOneWidget);
    expect(find.text('Chưa chạy thử'), findsNothing);
  });

  testWidgets('save writes the form over the disk base (Tk semantics)',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    bridge.connection =
        const AgentConnection('Agent test', 'Xưởng 9', 'Tổ chức test');
    await tester.tap(find.widgetWithText(OutlinedButton, 'Kiểm tra token'));
    await tester.pump();
    await tester.tap(find.widgetWithText(OutlinedButton, 'Lưu cấu hình'));
    await tester.pump();

    expect(find.textContaining('Đã lưu cấu hình ('), findsOneWidget);
    final saved = AgentConfig.decode(store.savedRaw!);
    expect(saved.site, 'Xưởng 9');
    expect(saved.workers, 32); // unedited field carried through
    expect(saved.key, 'demo-agent-key');
  });

  testWidgets('save refuses missing fields with the core message',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    await tester.enterText(find.byType(TextField).at(1), '');
    await tester.tap(find.widgetWithText(OutlinedButton, 'Lưu cấu hình'));
    await tester.pump();

    expect(find.text('Chưa lưu được — còn thiếu: token, xưởng đã xác nhận'),
        findsOneWidget);
  });

  testWidgets('save refuses a bad interval with the Tk text', (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    await tester.enterText(find.byType(TextField).at(4), 'abc');
    await tester.tap(find.widgetWithText(OutlinedButton, 'Lưu cấu hình'));
    await tester.pump();

    expect(find.text('Nhập số giây lớn hơn 0.'), findsWidgets);
  });

  testWidgets('test cycle runs the bridge and lands the verdict',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    await tester.tap(find.widgetWithText(OutlinedButton, 'Chạy thử'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(bridge.testCalls, 1);
    expect(bridge.lastTestCall!['key'], 'demo-agent-key');
    expect(bridge.lastTestCall!['site'], 'Trại Demo');
    expect(find.text('Chạy thử: OK'), findsOneWidget);
    expect(find.textContaining('đã đẩy snapshot 2 máy'), findsOneWidget);
  });

  testWidgets('protected key: field empty, hint shown, test omits the key',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.protectedKey();
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(_field(tester, 1).controller!.text, '');
    expect(find.textContaining('để trống để giữ nguyên'), findsOneWidget);
    expect(_field(tester, 4).controller!.text, '45');

    await tester.tap(find.widgetWithText(OutlinedButton, 'Chạy thử'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
    expect(bridge.lastTestCall!['key'], isNull);

    // Saving after an unrelated edit keeps the blob AND passes
    // validation (the blob counts as the key being present).
    await tester.enterText(find.byType(TextField).at(3), '192.168.3.0/24');
    await tester.tap(find.widgetWithText(OutlinedButton, 'Lưu cấu hình'));
    await tester.pump();
    final saved = AgentConfig.decode(store.savedRaw!);
    expect(saved.keyProtected, 'QUJDREVGRw==');
    expect(saved.site, 'Trại Demo');
    expect(saved.target, '192.168.3.0/24');
  });

  testWidgets('auto-start toggles through the bridge verbs', (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(tester.widget<Switch>(find.byType(Switch)).value, isFalse);
    await tester.ensureVisible(find.byType(Switch));
    await tester.tap(find.byType(Switch));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(bridge.taskInstalledState, isTrue);
    expect(find.text('Đã bật tự khởi động khi đăng nhập Windows.'),
        findsOneWidget);
    expect(tester.widget<Switch>(find.byType(Switch)).value, isTrue);
  });

  testWidgets('first run: no config -> sysinfo prefill, blank form',
      (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore(); // no fixture: file does not exist
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(_field(tester, 3).controller!.text, '192.168.1.0/24');
    expect(_field(tester, 0).controller!.text, 'https://mine.beeskybase.com');
    expect(find.text('Dán token từ Mine để kết nối xưởng.'), findsOneWidget);
    expect(find.text('Đã dừng'), findsOneWidget);
  });

  testWidgets('Hiện key toggles the key field masking', (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(_field(tester, 1).obscureText, isTrue);
    await tester.tap(find.byTooltip('Hiện token'));
    await tester.pump();
    expect(_field(tester, 1).obscureText, isFalse);
  });

  testWidgets('http cloud URL shows the unencrypted hint live', (tester) async {
    final bridge = MockAgentBridge();
    final store = MockConfigStore.demo();
    await _pumpPage(tester, bridge: bridge, store: store);

    expect(find.textContaining('không mã hoá'), findsNothing);
    await tester.enterText(
        find.byType(TextField).at(0), 'http://cloud.example.com');
    await tester.pump();
    expect(find.textContaining('không mã hoá'), findsOneWidget);
  });
}
