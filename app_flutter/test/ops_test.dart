import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/grid.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/ops.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.26 — the Operations task system (docs/operations-mapping.md):
/// the task model + history store round-trips, the mock bridge's
/// full task lifecycle (progress events, one honest failure, stop
/// accounting), the sidecar argv contract, and the widget flow —
/// selection raises the Operations bar, a confirmed task streams
/// its progress bar, lands in the history dialog with per-device
/// results, and survives a restart (store reload). The export
/// action writes a real file + a history entry.
///
/// v0.29 — the VNish tail (docs/vnish-ops-mapping.md): the new
/// task types round-trip by wire name and all confirm first; the
/// mock fails the dashd-only types honestly on cgminer units
/// while the diagnostic variant succeeds on any answering
/// family; the "Thêm lệnh" menu drives a plain tail action
/// (pause) and a parameterised one (throttle — HashCore's range
/// + default texts) end to end, and the API-key form enforces
/// the api-doc's 32-character key before anything runs.
void main() {
  Directory tempDir() =>
      Directory.systemTemp.createTempSync('beesky_ops');

  void deleteDir(Directory dir) {
    try {
      dir.deleteSync(recursive: true);
    } on Object {
      // best effort cleanup
    }
  }

  OpsTask sampleTask() => OpsTask(
        id: 'ops-1',
        type: OpsTaskType.reboot,
        createdAt: DateTime(2026, 11, 11, 9, 0, 0),
        finishedAt: DateTime(2026, 11, 11, 9, 0, 7),
        status: OpsStatus.hasErrors,
        targets: const ['192.168.2.101', '192.168.2.104'],
        results: const [
          OpsDeviceResult(
            ip: '192.168.2.101',
            ok: true,
            message: 'dashd accepted reboot',
          ),
          OpsDeviceResult(
            ip: '192.168.2.104',
            ok: false,
            message: 'không kết nối được',
          ),
        ],
      );

  group('task model', () {
    test('OpsTask JSON round-trip keeps counts + info text', () {
      final task = sampleTask();
      final back = OpsTask.fromJson(
        jsonDecode(jsonEncode(task.toJson())) as Map<String, dynamic>,
      );
      expect(back.id, task.id);
      expect(back.type, OpsTaskType.reboot);
      expect(back.status, OpsStatus.hasErrors);
      expect(back.total, 2);
      expect(back.completed, 2);
      expect(back.okCount, 1);
      expect(back.failCount, 1);
      expect(back.duration, const Duration(seconds: 7));
      expect(back.infoText(), contains('tổng số máy: 2'));
      expect(back.infoText(), contains('lỗi: 1'));
    });

    test('cancelled results round-trip and count apart', () {
      final task = OpsTask(
        id: 'ops-2',
        type: OpsTaskType.rescan,
        createdAt: DateTime(2026, 11, 11),
        finishedAt: DateTime(2026, 11, 11, 0, 1),
        status: OpsStatus.cancelled,
        targets: const ['10.0.0.1', '10.0.0.2'],
        results: const [
          OpsDeviceResult(
            ip: '10.0.0.2',
            ok: false,
            message: 'Đã hủy trước khi chạy',
            cancelled: true,
          ),
        ],
      );
      final back = OpsTask.fromJson(
        jsonDecode(jsonEncode(task.toJson())) as Map<String, dynamic>,
      );
      expect(back.cancelledCount, 1);
      expect(back.completed, 0);
      expect(back.results.single.cancelled, isTrue);
    });

    test('OpsEvent parses a rescan record; OpsSummary parses counts',
        () {
      final event = OpsEvent.fromJson({
        'event': 'result',
        'done': 1,
        'total': 2,
        'ip': '192.168.2.101',
        'ok': true,
        'message': 'rescanned (vnish)',
        'record': {
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
        },
      });
      expect(event.kind, 'result');
      expect(event.record?.model, 'Antminer S19 Pro');
      final summary = OpsSummary.fromJson({
        'total': 2,
        'completed': 2,
        'ok': 1,
        'failed': 1,
        'cancelled': 0,
        'status': 'hasErrors',
        'elapsed_s': 1.5,
      });
      expect(summary.status, OpsStatus.hasErrors);
      expect(summary.failed, 1);
    });

    test('v0.29 tail types round-trip by wire name and confirm '
        'before running', () {
      for (final type in [
        OpsTaskType.pauseMining,
        OpsTaskType.resumeMining,
        OpsTaskType.restartMining,
        OpsTaskType.findMiner,
        OpsTaskType.throttle,
        OpsTaskType.setPreset,
        OpsTaskType.resetAutotuneAll,
        OpsTaskType.resetAutotuneCurrent,
        OpsTaskType.configureApiKey,
        OpsTaskType.changePassword,
        OpsTaskType.diagnosticReport,
      ]) {
        expect(OpsTaskType.fromWire(type.wire), type);
        expect(type.needsConfirm, isTrue,
            reason: '${type.wire} mutates devices — it must confirm');
      }
      final task = OpsTask(
        id: 'ops-29',
        type: OpsTaskType.throttle,
        createdAt: DateTime(2026, 11, 11),
        finishedAt: DateTime(2026, 11, 11, 0, 0, 3),
        status: OpsStatus.success,
        targets: const ['192.168.2.101'],
        results: const [
          OpsDeviceResult(
            ip: '192.168.2.101',
            ok: true,
            message: 'dashd throttle set to 80%',
          ),
        ],
      );
      final back = OpsTask.fromJson(
        jsonDecode(jsonEncode(task.toJson())) as Map<String, dynamic>,
      );
      expect(back.type, OpsTaskType.throttle);
      expect(back.type.label, 'Giảm công suất');
    });

    test('MinerRecord.toJson round-trips through fromJson', () {
      final rec = MinerRecord.fromJson({
        'ip': '192.168.2.102',
        'model': 'Antminer L9',
        'source': 'cgminer',
        'chains': [
          {'index': 0, 'temp_c': 57.0, 'chips_alive': 84,
           'chips_total': 123},
        ],
        'fans_rpm': [4560],
        'chips_alive': 330,
        'chips_total': 369,
        'max_temp_c': 59.0,
        'problems': [
          {'code': 'MISSING_CHIPS', 'severity': 'warn',
           'detail': 'board 1: 84/123 chip'},
        ],
        'status': 'CHECK',
        'rate_value': 14.54,
        'rate_unit': 'MH/s',
      });
      final back = MinerRecord.fromJson(rec.toJson());
      expect(back.ip, rec.ip);
      expect(back.chains.single.chipsAlive, 84);
      expect(back.issues.single.code, 'MISSING_CHIPS');
      expect(back.rateValue, 14.54);
    });
  });

  group('history store', () {
    test('save + load round-trip; corrupt file reads as empty',
        () async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final store = OpsHistoryStore(primaryDir: tmp, fallbackDir: tmp);
      await store.save([sampleTask()]);
      final file = File(
          '${tmp.path}${Platform.pathSeparator}beesky-ops-history.json');
      expect(file.existsSync(), isTrue);
      final loaded = await store.load();
      expect(loaded, hasLength(1));
      expect(loaded.single.type, OpsTaskType.reboot);
      file.writeAsStringSync('{not json');
      expect(await store.load(), isEmpty);
    });

    test('retention caps at 100 entries (newest kept)', () async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final store = OpsHistoryStore(primaryDir: tmp, fallbackDir: tmp);
      final many = [
        for (var i = 0; i < 105; i++)
          sampleTask().copyWith(
            finishedAt: sampleTask().finishedAt,
          ),
      ];
      // Distinct ids so the cap is observable.
      final withIds = [
        for (var i = 0; i < many.length; i++)
          OpsTask(
            id: 'ops-$i',
            type: many[i].type,
            createdAt: many[i].createdAt,
            finishedAt: many[i].finishedAt,
            status: many[i].status,
            targets: many[i].targets,
            results: many[i].results,
          ),
      ];
      await store.save(withIds);
      final loaded = await store.load();
      expect(loaded, hasLength(100));
      expect(loaded.first.id, 'ops-5');
      expect(loaded.last.id, 'ops-104');
    });
  });

  group('mock bridge lifecycle', () {
    test('reboot over the fleet: events stream, .104 fails, '
        'summary hasErrors', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'reboot',
        'targets': ['192.168.2.101', '192.168.2.102', '192.168.2.104'],
      });
      final events = await run.events.toList();
      final summary = await run.summary;
      expect(events.first.kind, 'start');
      final results = events.where((e) => e.kind == 'result').toList();
      expect(results, hasLength(3));
      expect(results.map((e) => e.done), [1, 2, 3]);
      expect(results.firstWhere((e) => e.ip == '192.168.2.104').ok,
          isFalse);
      expect(summary.ok, 2);
      expect(summary.failed, 1);
      expect(summary.status, OpsStatus.hasErrors);
    });

    test('switch_pool fails honestly on a cgminer source', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'switch_pool',
        'targets': ['192.168.2.101', '192.168.2.102'],
        'payload': {'pool_id': 1},
      });
      final events = await run.events.toList();
      final byIp = {
        for (final e in events.where((e) => e.kind == 'result'))
          e.ip: e,
      };
      expect(byIp['192.168.2.101']?.ok, isTrue); // vnish
      expect(byIp['192.168.2.102']?.ok, isFalse); // cgminer
      expect(byIp['192.168.2.102']?.message, contains('not supported'));
    });

    test('pause_mining: the vnish unit succeeds, cgminer units '
        'fail honestly (dashd-only tail)', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'pause_mining',
        'targets': [
          '192.168.2.101',
          '192.168.2.102',
          '192.168.2.103',
          '192.168.2.104',
        ],
      });
      final events = await run.events.toList();
      final summary = await run.summary;
      final byIp = {
        for (final e in events.where((e) => e.kind == 'result'))
          e.ip: e,
      };
      expect(byIp['192.168.2.101']?.ok, isTrue); // vnish
      expect(byIp['192.168.2.101']?.message,
          contains('mining pause'));
      expect(byIp['192.168.2.102']?.ok, isFalse); // cgminer
      expect(byIp['192.168.2.102']?.message,
          contains('not supported'));
      expect(byIp['192.168.2.104']?.ok, isFalse); // unreachable
      expect(summary.ok, 1);
      expect(summary.status, OpsStatus.hasErrors);
    });

    test('diagnostic_report: answering units of every family '
        'produce a bundle, the dead one fails', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'diagnostic_report',
        'targets': ['192.168.2.101', '192.168.2.102', '192.168.2.104'],
        'payload': {'report_dir': '/mock/reports'},
      });
      final events = await run.events.toList();
      final summary = await run.summary;
      final byIp = {
        for (final e in events.where((e) => e.kind == 'result'))
          e.ip: e,
      };
      expect(byIp['192.168.2.101']?.message,
          contains('192.168.2.101-diagnostic.json'));
      expect(byIp['192.168.2.102']?.ok, isTrue); // cgminer answers
      expect(byIp['192.168.2.104']?.ok, isFalse);
      expect(summary.ok, 2);
    });

    test('find_miner mock reports the locate state', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'find_miner',
        'targets': ['192.168.2.101'],
      });
      final events = await run.events.toList();
      final result = events.singleWhere((e) => e.kind == 'result');
      expect(result.ok, isTrue);
      expect(result.message, contains('locate-miner is ON'));
    });

    test('rescan events carry the fresh fleet records', () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'rescan',
        'targets': ['192.168.2.101'],
      });
      final events = await run.events.toList();
      final result = events.singleWhere((e) => e.kind == 'result');
      expect(result.ok, isTrue);
      expect(result.record?.model, 'Antminer S19 Pro');
    });

    test('stop() accounts the unstarted remainder as cancelled',
        () async {
      final bridge = MockBridge();
      final run = await bridge.startOps({
        'type': 'reboot',
        'targets': [
          '192.168.2.101',
          '192.168.2.102',
          '192.168.2.103',
          '192.168.2.104',
        ],
      });
      final first = await run.events.firstWhere(
        (e) => e.kind == 'result',
      );
      expect(first.done, 1);
      await run.stop();
      final summary = await run.summary;
      expect(summary.status, OpsStatus.cancelled);
      expect(summary.completed + summary.cancelled, summary.total);
      expect(summary.cancelled, greaterThan(0));
    });

    test('sidecar argv contract: job path only, no values', () {
      expect(
        SidecarBridge.opsArgs('/tmp/beesky-ops-job.json'),
        ['ops', '--job', '/tmp/beesky-ops-job.json'],
      );
    });
  });

  group('widget flow', () {
    Future<void> pumpHome(
      WidgetTester tester, {
      required Directory tmp,
    }) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: HomePage(
            bridge: MockBridge(),
            credStore: CredStore(primaryDir: tmp, fallbackDir: tmp),
            groupStore: GroupStore(primaryDir: tmp, fallbackDir: tmp),
            gridStore: GridStore(primaryDir: tmp, fallbackDir: tmp),
            opsStore:
                OpsHistoryStore(primaryDir: tmp, fallbackDir: tmp),
            opsFiles: OpsFiles(primaryDir: tmp, fallbackDir: tmp),
          ),
        ),
      );
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 150)),
      );
      await tester.pump();
      await tester.tap(find.text('Máy đào'));
      await tester.pumpAndSettle();
      // Run the mock scan so the fleet (and the selection bar) exist.
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
    }

    Future<void> selectAll(WidgetTester tester) async {
      await tester.tap(find.text('Chọn tất cả'));
      await tester.pumpAndSettle();
    }

    testWidgets(
        'operations bar appears with selection; a confirmed reboot '
        'streams progress and lands in history with per-device '
        'results', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      expect(find.text('Khởi động lại'), findsNothing);
      await selectAll(tester);
      expect(find.text('Thao tác:'), findsOneWidget);
      expect(find.text('Khởi động lại'), findsOneWidget);
      expect(find.text('Đổi pool'), findsOneWidget);
      expect(find.text('Xuất danh sách'), findsOneWidget);

      await tester.tap(find.text('Khởi động lại'));
      await tester.pumpAndSettle();
      // The "Confirm operation" dialog names the action + count.
      expect(find.text('Xác nhận thao tác — Khởi động lại'),
          findsOneWidget);
      await tester.tap(find.text('Chạy Khởi động lại'));
      await tester.pump();
      // Progress bar: the mock emits every 60 ms; let the run land.
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('địa chỉ'), findsWidgets);
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();
      expect(find.textContaining('Khởi động lại: xong'), findsWidgets);

      // History: the entry is there with its counts, expandable to
      // per-device results (the .104 failure included).
      await tester.tap(find.text('Lịch sử tác vụ'));
      await tester.pumpAndSettle();
      expect(find.text('Lịch sử tác vụ'), findsWidgets);
      expect(find.textContaining('Khởi động lại — Có lỗi'),
          findsOneWidget);
      await tester.tap(find.textContaining('Khởi động lại — Có lỗi'));
      await tester.pumpAndSettle();
      expect(find.text('192.168.2.104'), findsWidgets);
      expect(find.textContaining('không kết nối được'), findsWidgets);
      // The history FILE exists on disk with the entry in it.
      final histFile = File(
          '${tmp.path}${Platform.pathSeparator}beesky-ops-history.json');
      expect(histFile.existsSync(), isTrue);
      final entries =
          jsonDecode(histFile.readAsStringSync()) as List<dynamic>;
      expect(entries, hasLength(1));
      expect((entries.single as Map)['type'], 'reboot');
    });

    testWidgets('history survives a restart: a fresh HomePage with '
        'the same store shows the recorded task', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      // Seed the store as a previous session would have left it.
      final store = OpsHistoryStore(primaryDir: tmp, fallbackDir: tmp);
      await tester.runAsync(() => store.save([sampleTask()]));
      await pumpHome(tester, tmp: tmp);
      await tester.tap(find.text('Lịch sử tác vụ'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Khởi động lại — Có lỗi'),
          findsOneWidget);
      expect(find.textContaining('1 thao tác'), findsOneWidget);
    });

    testWidgets('export writes the selected records file and a '
        'history entry', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await selectAll(tester);
      await tester.tap(find.text('Xuất danh sách'));
      await tester.pumpAndSettle();
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)),
      );
      final exports = tmp
          .listSync()
          .whereType<File>()
          .where((f) => f.path.contains('beesky-export-'))
          .toList();
      expect(exports, hasLength(1));
      final records =
          jsonDecode(exports.single.readAsStringSync()) as List<dynamic>;
      expect(records, hasLength(4));
      await tester.tap(find.text('Lịch sử tác vụ'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Xuất danh sách — Thành công'),
          findsOneWidget);
    });

    testWidgets('Thêm lệnh menu: pause runs through the confirm '
        'and lands in history as a tail task', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await selectAll(tester);
      expect(find.text('Thêm lệnh'), findsOneWidget);
      await tester.tap(find.text('Thêm lệnh'));
      await tester.pumpAndSettle();
      expect(find.text('Tạm dừng đào'), findsOneWidget);
      expect(find.text('Báo cáo chẩn đoán'), findsOneWidget);
      await tester.tap(find.text('Tạm dừng đào'));
      await tester.pumpAndSettle();
      expect(find.text('Xác nhận thao tác — Tạm dừng đào'),
          findsOneWidget);
      await tester.tap(find.text('Chạy Tạm dừng đào'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
      expect(find.textContaining('Tạm dừng đào: xong'), findsWidgets);
      final histFile = File(
          '${tmp.path}${Platform.pathSeparator}beesky-ops-history.json');
      final entries =
          jsonDecode(histFile.readAsStringSync()) as List<dynamic>;
      expect((entries.single as Map)['type'], 'pause_mining');
    });

    testWidgets('throttle dialog shows the documented range and '
        'defaults to 100%, then the task runs', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await selectAll(tester);
      await tester.tap(find.text('Thêm lệnh'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Giảm công suất'));
      await tester.pumpAndSettle();
      // HashCore's dialog texts: range + reset-to-default + 100%.
      expect(find.text('Phạm vi cho phép: 20–100%'), findsOneWidget);
      expect(find.text('Đặt lại mặc định: 100%'), findsOneWidget);
      expect(find.text('100%'), findsOneWidget);
      await tester.tap(find.text('Tiếp tục'));
      await tester.pumpAndSettle();
      expect(find.text('Xác nhận thao tác — Giảm công suất'),
          findsOneWidget);
      await tester.tap(find.text('Chạy Giảm công suất'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
      expect(find.textContaining('Giảm công suất: xong'), findsWidgets);
    });

    testWidgets('api-key dialog refuses a key that is not '
        '32 characters', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await selectAll(tester);
      await tester.tap(find.text('Thêm lệnh'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Cấu hình API key'));
      await tester.pumpAndSettle();
      await tester.enterText(
          find.byType(TextField).first, 'short-key');
      await tester.tap(find.text('Tiếp tục'));
      await tester.pumpAndSettle();
      expect(find.textContaining('phải đúng 32 ký tự'),
          findsOneWidget);
      // The dialog is still open — no task was started.
      expect(find.text('Cấu hình API key (VNish/dashd)'),
          findsOneWidget);
      expect(find.text('Xác nhận thao tác — Cấu hình API key'),
          findsNothing);
    });

    testWidgets('rescan runs without a confirm dialog and refreshes '
        'the fleet', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await selectAll(tester);
      await tester.tap(find.text('Quét lại'));
      await tester.pump();
      expect(find.text('Xác nhận thao tác — Quét lại'), findsNothing);
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pumpAndSettle();
      expect(find.textContaining('Quét lại: xong'), findsWidgets);
    });
  });
}
