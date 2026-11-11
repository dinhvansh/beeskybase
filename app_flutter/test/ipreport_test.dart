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
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.34.0: IP-Report (docs/ipreport-mapping.md) + Settings
/// completion + UI smalls (docs/settings-mapping.md).
///
/// Pure units first (IpReport model, AppSettings round-trip,
/// sidecar arg builders, the mock IP-Report run), then widget
/// tests on the real HomePage with the mock bridge: the IP Report
/// panel, group search + combined mode + reset-statistics, the
/// command palette, and the zoom hotkeys.
void main() {
  Directory tempDir() =>
      Directory.systemTemp.createTempSync('beesky_v34');

  Future<void> pumpHome(
    WidgetTester tester, {
    required BeeSkyBridge bridge,
    required Directory tmp,
    AppSettings? settings,
  }) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final fb = Directory('${tmp.path}/fb')..createSync(recursive: true);
    if (settings != null) {
      SettingsStore(primaryDir: tmp, fallbackDir: fb).save(settings);
    }
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

  group('IpReport model', () {
    test('round-trips; targetIp falls back to sender', () {
      const r = IpReport(
        receivedAt: 1793123456.0,
        sender: '192.168.2.105',
        text: '',
        ip: null,
        mac: null,
        family: 'whatsminer',
      );
      final back = IpReport.fromJson(r.toJson());
      expect(back.targetIp, '192.168.2.105');
      expect(back.familyLabel, 'Whatsminer');
      expect(back.whenText, isNotEmpty);
      const claimed = IpReport(
        receivedAt: 1793123456.0,
        sender: '192.168.2.101',
        text: '192.168.2.101,AA:BB:CC:DD:EE:01',
        ip: '192.168.2.101',
        mac: 'AA:BB:CC:DD:EE:01',
        family: 'antminer',
      );
      expect(claimed.targetIp, '192.168.2.101');
      expect(claimed.familyLabel, 'Antminer');
      expect(
        IpReport.fromJson(claimed.toJson()).mac,
        'AA:BB:CC:DD:EE:01',
      );
    });
  });

  group('AppSettings (v0.34 fields)', () {
    test('round-trips every new field', () {
      final tmp = tempDir();
      final store = SettingsStore(
        primaryDir: tmp,
        fallbackDir: Directory('${tmp.path}/fb'),
      );
      store.save(const AppSettings(
        defaultTarget: '10.0.0.0/24',
        priceVndKwh: 1750,
        probeTimeoutS: 2.5,
        requestTimeoutS: 5,
        opsStaggerS: 0.5,
        scanWorkers: 32,
        opsWorkers: 2,
        scale: 1.15,
        ipReportEnabled: true,
      ));
      final back = store.load();
      expect(back.defaultTarget, '10.0.0.0/24');
      expect(back.priceVndKwh, 1750);
      expect(back.probeTimeoutS, 2.5);
      expect(back.requestTimeoutS, 5);
      expect(back.opsStaggerS, 0.5);
      expect(back.scanWorkers, 32);
      expect(back.opsWorkers, 2);
      expect(back.scale, 1.15);
      expect(back.ipReportEnabled, isTrue);
    });

    test('a v0.32 file loads with the new defaults', () {
      final s = AppSettings.fromJson({
        'default_target': '192.168.2.0/24',
        'price_vnd_kwh': 2000,
      });
      expect(s.probeTimeoutS, 1.5);
      expect(s.requestTimeoutS, 3.0);
      expect(s.opsStaggerS, 0.0);
      expect(s.scanWorkers, 64);
      expect(s.opsWorkers, 4);
      expect(s.scale, 1.0);
      expect(s.ipReportEnabled, isFalse);
    });

    test('copyWith changes one field, keeps the rest', () {
      const s = AppSettings(scale: 1.0, probeTimeoutS: 1.5);
      final next = s.copyWith(scale: 1.1);
      expect(next.scale, 1.1);
      expect(next.probeTimeoutS, 1.5);
    });
  });

  group('sidecar arg builders (v0.34)', () {
    test('scan args carry timeout + workers only when given', () {
      expect(
        SidecarBridge.scanArgs('192.168.2.0/24'),
        ['scan', '192.168.2.0/24', '--json'],
      );
      expect(
        SidecarBridge.scanArgs('192.168.2.0/24',
            timeout: 2.5, workers: 32),
        [
          'scan',
          '192.168.2.0/24',
          '--json',
          '--timeout',
          '2.5',
          '--workers',
          '32',
        ],
      );
      expect(
        SidecarBridge.scanGroupArgs('Trại chính',
            timeout: 1.5, workers: 64),
        [
          'scan',
          '--group',
          'Trại chính',
          '--json',
          '--timeout',
          '1.5',
          '--workers',
          '64',
        ],
      );
      expect(
        SidecarBridge.inspectArgs('192.168.2.101', timeout: 4.0),
        ['inspect', '192.168.2.101', '--json', '--timeout', '4.0'],
      );
    });

    test('ipreport args are the documented verbs', () {
      expect(
        SidecarBridge.ipReportArgs('/tmp/beesky-ipreports.json'),
        ['ipreport', 'listen', '--out', '/tmp/beesky-ipreports.json'],
      );
      expect(
        SidecarBridge.listIpReportsArgs('/tmp/beesky-ipreports.json'),
        [
          'ipreport',
          'list',
          '--file',
          '/tmp/beesky-ipreports.json',
          '--json',
        ],
      );
    });

    test('mock bridge lists the canned reports + streams them', () async {
      final bridge = MockBridge();
      final listed = await bridge.listIpReports();
      expect(listed.length, 2);
      expect(listed.first.targetIp, '192.168.2.101');
      expect(listed.last.family, 'whatsminer');
      final run = await bridge.startIpReport();
      final got = await run.reports.take(2).toList();
      expect(got.length, 2);
      await run.stop();
    });
  });

  group('SettingsView (5 tabs)', () {
    Future<AppSettings? Function()> pumpSettings(
      WidgetTester tester, {
      AppSettings settings = const AppSettings(),
    }) async {
      AppSettings? saved;
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: Scaffold(
            body: SettingsView(
              settings: settings,
              onSave: (s) => saved = s,
              credCount: 3,
              onOpenCreds: () {},
              onOpenGroups: () {},
              ticketsDir: '(mock) tickets',
              coreVersion: '0.35.0',
              sidecarMissing: false,
              dataDir: '(mock) data',
              storeFiles: const [
                StoreFileInfo('Nhóm mạng', 128),
                StoreFileInfo('IP Report', null),
              ],
              onClearOpsHistory: () {},
              onClearEvents: () {},
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      return () => saved;
    }

    testWidgets('all five tabs exist; timeouts save through',
        (tester) async {
      final getSaved = await pumpSettings(tester);
      expect(find.text('Chung'), findsOneWidget);
      expect(find.text('Tài khoản'), findsOneWidget);
      expect(find.text('Thời gian chờ'), findsOneWidget);
      expect(find.text('Nhật ký'), findsOneWidget);
      expect(find.text('Nâng cao'), findsOneWidget);

      await tester.tap(find.text('Thời gian chờ'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Probe timeout'), findsOneWidget);
      await tester.enterText(
        find.byType(TextField).at(0),
        '2.5',
      );
      await tester.tap(find.text('Lưu cài đặt'));
      await tester.pumpAndSettle();
      final saved = getSaved();
      expect(saved, isNotNull);
      expect(saved!.probeTimeoutS, 2.5);
      expect(saved.priceVndKwh, 2000); // untouched tabs keep values
    });

    testWidgets('scale stepper moves 100% -> 105%; IP Report switch '
        'saves enabled', (tester) async {
      final getSaved = await pumpSettings(tester);
      expect(find.text('100%'), findsOneWidget);
      await tester.tap(find.byIcon(Icons.add).first);
      await tester.pumpAndSettle();
      expect(find.text('105%'), findsOneWidget);
      await tester.tap(find.byType(Switch));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Lưu cài đặt'));
      await tester.pumpAndSettle();
      final saved = getSaved();
      expect(saved, isNotNull);
      expect(saved!.scale, 1.05);
      expect(saved.ipReportEnabled, isTrue);
    });

    testWidgets('an out-of-range timeout is refused with an error',
        (tester) async {
      final getSaved = await pumpSettings(tester);
      await tester.tap(find.text('Thời gian chờ'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextField).at(0),
        '99',
      );
      await tester.tap(find.text('Lưu cài đặt'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Probe timeout phải'), findsOneWidget);
      expect(getSaved(), isNull);
    });

    testWidgets('logs tab shows the store files + sizes', (tester) async {
      await pumpSettings(tester);
      await tester.tap(find.text('Nhật ký'));
      await tester.pumpAndSettle();
      expect(find.text('Nhóm mạng'), findsOneWidget);
      expect(find.text('128 B'), findsOneWidget);
      expect(find.text('chưa có file'), findsOneWidget);
      expect(find.text('Xóa lịch sử thao tác'), findsOneWidget);
      expect(find.text('Xóa nhật ký sự kiện'), findsOneWidget);
    });
  });

  group('groups screen smalls (mock bridge)', () {
    testWidgets('search filters by name; reset-stats restores the MỚI tag',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      // Demo groups: Trại chính (scanned) + Kho phụ (never scanned).
      expect(find.text('Trại chính'), findsOneWidget);
      expect(find.text('Kho phụ'), findsOneWidget);
      await tester.enterText(
        find.byType(TextField).first,
        'kho',
      );
      await tester.pumpAndSettle();
      expect(find.text('Trại chính'), findsNothing);
      expect(find.text('Kho phụ'), findsOneWidget);
      await tester.enterText(
        find.byType(TextField).first,
        '',
      );
      await tester.pumpAndSettle();
      expect(find.text('Trại chính'), findsOneWidget);

      // Reset statistics on the scanned group: its last-scan line
      // becomes "Chưa quét" and the MỚI tag returns.
      expect(find.text('Đặt lại'), findsOneWidget);
      await tester.tap(find.text('Đặt lại'));
      await tester.pumpAndSettle();
      expect(find.text('Chưa quét'), findsWidgets);
    });

    testWidgets('combined mode shows one union card; Quét gộp scans it',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await tester.tap(find.text('Xem gộp'));
      await tester.pumpAndSettle();
      expect(find.text('Tất cả nhóm'), findsOneWidget);
      expect(find.text('Quét gộp'), findsOneWidget);
      expect(find.text('Trại chính'), findsNothing);
      await tester.tap(find.text('Quét gộp'));
      await tester.pumpAndSettle();
      // The union scan lands on the miners view (mock fleet).
      expect(find.text('Máy đào'), findsWidgets);
      expect(find.text('192.168.2.101'), findsWidgets);
    });
  });

  group('IP Report panel (mock bridge)', () {
    testWidgets('persisted reports show; toggle starts the listener',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      expect(find.text('IP Report'), findsOneWidget);
      // Persisted (mock) reports load at startup.
      expect(find.textContaining('192.168.2.101'), findsWidgets);
      expect(find.textContaining('Whatsminer'), findsWidgets);
      expect(find.textContaining('IP Report đang tắt'), findsOneWidget);
      // Toggle on: the listener starts (mock run streams the same
      // canned reports again — no duplicates by target IP).
      await tester.tap(find.byType(Switch).last);
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pumpAndSettle();
      expect(find.textContaining('Đang nghe IP Report'), findsOneWidget);
      expect(find.textContaining('192.168.2.101'), findsWidgets);
    });

    testWidgets('a report opens as a group named after its IP',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(
        tester,
        bridge: MockBridge(),
        tmp: tmp,
        settings: const AppSettings(ipReportEnabled: true),
      );
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pumpAndSettle();
      expect(find.text('Mở thành nhóm'), findsWidgets);
      // Newest report first: the Whatsminer (105) row is on top,
      // the Antminer (101) row is last.
      await tester.tap(find.text('Mở thành nhóm').last);
      await tester.pumpAndSettle();
      expect(find.text('IP Report 192.168.2.101'), findsOneWidget);
    });
  });

  group('command palette + zoom hotkeys (mock bridge)', () {
    Future<void> sendCtrl(WidgetTester tester, LogicalKeyboardKey key) async {
      await tester.sendKeyDownEvent(LogicalKeyboardKey.control);
      await tester.sendKeyEvent(key);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.control);
      await tester.pumpAndSettle();
    }

    testWidgets('Ctrl+K opens the palette; picking Cài đặt opens it',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await sendCtrl(tester, LogicalKeyboardKey.keyK);
      expect(find.text('Gõ lệnh…'), findsOneWidget);
      expect(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.text('Quét tất cả nhóm'),
        ),
        findsOneWidget,
      );
      await tester.enterText(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextField),
        ),
        'Cài đặt',
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Mở Cài đặt'));
      await tester.pumpAndSettle();
      expect(find.text('Chung'), findsOneWidget);
    });

    testWidgets('Ctrl+= zooms to 105% (shown in Cài đặt)',
        (tester) async {
      final tmp = tempDir();
      await pumpHome(tester, bridge: MockBridge(), tmp: tmp);
      await sendCtrl(tester, LogicalKeyboardKey.equal);
      await tester.tap(find.text('Cài đặt'));
      await tester.pumpAndSettle();
      expect(find.text('105%'), findsOneWidget);
    });
  });

  group('MinerRecord group decoration', () {
    test('withGroup keeps every field, sets the group name', () {
      final rec = MinerRecord.fromJson({
        'ip': '192.168.2.101',
        'model': 'Antminer S19 Pro',
        'source': 'vnish',
        'chains': [],
        'fans_rpm': [],
        'chips_alive': 342,
        'chips_total': 342,
        'max_temp_c': 65.0,
        'problems': [],
        'status': 'OK',
        'rate_value': 110.5,
        'rate_unit': 'TH/s',
        'ths': 110.5,
      });
      final decorated = rec.withGroup('Trại chính');
      expect(decorated.groupName, 'Trại chính');
      expect(decorated.ip, '192.168.2.101');
      expect(decorated.rateValue, 110.5);
      expect(decorated.toJson().containsKey('groupName'), isFalse);
    });
  });
}
