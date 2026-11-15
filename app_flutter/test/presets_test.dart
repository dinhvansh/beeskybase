import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/detail.dart';
import 'package:beesky_app/grid.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/ops.dart';
import 'package:beesky_app/presets.dart';
import 'package:beesky_app/presets_dialogs.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.28 — pool presets + clone + enrichment + stretch
/// (docs/presets-ipreport-mapping.md): the Dart pattern
/// expander pinned to the SAME case table as the Python core
/// suite (tests/mock_pools_test.py — any change must land in
/// both), preset JSON round-trips through the grid store,
/// the Presets center + editor validation, the apply/clone
/// widget flows against the mock bridge, the enrichment
/// rendering (record pools light up the Pools view + the
/// detail Pools tab), the note column decoration, and the
/// group-merge semantics + "Lưu & quét".
void main() {
  Directory tempDir() =>
      Directory.systemTemp.createTempSync('beesky_presets');

  void deleteDir(Directory dir) {
    try {
      dir.deleteSync(recursive: true);
    } on Object {
      // best effort cleanup
    }
  }

  group('worker patterns — the shared case table', () {
    const ctx = PatternContext(
      ip: '192.168.2.101',
      index: 2,
      currentUser: 'acct.w1',
      currentUrl: 'stratum+tcp://pool.example.com:3333',
    );

    test('expansions match the Python table exactly', () {
      String e(String t, [PatternContext c = ctx]) =>
          expandWorkerPattern(t, c);
      expect(e('farm.worker-7'), 'farm.worker-7');
      expect(e('{account}'), 'acct');
      expect(e('{worker}'), 'w1');
      expect(e('{account}.{worker}'), 'acct.w1');
      const nodot = PatternContext(ip: '10.0.0.1', currentUser: 'solo');
      expect(e('{account}|{worker}', nodot), 'solo|');
      expect(e('{ip:.}/{ip1}.{ip2}.{ip3}.{ip4}'),
          '192.168.2.101/192.168.2.101');
      expect(e('w-{ip4}'), 'w-101');
      expect(e('{n}'), '3');
      expect(e('{nn}/{nnn}'), '03/003');
      expect(e('{n:10:5}'), '20');
      expect(e('{n}', const PatternContext(ip: '10.0.0.1')), '1');
      expect(e('{proto-str}://{pool-host}:{port}'),
          'stratum+tcp://pool.example.com:3333');
      expect(e('w{'), 'w{');
      // {n} ordering across the target list: index drives it.
      expect(e('farm.{nn}', const PatternContext(ip: '10.0.0.1', index: 0)),
          'farm.01');
      expect(e('farm.{nn}', const PatternContext(ip: '10.0.0.2', index: 1)),
          'farm.02');
    });

    test('failures raise PatternException, never a guess', () {
      const bare = PatternContext(ip: '10.0.0.9');
      expect(
        () => expandWorkerPattern('{account}', bare),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message',
                contains('current pool worker'))),
      );
      expect(
        () => expandWorkerPattern('{pool-host}', bare),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message', contains('current pool'))),
      );
      expect(
        () => expandWorkerPattern('{mac}', ctx),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message', contains('MAC address'))),
      );
      expect(
        () => expandWorkerPattern('{host}', ctx),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message', contains('hostname'))),
      );
      expect(
        () => expandWorkerPattern('{bogus}', ctx),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message', contains('unknown pattern'))),
      );
      expect(
        () => expandWorkerPattern('{n:x}', ctx),
        throwsA(isA<PatternException>()
            .having((e) => e.message, 'message', contains('integers'))),
      );
    });

    test('patternNeedsCurrentPool classification matches the core', () {
      expect(patternNeedsCurrentPool('w.{account}'), isTrue);
      expect(patternNeedsCurrentPool('w.{n}-{ip4}'), isFalse);
      expect(patternNeedsCurrentPool('plain'), isFalse);
    });
  });

  group('pool preset store', () {
    PoolPreset sample() => PoolPreset(
          name: 'Trại A',
          description: 'pool chính + dự phòng',
          slots: [
            PoolSlot(
              url: 'stratum+tcp://pool.example.com:3333',
              worker: '{account}.{nn}',
              password: 'x',
            ),
            PoolSlot(
              url: 'stratum+tcp://backup.example.com:3333',
              worker: 'farm.{ip4}',
            ),
          ],
        );

    test('GridConfig JSON round-trip keeps pool_presets', () {
      final cfg = GridConfig()..poolPresets = [sample()];
      final doc = jsonDecode(jsonEncode(cfg.toJson()))
          as Map<String, dynamic>;
      expect(doc.containsKey('pool_presets'), isTrue);
      final back = GridConfig.fromJson(doc);
      expect(back.poolPresets, hasLength(1));
      final p = back.poolPresets.single;
      expect(p.name, 'Trại A');
      expect(p.description, 'pool chính + dự phòng');
      expect(p.slots, hasLength(2));
      expect(p.slots[0].worker, '{account}.{nn}');
      expect(p.slots[0].password, 'x');
      expect(p.slots[1].password, '');
    });

    test('empty slots are dropped; the job form omits empty passwords',
        () {
      final p = PoolPreset(name: 'M', slots: [
        PoolSlot(url: 'u1', worker: 'w1'),
        PoolSlot(), // editor artefact — never stored
        PoolSlot(url: 'u3', worker: 'w3', password: 'pw'),
      ]);
      expect(p.activeSlots, hasLength(2));
      expect(p.toJson()['slots'], hasLength(2));
      final job = p.activeSlots.map((s) => s.toJobJson()).toList();
      expect(job[0], {'url': 'u1', 'user': 'w1'});
      expect(job[1], {'url': 'u3', 'user': 'w3', 'password': 'pw'});
    });

    test('GridStore persists pool presets to beesky-grid.json', () async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final store = GridStore(primaryDir: tmp, fallbackDir: tmp);
      await store.save(GridConfig()..poolPresets = [sample()]);
      final (loaded, _) = await store.load();
      expect(loaded.poolPresets.single.name, 'Trại A');
      expect(loaded.poolPresets.single.slots.first.worker,
          '{account}.{nn}');
    });
  });

  group('group merge (stretch, mapping §6)', () {
    GroupLastScan scan(String at) => GroupLastScan(
        at: at, scanned: 10, found: 2, ok: 1, check: 1, error: 0);

    test('union semantics: keep identity, dedup targets + creds, '
        'newer lastScan wins', () {
      final keep = NetGroup(
        id: 'g1',
        name: 'Trại chính',
        targets: '192.168.2.0/24, 10.0.0.0/24',
        creds: [CredSet(label: 'A', user: 'root', type: 'vnish')],
        autoscanEnabled: true,
        autoscanIntervalMin: 45,
        lastScan: scan('2026-11-11T08:00:00+07:00'),
      );
      final other = NetGroup(
        id: 'g2',
        name: 'Kho phụ',
        targets: '10.0.0.0/24, 192.168.3.0/24',
        creds: [
          CredSet(label: 'A', user: 'root', type: 'vnish'), // dup
          CredSet(label: 'B', user: 'admin', type: 'stock'),
        ],
        lastScan: scan('2026-11-11T09:30:00+07:00'),
      );
      final merged = mergeGroups(keep, other);
      expect(merged.id, 'g1');
      expect(merged.name, 'Trại chính');
      expect(merged.targets,
          '192.168.2.0/24, 10.0.0.0/24, 192.168.3.0/24');
      expect(merged.creds.map((c) => c.label), ['A', 'B']);
      expect(merged.autoscanEnabled, isTrue);
      expect(merged.autoscanIntervalMin, 45);
      expect(merged.lastScan!.at, '2026-11-11T09:30:00+07:00');
    });

    test('lastScan: one-sided survives; both-null stays null', () {
      final a = NetGroup(id: 'a', name: 'A', targets: 'x');
      final b = NetGroup(
          id: 'b',
          name: 'B',
          targets: 'y',
          lastScan: scan('2026-11-11T09:00:00+07:00'));
      expect(mergeGroups(a, b).lastScan!.at, contains('09:00'));
      expect(mergeGroups(b, a).lastScan!.at, contains('09:00'));
      expect(mergeGroups(a, a).lastScan, isNull);
    });
  });

  group('presets center + editor (widget)', () {
    Future<void> pumpCenter(
      WidgetTester tester, {
      required GridConfig config,
      required void Function(GridConfig) onChanged,
      MinerRecord? previewRecord,
    }) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: Scaffold(
            body: PresetsCenterDialog(
              config: config,
              onChanged: onChanged,
              previewRecord: previewRecord,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    MinerRecord previewRec() => MinerRecord.fromJson(const {
          'ip': '192.168.2.101',
          'model': 'Antminer S19 Pro',
          'source': 'vnish',
          'chains': <dynamic>[],
          'fans_rpm': <dynamic>[],
          'chips_alive': 342,
          'chips_total': 342,
          'max_temp_c': 65.0,
          'problems': <dynamic>[],
          'status': 'OK',
          'pools': [
            {
              'url': 'stratum+tcp://pool.example.com:3333',
              'worker': 'mockworker.001',
              'status': 'alive',
            },
          ],
          'rate_value': 110.5,
          'rate_unit': 'TH/s',
        });

    testWidgets('two tabs; pool CRUD reports through onChanged; '
        'delete asks first', (tester) async {
      final emitted = <GridConfig>[];
      await pumpCenter(
        tester,
        config: GridConfig(),
        onChanged: emitted.add,
        previewRecord: previewRec(),
      );
      // Both tabs exist; the Filters tab is the v0.25 surface.
      expect(find.text('Bộ lọc'), findsOneWidget);
      expect(find.text('Pools'), findsOneWidget);
      await tester.tap(find.text('Pools'));
      await tester.pumpAndSettle();

      // Create a preset through the editor.
      await tester.tap(find.text('Mẫu pool mới'));
      await tester.pumpAndSettle();
      final editor = find.byType(AlertDialog);
      final fields =
          find.descendant(of: editor, matching: find.byType(TextField));
      await tester.enterText(fields.at(0), 'Mẫu trại A');
      await tester.enterText(fields.at(2), 'stratum+tcp://p.example:3333');
      await tester.enterText(fields.at(3), '{account}.{nn}');
      await tester.tap(find.descendant(
          of: editor, matching: find.text('Lưu mẫu')));
      await tester.pumpAndSettle();
      expect(emitted, isNotEmpty);
      expect(emitted.last.poolPresets.single.name, 'Mẫu trại A');
      expect(emitted.last.poolPresets.single.slots.single.worker,
          '{account}.{nn}');
      expect(find.text('Mẫu trại A'), findsOneWidget);

      // Duplicate appends the copy suffix.
      await tester.tap(find.byIcon(Icons.copy_outlined));
      await tester.pumpAndSettle();
      expect(find.text('Mẫu trại A (bản sao)'), findsOneWidget);

      // Delete asks first, then removes.
      await tester.tap(find.byIcon(Icons.delete_outline).first);
      await tester.pumpAndSettle();
      expect(find.textContaining('Xóa mẫu'), findsWidgets);
      await tester.tap(find.text('Đồng ý'));
      await tester.pumpAndSettle();
      expect(emitted.last.poolPresets, hasLength(1));
    });

    testWidgets('editor validation: slot 1 is required; a name '
        'clash warns before replace', (tester) async {
      final cfg = GridConfig()
        ..poolPresets = [
          PoolPreset(name: 'Đã có', slots: [
            PoolSlot(url: 'stratum+tcp://a:1', worker: 'w'),
          ]),
        ];
      await pumpCenter(
        tester,
        config: cfg,
        onChanged: (_) {},
        previewRecord: previewRec(),
      );
      await tester.tap(find.text('Pools'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Mẫu pool mới'));
      await tester.pumpAndSettle();
      final editor = find.byType(AlertDialog);
      final fields =
          find.descendant(of: editor, matching: find.byType(TextField));
      // Name only, no slot 1 → refused with the original's rule.
      await tester.enterText(fields.at(0), 'Mới');
      await tester.tap(find.descendant(
          of: editor, matching: find.text('Lưu mẫu')));
      await tester.pumpAndSettle();
      expect(find.textContaining('Pool 1 phải có đủ'), findsOneWidget);
      // A clashing name warns that saving replaces.
      await tester.enterText(fields.at(0), 'Đã có');
      await tester.pumpAndSettle();
      expect(find.textContaining('Lưu sẽ thay thế mẫu đó'),
          findsOneWidget);
      // The live preview expands against the preview record.
      await tester.enterText(fields.at(2), 'stratum+tcp://p.example:3333');
      await tester.enterText(fields.at(3), '{account}.{nn}');
      await tester.pumpAndSettle();
      expect(find.textContaining('mockworker.01'), findsWidgets);
    });
  });

  group('home flows (mock shell)', () {
    Future<void> pumpHome(
      WidgetTester tester, {
      required Directory tmp,
      GridConfig? gridSeed,
      Map<String, String>? noteSeed,
    }) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      // Store seeding is real dart:io — it must run OUTSIDE
      // the fake-async zone (the ops suites' harness lesson).
      await tester.runAsync(() async {
        if (gridSeed != null) {
          await GridStore(primaryDir: tmp, fallbackDir: tmp)
              .save(gridSeed);
        }
        if (noteSeed != null) {
          await NoteStore(primaryDir: tmp, fallbackDir: tmp)
              .save(noteSeed);
        }
      });
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: HomePage(
            bridge: MockBridge(),
            credStore: CredStore(primaryDir: tmp, fallbackDir: tmp),
            groupStore: GroupStore(primaryDir: tmp, fallbackDir: tmp),
            gridStore: GridStore(primaryDir: tmp, fallbackDir: tmp),
            opsStore: OpsHistoryStore(primaryDir: tmp, fallbackDir: tmp),
            opsFiles: OpsFiles(primaryDir: tmp, fallbackDir: tmp),
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
      await tester.tap(find.text('Quét ngay').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
    }

    /// Selection is the per-row CHECKBOX (a row tap only opens
    /// the detail panel — the shipped v0.25 model). The header
    /// tri-state checkbox is index 0; rows follow in fleet
    /// order (S19 = 1, L9 = 2).
    Future<void> checkRow(WidgetTester tester, int checkboxIndex) async {
      await tester.tap(find.byType(Checkbox).at(checkboxIndex));
      await tester.pumpAndSettle();
    }

    testWidgets('enrichment: the Pools view shows record pools; '
        'the detail Pools tab renders them + status without '
        'inspect', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      // The Pools view-mode segment (a second muted 'Pools'
      // label lives elsewhere on the screen — target the
      // segment by its semibold style).
      final poolsSegment = find.byWidgetPredicate((w) =>
          w is Text &&
          w.data == 'Pools' &&
          w.style?.fontWeight == FontWeight.w600);
      await tester.tap(poolsSegment);
      await tester.pumpAndSettle();
      expect(
          find.text('stratum+tcp://pool.example.com:3333'), findsWidgets);
      expect(find.text('mockworker.001'), findsWidgets);
      // Detail: the S19 Pools tab comes from the record itself
      // (rows open the detail panel in every view mode).
      await tester.tap(find.text('192.168.2.101'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Pools').last);
      await tester.pumpAndSettle();
      expect(find.text('Pool 1 URL'), findsOneWidget);
      expect(
          find.text('stratum+tcp://pool.example.com:3333'), findsWidgets);
      // Both fixture pools report 'alive' — one status row each.
      expect(find.text('alive'), findsNWidgets(2));
    });

    testWidgets('apply preset: picker → confirm → a switch_pool '
        'history entry', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final seed = GridConfig()
        ..poolPresets = [
          PoolPreset(name: 'Mẫu trại A', slots: [
            PoolSlot(
                url: 'stratum+tcp://pool.example.com:3333',
                worker: '{account}.{nn}'),
          ]),
        ];
      await pumpHome(tester, tmp: tmp, gridSeed: seed);
      await checkRow(tester, 1); // the S19
      expect(find.text('Áp mẫu pool'), findsOneWidget);
      await tester.tap(find.text('Áp mẫu pool'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Mẫu trại A'));
      await tester.pumpAndSettle();
      expect(find.text('Xác nhận thao tác — Đổi pool'), findsOneWidget);
      await tester.tap(find.text('Chạy Đổi pool'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pumpAndSettle();
      final histFile = File(
          '${tmp.path}${Platform.pathSeparator}beesky-ops-history.json');
      expect(histFile.existsSync(), isTrue);
      final entries =
          jsonDecode(histFile.readAsStringSync()) as List<dynamic>;
      expect(entries, hasLength(1));
      expect((entries.single as Map)['type'], 'switch_pool');
    });

    testWidgets('clone: the source is excluded; the cgminer '
        'target fails honestly in history', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await checkRow(tester, 1); // the S19 — the detailed source
      await checkRow(tester, 2); // the L9 — the clone target
      expect(find.text('Chép cấu hình pool'), findsOneWidget);
      await tester.tap(find.text('Chép cấu hình pool'));
      await tester.pumpAndSettle();
      expect(find.text('Xác nhận thao tác — Đổi pool'), findsOneWidget);
      // The confirm lists ONLY the target — the source is out.
      final dialog = find.byType(AlertDialog);
      expect(
        find.descendant(of: dialog, matching: find.text('192.168.2.102')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: dialog, matching: find.text('192.168.2.101')),
        findsNothing,
      );
      await tester.tap(find.text('Chạy Đổi pool'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pumpAndSettle();
      final histFile = File(
          '${tmp.path}${Platform.pathSeparator}beesky-ops-history.json');
      final entries =
          jsonDecode(histFile.readAsStringSync()) as List<dynamic>;
      expect(entries, hasLength(1));
      final task = entries.single as Map<String, dynamic>;
      expect(task['type'], 'switch_pool');
      expect(task['targets'], ['192.168.2.102']);
      final results = task['results'] as List<dynamic>;
      expect(results, hasLength(1));
      expect((results.single as Map)['ok'], isFalse);
    });

    testWidgets('note column: a saved note decorates the record '
        'in Tùy chỉnh view', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      // 'note' joins the Custom set only when the user enables
      // it (the shipped default set is the v0.24 one) — seed
      // the config with it on, in Custom mode.
      final gridSeed = GridConfig()
        ..viewMode = GridViewMode.custom
        ..visibleColumns = {...gridDefaultVisible, 'note'};
      await pumpHome(tester,
          tmp: tmp,
          gridSeed: gridSeed,
          noteSeed: {'192.168.2.101': 'máy mới thay quạt'});
      expect(find.text('GHI CHÚ'), findsOneWidget);
      expect(find.text('máy mới thay quạt'), findsOneWidget);
    });

    testWidgets('presets center opens from the toolbar with '
        'both tabs', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await tester.tap(find.text('Trung tâm mẫu'));
      await tester.pumpAndSettle();
      // The toolbar's own Bộ lọc button also carries the
      // label — both tabs just need to be there.
      expect(find.text('Bộ lọc'), findsWidgets);
      expect(find.text('Pools'), findsWidgets);
    });

    testWidgets('"Lưu & quét" saves the group AND enters its '
        'scan', (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      await pumpHome(tester, tmp: tmp);
      await tester.tap(find.text('Nhóm mạng').first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Sửa').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Lưu & quét'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();
      // The group scan landed us in the miners view, scoped.
      expect(find.textContaining('Quét nhóm Kho phụ xong'),
          findsOneWidget);
      expect(find.text('192.168.2.102'), findsOneWidget);
    });
  });
}
