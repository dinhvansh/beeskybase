import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/detail.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.27.0 — device detail tabs (docs/device-detail-mapping.md):
/// the inspect wire models (per-family sections, unsupported
/// markers, the cgminer grade DATA-GAP), the local chart history
/// (append/prune, per-device units, point prep), the notes store,
/// the inspect argv contract, and the tab-level widget behaviour
/// against the mock bridge.

MinerRecord _rec({
  String ip = '10.0.0.1',
  double? rateValue = 100,
  String? rateUnit = 'TH/s',
  double? ths,
  double? maxTempC = 60,
  double? powerW,
  String? mac,
}) =>
    MinerRecord(
      ip: ip,
      model: 'Antminer S19 Pro',
      source: 'vnish',
      chains: const [],
      fansRpm: const [],
      chipsAlive: 0,
      chipsTotal: 0,
      maxTempC: maxTempC,
      issues: const [],
      status: 'OK',
      rateValue: rateValue,
      rateUnit: rateUnit,
      legacyThs: ths,
      mac: mac,
      powerW: powerW,
    );

Directory _tempDir() =>
    Directory.systemTemp.createTempSync('beesky_detail_test_');

void _deleteDir(Directory dir) {
  try {
    dir.deleteSync(recursive: true);
  } on FileSystemException {
    // A temp dir the OS cleans later is not a test failure.
  }
}

void main() {
  group('inspect wire models', () {
    test('vnish document: grade split, pools, fan mode parse', () {
      final doc = InspectResult.fromJson(jsonDecode('''
{"ip": "10.0.0.9", "source": "vnish", "model": "Antminer S19 Pro",
 "cred_label": "VNish trại",
 "boards": {"supported": true, "boards": [
   {"index": 1, "chips_total": 114, "stable": 112, "slow": 1,
    "critical": 1, "dead_positions": [10], "chip_temp_c": 74.0,
    "pcb_temp_c": 62.0, "chips": null}]},
 "pools": {"supported": true, "pools": [
   {"id": 0, "url": "stratum+tcp://p:3333", "user": "w.001",
    "status": "working", "accepted": 10, "rejected": 1,
    "stale": 0, "ping": 42}]},
 "fans": {"supported": true, "mode": "auto", "mode_param": null,
   "duty_pct": 62, "fans": [
     {"id": 1, "rpm": 4320, "status": "ok", "max_rpm": 6000}]}}
''') as Map<String, dynamic>);
      expect(doc.claimed, isTrue);
      expect(doc.credLabel, 'VNish trại');
      final board = doc.boards.boards.single;
      expect(board.hasGrades, isTrue);
      expect((board.stable, board.slow, board.critical), (112, 1, 1));
      expect(board.deadPositions, [10]);
      expect(board.pcbTempC, 62.0);
      expect(doc.pools.pools.single.status, 'working');
      expect(doc.fans.mode, 'auto');
      expect(doc.fans.dutyPct, 62);
      expect(doc.fans.fans.single.status, 'ok');
    });

    test('cgminer document: acs boards carry NO grade buckets', () {
      final doc = InspectResult.fromJson(jsonDecode('''
{"ip": "10.0.0.10", "source": "cgminer", "model": "Antminer L9",
 "cred_label": null,
 "boards": {"supported": true, "boards": [
   {"index": 2, "acs": "oox", "chips_total": 3, "chips_ok": 2,
    "dead_positions": [3], "other_chars": {"x": 1}, "temp_c": 59.0}]},
 "pools": {"supported": false, "reason": "pools command refused"},
 "fans": {"supported": true, "mode": null,
   "fans": [{"id": 1, "rpm": 4560}]}}
''') as Map<String, dynamic>);
      final board = doc.boards.boards.single;
      expect(board.hasGrades, isFalse);
      expect(board.chipsOk, 2);
      expect(board.otherChars, {'x': 1});
      expect(doc.pools.supported, isFalse);
      expect(doc.pools.reason, contains('refused'));
      expect(doc.fans.mode, isNull);
    });

    test('error document + failure factory render as unclaimed', () {
      final doc = InspectResult.fromJson(jsonDecode(
        '{"ip": "10.0.0.11", "source": null, "error": "no miner answered"}',
      ) as Map<String, dynamic>);
      expect(doc.claimed, isFalse);
      expect(doc.error, 'no miner answered');
      expect(doc.boards.supported, isFalse);
      final failed = InspectResult.failure('10.0.0.11', 'boom');
      expect(failed.error, 'boom');
      expect(failed.pools.reason, 'boom');
    });
  });

  group('history', () {
    test('append: keyed by IP, rate in the record native unit', () {
      final history = <String, List<HistorySample>>{};
      appendHistorySample(
        history,
        _rec(ip: '10.0.0.1', rateValue: 14.54, rateUnit: 'MH/s'),
        DateTime(2026, 11, 11, 10),
      );
      final samples = history['10.0.0.1']!;
      expect(samples.single.rateValue, 14.54);
      expect(samples.single.rateUnit, 'MH/s');
    });

    test('append: MAC keys when present; legacy ths reads as TH/s',
        () {
      final history = <String, List<HistorySample>>{};
      appendHistorySample(
        history,
        _rec(ip: '10.0.0.2', rateValue: null, rateUnit: null,
            ths: 99.5, mac: 'AA:BB:CC:DD:EE:FF'),
        DateTime(2026, 11, 11, 10),
      );
      expect(history.keys, ['AA:BB:CC:DD:EE:FF']);
      expect(history.values.single.single.rateValue, 99.5);
      expect(history.values.single.single.rateUnit, 'TH/s');
    });

    test('append: prunes to the per-device cap, oldest first', () {
      final history = <String, List<HistorySample>>{};
      final base = DateTime(2026, 11, 11);
      for (var i = 0; i < historyCapPerDevice + 5; i++) {
        appendHistorySample(
          history,
          _rec(maxTempC: i.toDouble()),
          base.add(Duration(minutes: i)),
        );
      }
      final samples = history['10.0.0.1']!;
      expect(samples.length, historyCapPerDevice);
      expect(samples.first.maxTempC, 5);
      expect(samples.last.maxTempC, historyCapPerDevice + 4);
    });

    test('sample JSON round-trip', () {
      final sample = HistorySample(
        ts: DateTime(2026, 11, 11, 9, 30),
        rateValue: 110.5,
        rateUnit: 'TH/s',
        maxTempC: 65,
        powerW: 3210,
      );
      final back = HistorySample.fromJson(sample.toJson());
      expect(back.ts, sample.ts);
      expect(back.rateValue, 110.5);
      expect(back.rateUnit, 'TH/s');
      expect(back.powerW, 3210);
    });

    test('chart prep: nulls skipped per metric, unit from latest',
        () {
      final t = DateTime(2026, 11, 11, 10);
      final samples = [
        HistorySample(
            ts: t, rateValue: 100, rateUnit: 'TH/s', maxTempC: 60),
        HistorySample(
            ts: t.add(const Duration(minutes: 5)), maxTempC: 61),
        HistorySample(
            ts: t.add(const Duration(minutes: 10)),
            rateValue: 102,
            rateUnit: 'TH/s',
            powerW: 3000),
      ];
      expect(ratePoints(samples).map((p) => p.value), [100, 102]);
      expect(tempPoints(samples).length, 2);
      expect(powerPoints(samples).single.value, 3000);
      expect(rateUnitOf(samples), 'TH/s');
      expect(ratePoints(const []), isEmpty);
      expect(rateUnitOf(const []), isNull);
    });

    test('stores: history + notes round-trip; corrupt reads empty',
        () async {
      final tmp = _tempDir();
      addTearDown(() => _deleteDir(tmp));
      final historyStore =
          HistoryStore(primaryDir: tmp, fallbackDir: tmp);
      final history = <String, List<HistorySample>>{};
      appendHistorySample(history, _rec(powerW: 3100), DateTime(2026));
      await historyStore.save(history);
      final loaded = await historyStore.load();
      expect(loaded['10.0.0.1']!.single.powerW, 3100);

      final noteStore = NoteStore(primaryDir: tmp, fallbackDir: tmp);
      await noteStore.save({'10.0.0.1': 'kiểm tra quạt'});
      expect(await noteStore.load(), {'10.0.0.1': 'kiểm tra quạt'});

      File('${tmp.path}${Platform.pathSeparator}beesky-notes.json')
          .writeAsStringSync('{not json');
      expect(await noteStore.load(), isEmpty);
    });
  });

  group('bridge contract', () {
    test('inspectArgs: ip + paths only, never values', () {
      expect(
        SidecarBridge.inspectArgs('10.0.0.9',
            credsFile: '/tmp/c.json',
            group: 'Trại A',
            groupsFile: '/tmp/g.json'),
        [
          'inspect', '10.0.0.9', '--json',
          '--creds-file', '/tmp/c.json',
          '--group', 'Trại A',
          '--groups-file', '/tmp/g.json',
        ],
      );
      expect(SidecarBridge.inspectArgs('10.0.0.9'),
          ['inspect', '10.0.0.9', '--json']);
    });

    test('MockBridge inspect fixtures honour the family shapes',
        () async {
      final bridge = MockBridge();
      final vnish = await bridge.inspect('192.168.2.101');
      expect(vnish.boards.boards.first.hasGrades, isTrue);
      expect(vnish.fans.mode, 'auto');
      final l9 = await bridge.inspect('192.168.2.102');
      expect(l9.boards.boards.every((b) => !b.hasGrades), isTrue);
      expect(l9.boards.boards[1].deadPositions.length, 39);
      expect(l9.pools.pools.single.status, 'Alive');
      final dead = await bridge.inspect('192.168.2.104');
      expect(dead.claimed, isFalse);
      expect(dead.error, isNotNull);
    });
  });

  group('chart painter data shapes', () {
    testWidgets('single point and flat series paint without error',
        (tester) async {
      final t = DateTime(2026, 11, 11, 10);
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              MiniChart(
                title: 'Hashrate',
                unit: 'TH/s',
                points: [ChartPoint(t, 110)],
                color: Colors.yellow,
              ),
              MiniChart(
                title: 'Nhiệt độ tối đa',
                unit: '°C',
                points: [
                  ChartPoint(t, 60),
                  ChartPoint(t.add(const Duration(minutes: 5)), 60),
                ],
                color: Colors.red,
              ),
            ],
          ),
        ),
      ));
      await tester.pump();
      expect(find.text('110.0 TH/s'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });

  group('detail tabs (widget)', () {
    Future<void> pumpApp(WidgetTester tester, Directory tmp) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: HomePage(
            bridge: MockBridge(),
            credStore: CredStore(primaryDir: tmp, fallbackDir: tmp),
            groupStore: GroupStore(primaryDir: tmp, fallbackDir: tmp),
            historyStore:
                HistoryStore(primaryDir: tmp, fallbackDir: tmp),
            noteStore: NoteStore(primaryDir: tmp, fallbackDir: tmp),
          ),
        ),
      );
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 150)),
      );
      await tester.pump();
      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();
    }

    Future<void> runScan(WidgetTester tester) async {
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
    }

    Future<void> openTab(WidgetTester tester, String name) async {
      await tester.tap(find.text(name).last);
      await tester.pump();
      // The mock inspect answers after 250 ms of fake time; the
      // fetch kicks off from a post-frame callback.
      await tester.pump(const Duration(milliseconds: 350));
      await tester.pumpAndSettle();
    }

    testWidgets(
        'tabs render per section for the vnish S19: pools, fan '
        'mode, board grades, charts', (tester) async {
      final tmp = _tempDir();
      addTearDown(() => _deleteDir(tmp));
      await pumpApp(tester, tmp);
      await runScan(tester);
      // The first row (S19, vnish) is auto-selected; the tab
      // strip is part of its detail panel.
      for (final name in [
        'Số liệu', 'Biểu đồ', 'Board', 'Pools', 'Quạt', 'Ghi chú',
      ]) {
        expect(find.text(name), findsWidgets, reason: 'tab $name');
      }
      await openTab(tester, 'Pools');
      expect(find.text('Pool 1 URL'), findsOneWidget);
      expect(
        find.text('stratum+tcp://pool.example.com:3333'),
        findsOneWidget,
      );
      expect(find.text('mockworker.001'), findsOneWidget);

      await openTab(tester, 'Quạt');
      expect(find.textContaining('auto'), findsWidgets);
      expect(find.textContaining('duty 62%'), findsOneWidget);

      await openTab(tester, 'Board');
      expect(
        find.text('Ổn định 114 · Chậm 0 · Nghiêm trọng 0'),
        findsNWidgets(3),
      );

      await openTab(tester, 'Biểu đồ');
      expect(find.text('Hashrate'), findsWidgets);
      expect(find.text('110.5 TH/s'), findsWidgets);
      expect(find.text('Công suất'), findsOneWidget);
    });

    testWidgets(
        'the cgminer L9: pools render, the Boards tab states the '
        'grade DATA-GAP instead of inventing buckets',
        (tester) async {
      final tmp = _tempDir();
      addTearDown(() => _deleteDir(tmp));
      await pumpApp(tester, tmp);
      await runScan(tester);
      // Select the L9 row (its model cell in the table).
      await tester.tap(find.text('Antminer L9').first);
      await tester.pumpAndSettle();

      await openTab(tester, 'Board');
      expect(find.textContaining('không phân loại chip'), findsOneWidget);
      expect(find.textContaining('Ký tự acs khác: x ×39'), findsOneWidget);
      // No bucket LINE (the gap note itself names the missing
      // buckets in prose — that mention is the honesty, not data).
      expect(find.textContaining('· Chậm'), findsNothing);
      expect(find.textContaining('· Nghiêm trọng'), findsNothing);

      await openTab(tester, 'Quạt');
      expect(
        find.text('— (firmware không báo)'),
        findsOneWidget,
      );
    });

    testWidgets('charts empty state for a device with no samples',
        (tester) async {
      final tmp = _tempDir();
      addTearDown(() => _deleteDir(tmp));
      await pumpApp(tester, tmp);
      await runScan(tester);
      // The unreachable unit: no live record -> no samples.
      await tester.tap(find.text('192.168.2.104').first);
      await tester.pumpAndSettle();
      await openTab(tester, 'Biểu đồ');
      expect(
        find.textContaining('Chưa có dữ liệu biểu đồ'),
        findsOneWidget,
      );
    });

    testWidgets('a note saves and survives a fresh HomePage',
        (tester) async {
      final tmp = _tempDir();
      addTearDown(() => _deleteDir(tmp));
      await pumpApp(tester, tmp);
      await runScan(tester);
      await openTab(tester, 'Ghi chú');
      await tester.enterText(
        find.byType(TextField).last,
        'Quạt 2 kêu to, kiểm tra cuối tuần',
      );
      await tester.tap(find.text('Lưu ghi chú'));
      await tester.pump();
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 150)),
      );
      await tester.pump();

      // A fresh page over the same stores shows the note again.
      await tester.pumpWidget(const SizedBox.shrink());
      await pumpApp(tester, tmp);
      await runScan(tester);
      await openTab(tester, 'Ghi chú');
      expect(
        find.text('Quạt 2 kêu to, kiểm tra cuối tuần'),
        findsOneWidget,
      );
    });
  });
}
