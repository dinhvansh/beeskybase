import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/detail.dart';
import 'package:beesky_app/grid.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/ops.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:beesky_app/views.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.32.0: the five views + the sidecar-missing failure mode.
///
/// The views render from the mock bridge / fixtures exactly the
/// way the app runs them; the sidecar tests point a REAL
/// SidecarBridge at a path that does not exist — the owner's
/// 2026-11-12 standalone-zip layout — and pin the ONE friendly
/// message on every surface (never a raw ProcessException).
/// Every HomePage pump wires ALL stores at a fresh temp dir, so
/// no test can see another test's persisted state.
void main() {
  Directory tempDir() => Directory.systemTemp.createTempSync('beesky_v32');

  Future<void> pumpHome(
    WidgetTester tester, {
    required BeeSkyBridge bridge,
    required Directory tmp,
  }) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final fb = Directory('${tmp.path}/fb')..createSync(recursive: true);
    await tester.pumpWidget(
      MaterialApp(
        theme: buildBeeSkyTheme(),
        home: HomePage(
          bridge: bridge,
          credStore: CredStore(primaryDir: tmp, fallbackDir: fb),
          groupStore: GroupStore(primaryDir: tmp, fallbackDir: fb),
          gridStore: GridStore(primaryDir: tmp, fallbackDir: fb),
          opsStore: OpsHistoryStore(primaryDir: tmp, fallbackDir: fb),
          opsFiles: OpsFiles(primaryDir: tmp, fallbackDir: fb),
          historyStore: HistoryStore(primaryDir: tmp, fallbackDir: fb),
          noteStore: NoteStore(primaryDir: tmp, fallbackDir: fb),
          settingsStore: SettingsStore(primaryDir: tmp, fallbackDir: fb),
          eventStore: EventLogStore(primaryDir: tmp, fallbackDir: fb),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  group('sidecar resolution (Workstream B)', () {
    test('a missing sibling is KNOWN missing, and every verb says '
        'the one friendly message', () async {
      final tmp = tempDir();
      final missing = '${tmp.path}${Platform.pathSeparator}nope'
          '${Platform.pathSeparator}beesky.exe';
      final bridge = SidecarBridge(exePath: missing);
      expect(bridge.sidecarMissing, isTrue);
      expect(bridge.ticketsDirPath, contains('tickets'));

      for (final call in <Future<dynamic> Function()>[
        bridge.sysinfo,
        () => bridge.scan('192.168.1.0/24'),
        () => bridge.scanGroup('Trại chính'),
        () => bridge.exportTickets('192.168.1.0/24'),
        () => bridge.listTickets(tmp.path),
        () => bridge.inspect('192.168.1.10'),
      ]) {
        await expectLater(
          call(),
          throwsA(isA<SidecarException>().having(
            (e) => e.message,
            'message',
            missingSidecarMessage,
          )),
        );
      }
    });

    test('an existing exe path is not missing', () {
      final tmp = tempDir();
      final exe = File('${tmp.path}${Platform.pathSeparator}beesky.exe')
        ..writeAsStringSync('not really an exe');
      final bridge = SidecarBridge(exePath: exe.path);
      expect(bridge.sidecarMissing, isFalse);
    });

    test('scan args carry the events-state path only when given', () {
      expect(SidecarBridge.scanArgs('10.0.0.0/24'),
          ['scan', '10.0.0.0/24', '--json']);
      expect(
        SidecarBridge.scanArgs('10.0.0.0/24', eventsState: '/tmp/st.json'),
        ['scan', '10.0.0.0/24', '--json', '--events-state', '/tmp/st.json'],
      );
      expect(SidecarBridge.listTicketsArgs('/tmp/t'),
          ['tickets', '--dir', '/tmp/t', '--json']);
    });
  });

  group('pure view helpers', () {
    test('heat bands match the web dashboard hexes + thresholds', () {
      expect(heatBandColor(null), const Color(0xFF2C2C2C));
      expect(heatBandColor(59.9), const Color(0xFF14532D));
      expect(heatBandColor(60), const Color(0xFF4A5D23));
      expect(heatBandColor(75), const Color(0xFF7A5A12));
      expect(heatBandColor(85), const Color(0xFF8A4512));
      expect(heatBandColor(90), const Color(0xFF8A1F1A));
    });

    test('compareIp orders numerically, not lexically', () {
      final ips = ['192.168.2.103', '192.168.2.99', '192.168.2.101']
        ..sort(compareIp);
      expect(ips, ['192.168.2.99', '192.168.2.101', '192.168.2.103']);
    });

    test('fleet power counts only reporting miners', () {
      MinerRecord rec(double? w) => MinerRecord(
            ip: '10.0.0.1',
            model: 'M',
            source: 'vnish',
            chains: const [],
            fansRpm: const [],
            chipsAlive: 0,
            chipsTotal: 0,
            maxTempC: 60,
            issues: const [],
            status: 'OK',
            rateValue: 100,
            rateUnit: 'TH/s',
            legacyThs: 100,
            powerW: w,
          );
      final fleet = fleetPower([rec(3200), rec(null), rec(1800)]);
      expect(fleet.totalW, 5000);
      expect(fleet.reporting, 2);
      expect(fleet.total, 3);
      expect(fleet.kwhPerDay, closeTo(120, 0.001));
    });

    test('energy integration: rectangle rule, gap skip, window', () {
      HistorySample s(DateTime t, double? w) =>
          HistorySample(ts: t, powerW: w);
      final now = DateTime(2026, 11, 12, 12, 0);
      final history = {
        // 3000 W for 10 min = 0.5 kWh; the next sample is 110 min
        // later (gap — skipped) and carries no power anyway.
        '10.0.0.1': [
          s(now.subtract(const Duration(minutes: 20)), 3000),
          s(now.subtract(const Duration(minutes: 10)), 3000),
          s(now.add(const Duration(minutes: 100)), null),
        ],
        // Outside the 7-day window: contributes nothing.
        '10.0.0.2': [
          s(now.subtract(const Duration(days: 9)), 5000),
          s(now.subtract(const Duration(days: 9, minutes: -10)), 5000),
        ],
      };
      final e = integrateEnergy(history, now: now);
      expect(e.totalKwh, closeTo(0.5, 0.001));
      expect(e.perDevice['10.0.0.1'], closeTo(0.5, 0.001));
      expect(e.perDevice.containsKey('10.0.0.2'), isFalse);
      expect(e.perDay[dayKeyOf(now)], closeTo(0.5, 0.001));
    });

    test('formatVnd groups thousands with dots', () {
      expect(formatVnd(0), '0 ₫');
      expect(formatVnd(2000), '2.000 ₫');
      expect(formatVnd(153600), '153.600 ₫');
    });

    test('settings store round-trips + defaults', () {
      final tmp = tempDir();
      final store = SettingsStore(
        primaryDir: tmp,
        fallbackDir: Directory('${tmp.path}/fb'),
      );
      expect(store.load().priceVndKwh, 2000);
      expect(store.load().defaultTarget, '');
      store.save(const AppSettings(
          defaultTarget: '10.0.0.0/24', priceVndKwh: 1750));
      final back = store.load();
      expect(back.defaultTarget, '10.0.0.0/24');
      expect(back.priceVndKwh, 1750);
    });

    test('event log store round-trips + per-target state paths differ',
        () {
      final tmp = tempDir();
      final store = EventLogStore(
        primaryDir: tmp,
        fallbackDir: Directory('${tmp.path}/fb'),
      );
      expect(store.load(), isEmpty);
      store.save(const [
        FleetEvent(
          ts: 1,
          time: '2026-11-12 07:00:00',
          ip: '10.0.0.9',
          model: 'Antminer S19 Pro',
          source: 'vnish',
          type: 'OFFLINE',
          severity: 'critical',
          detail: 'gone',
        ),
      ]);
      final back = store.load();
      expect(back.single.type, 'OFFLINE');
      expect(back.single.typeLabel, 'Mất kết nối');
      expect(back.single.severityLabel, 'Khẩn cấp');
      final a = store.stateFilePathFor('192.168.1.0/24');
      final b = store.stateFilePathFor('192.168.2.0/24');
      expect(a, isNot(b));
      expect(store.stateFilePathFor('192.168.1.0/24'), a);
    });
  });

  group('the five views (mock bridge)', () {
    testWidgets('sidebar has no SAU; heat map draws the fleet',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      expect(find.text('SAU'), findsNothing);

      // Scan first (the heat map draws the CURRENT records).
      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Bản đồ nhiệt'));
      await tester.pumpAndSettle();
      // Octet tiles: 101 (S19, 65°C max), 103 (Z15, offline).
      expect(find.text('101'), findsOneWidget);
      expect(find.text('103'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
      expect(find.text('65°C'), findsOneWidget);
    });

    testWidgets('energy view shows fleet + history sections',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await tester.tap(find.text('Điện năng'));
      await tester.pumpAndSettle();
      // The mock seeds demo history with power samples, so the
      // history section has content even before any scan.
      expect(find.textContaining('7 ngày qua'), findsOneWidget);
      expect(find.textContaining('Phạm vi:'), findsOneWidget);
      expect(find.textContaining('/kWh'), findsWidgets);
    });

    testWidgets('repairs view lists the mock tickets + opens detail',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await tester.tap(find.text('Lịch sử sửa'));
      await tester.pumpAndSettle();
      expect(find.text('192.168.2.103'), findsOneWidget);
      expect(find.text('Antminer Z15'), findsOneWidget);
      expect(find.textContaining('1 vấn đề'), findsWidgets);
      await tester.tap(find.text('192.168.2.103'));
      await tester.pumpAndSettle();
      expect(find.textContaining('PHIẾU KIỂM TRA'), findsWidgets);
      await tester.tap(find.text('Đóng'));
      await tester.pumpAndSettle();
    });

    testWidgets('events view: empty first, the scan diff lands after',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await tester.tap(find.text('Sự kiện'));
      await tester.pumpAndSettle();
      expect(find.text('Chưa có sự kiện nào'), findsOneWidget);

      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Sự kiện'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Quá nhiệt'), findsWidgets);
      expect(find.textContaining('Mất chip'), findsWidgets);
    });

    testWidgets('settings view persists target + price', (tester) async {
      final tmp = tempDir();
      final fb = Directory('${tmp.path}/fb')..createSync(recursive: true);
      final store = SettingsStore(primaryDir: tmp, fallbackDir: fb);
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: HomePage(
            bridge: MockBridge(),
            credStore: CredStore(primaryDir: tmp, fallbackDir: fb),
            groupStore: GroupStore(primaryDir: tmp, fallbackDir: fb),
            gridStore: GridStore(primaryDir: tmp, fallbackDir: fb),
            opsStore: OpsHistoryStore(primaryDir: tmp, fallbackDir: fb),
            opsFiles: OpsFiles(primaryDir: tmp, fallbackDir: fb),
            historyStore: HistoryStore(primaryDir: tmp, fallbackDir: fb),
            noteStore: NoteStore(primaryDir: tmp, fallbackDir: fb),
            settingsStore: store,
            eventStore: EventLogStore(primaryDir: tmp, fallbackDir: fb),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Cài đặt'));
      await tester.pumpAndSettle();
      expect(find.text('BeeSky v0.38.0'), findsWidgets);
      // The credential count lives on the Tài khoản tab now.
      await tester.tap(find.text('Tài khoản'));
      await tester.pumpAndSettle();
      expect(find.textContaining('bộ đã lưu'), findsOneWidget);
      await tester.tap(find.text('Chung'));
      await tester.pumpAndSettle();

      // On the Chung tab the only TextFields in the tree are
      // the two form fields (target, then price).
      final fields = find.byType(TextField);
      await tester.enterText(fields.at(0), '10.9.0.0/24');
      await tester.enterText(fields.at(1), '1750');
      await tester.tap(find.text('Lưu cài đặt'));
      await tester.pumpAndSettle();

      final saved = store.load();
      expect(saved.defaultTarget, '10.9.0.0/24');
      expect(saved.priceVndKwh, 1750);
      expect(find.text('Đã lưu cài đặt.'), findsOneWidget);

      // The price takes effect in Điện năng.
      await tester.tap(find.text('Điện năng'));
      await tester.pumpAndSettle();
      expect(find.textContaining('1.750 ₫'), findsWidgets);
    });
  });

  group('missing sidecar in the real shell', () {
    testWidgets('pill + status show the friendly state, no raw text',
        (tester) async {
      final tmp = tempDir();
      final missing = '${tmp.path}${Platform.pathSeparator}bundle'
          '${Platform.pathSeparator}beesky.exe';
      final bridge = SidecarBridge(exePath: missing);
      await pumpHome(tester, bridge: bridge, tmp: tmp);

      expect(find.text('Chưa có ruột quét (thiếu beesky.exe)'),
          findsOneWidget);
      expect(find.text(missingSidecarMessage), findsWidgets);
      expect(find.textContaining('ProcessException'), findsNothing);
      expect(find.textContaining('cannot find the file'), findsNothing);

      // A scan attempt surfaces the same message, not an exception.
      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Quét ngay').first);
      await tester.pumpAndSettle();
      expect(find.textContaining('Không tìm thấy beesky.exe cạnh app'),
          findsWidgets);
      expect(find.textContaining('ProcessException'), findsNothing);
    });
  });
}
