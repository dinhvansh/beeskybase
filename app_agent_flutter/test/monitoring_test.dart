import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:beesky_agent_app/agent_bridge.dart';
import 'package:beesky_agent_app/agent_config.dart';
import 'package:beesky_agent_app/main.dart';

class FailingTestBridge extends MockAgentBridge {
  @override
  Future<TestOutcome> testRun(
          {required String configPath,
          required String target,
          required String cloudUrl,
          required String? key,
          required String site,
          required String intervalRaw}) async =>
      throw StateError('fixture');
}

class PendingTaskBridge extends MockAgentBridge {
  final result = Completer<TaskOutcome>();
  int installs = 0;
  @override
  Future<TaskOutcome> installTask(String path) {
    installs++;
    return result.future;
  }
}

void main() {
  Future<void> open(WidgetTester t, MockAgentBridge bridge,
      {Size size = const Size(1100, 900), MockConfigStore? store}) async {
    t.view.physicalSize = size;
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.reset);
    await t.pumpWidget(
        BeeSkyAgentApp(bridge: bridge, store: store ?? MockConfigStore.demo()));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
  }

  testWidgets('running Agent locks configuration and cannot run a second scan',
      (t) async {
    final bridge = MockAgentBridge()..running = true;
    await open(t, bridge);
    for (final field in t.widgetList<TextField>(find.byType(TextField))) {
      expect(field.readOnly, isTrue);
    }
    expect(
        t
            .widget<OutlinedButton>(
                find.widgetWithText(OutlinedButton, 'Lưu cấu hình'))
            .onPressed,
        isNull);
    expect(
        t
            .widget<OutlinedButton>(
                find.widgetWithText(OutlinedButton, 'Chạy thử'))
            .onPressed,
        isNull);
    // Stop never needs a working Cloud or a valid token.
    bridge.connectionError = 'Không có mạng';
    await t.tap(find.text('Dừng Agent'));
    await t.pump();
    expect(bridge.running, isFalse);
    expect(bridge.connectionCalls, 0);
    expect(t.widget<TextField>(find.byType(TextField).first).readOnly, isFalse);
  });

  testWidgets('invalid targets and non-finite intervals never start the engine',
      (t) async {
    final bridge = MockAgentBridge();
    await open(t, bridge);
    await t.enterText(
        find.byType(TextField).at(3), '192.168.1.60-192.168.1.10');
    await t.tap(find.text('Bắt đầu Agent'));
    await t.pump();
    expect(bridge.connectionCalls, 0);
    expect(bridge.running, isFalse);
    expect(find.textContaining('Dải IP chưa hợp lệ'), findsWidgets);
    await t.enterText(find.byType(TextField).at(3), '192.168.1.0/24');
    await t.enterText(find.byType(TextField).at(4), 'NaN');
    await t.tap(find.text('Bắt đầu Agent'));
    await t.pump();
    expect(bridge.connectionCalls, 0);
    expect(bridge.running, isFalse);
    expect(find.text('Nhập số giây lớn hơn 0.'), findsWidgets);
    // Pairing a token is independent of the scan settings.
    await t.tap(find.text('Kiểm tra token'));
    await t.pump();
    expect(bridge.connectionCalls, 1);
    expect(find.textContaining('Đã kết nối:'), findsOneWidget);
  });

  testWidgets('test exceptions restore actions and show a recoverable error',
      (t) async {
    await open(t, FailingTestBridge());
    await t.tap(find.text('Chạy thử'));
    await t.pump();
    await t.pump();
    expect(find.textContaining('Chạy thử chưa hoàn tất'), findsOneWidget);
    expect(
        t.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNotNull);
    expect(
        t
            .widget<OutlinedButton>(
                find.widgetWithText(OutlinedButton, 'Chạy thử'))
            .onPressed,
        isNotNull);
    expect(t.takeException(), isNull);
  });

  testWidgets('startup cannot be submitted twice while Windows is responding',
      (t) async {
    final bridge = PendingTaskBridge();
    await open(t, bridge);
    await t.ensureVisible(find.byType(Switch));
    await t.tap(find.byType(Switch));
    await t.pump();
    await t.pump();
    expect(bridge.installs, 1);
    expect(t.widget<Switch>(find.byType(Switch)).onChanged, isNull);
    expect(t.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNull);
    bridge.taskInstalledState = true;
    bridge.result.complete(const TaskOutcome(true, 'Đã bật tự khởi động.'));
    await t.pump();
    await t.pump();
    expect(t.widget<Switch>(find.byType(Switch)).value, isTrue);
    expect(
        t.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNotNull);
  });

  testWidgets('laptop and narrow layouts retain actions with enlarged text',
      (t) async {
    t.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(t.platformDispatcher.clearTextScaleFactorTestValue);
    for (final size in [
      const Size(1366, 768),
      const Size(1024, 640),
      const Size(640, 720)
    ]) {
      await open(t, MockAgentBridge(), size: size);
      expect(t.takeException(), isNull);
      expect(
          t.getRect(find.text('Bắt đầu Agent')).bottom, lessThan(size.height));
      await t.pumpWidget(const SizedBox.shrink());
    }
  });

  group('honest runtime status', () {
    final now = DateTime(2026, 11, 16, 9);
    AgentStatus cycle(DateTime time, {int count = 2}) => AgentStatus(
        time: time.toString(),
        timestamp: time.millisecondsSinceEpoch / 1000,
        ok: true,
        miners: count,
        error: null,
        cloudUrl: 'https://cloud.invalid',
        site: 'Xưởng 1');
    test('old successful cycle is not the first cycle of a restarted worker',
        () {
      final view = deriveStatusView(
          cycle(now.subtract(const Duration(seconds: 2))),
          running: true,
          now: now,
          startedAt: now);
      expect(view.pillText, 'Đang quét');
      expect(view.tone, 'warn');
    });
    test('stale success does not stay green indefinitely', () {
      final view = deriveStatusView(
          cycle(now.subtract(const Duration(minutes: 8))),
          running: true,
          now: now);
      expect(view.pillText, 'Chưa có dữ liệu mới');
      expect(view.tone, 'warn');
    });
    test('an empty delivered scan is distinct from working miners', () {
      final view =
          deriveStatusView(cycle(now, count: 0), running: true, now: now);
      expect(view.pillText, 'Chưa tìm thấy máy');
      expect(view.tone, 'warn');
    });
    test('a fresh responding scan is healthy', () {
      expect(deriveStatusView(cycle(now), running: true, now: now).tone, 'ok');
    });
  });

  test('scan ranges are validated without expanding huge networks', () {
    for (final input in [
      '192.168.1.1',
      '10.0.0.0/24',
      '10.0.0.1-10.0.0.5,10.0.0.3',
      '10.0.0.0/20,10.0.0.0/20',
      '10.0.0.0/31',
      '10.0.0.1/32'
    ]) {
      expect(validateScanTarget(input), isNull, reason: input);
    }
    for (final input in [
      '',
      '10.0.0.0/0',
      '10.0.0.1/33',
      '999.1.1.1',
      '10.0.0.6-10.0.0.1'
    ]) {
      expect(validateScanTarget(input), isNotNull, reason: input);
    }
  });
}
