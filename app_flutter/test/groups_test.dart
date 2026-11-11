import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.24: network groups — the store document is the core's schema
/// (beesky-groups.json), group scans go through the sidecar as
/// `scan --group <name>` (paths only on argv, never values), the
/// app opens on the groups screen, and the editor round-trips
/// name/targets/autoscan/per-group creds through the store file.
void main() {
  group('NetGroup JSON (the core store schema)', () {
    test('round-trips every field, last_scan included', () {
      final group = NetGroup(
        id: 'abc123',
        name: 'Trại chính',
        targets: '192.168.2.0/24',
        creds: [
          CredSet(label: 'VNish trại', user: 'root', secret: 'pw',
              type: 'vnish'),
        ],
        autoscanEnabled: true,
        autoscanIntervalMin: 45,
        lastScan: const GroupLastScan(
          at: '2026-11-11T08:15:00+07:00',
          scanned: 254,
          found: 63,
          ok: 12,
          check: 51,
          error: 0,
        ),
      );
      final back = NetGroup.fromJson(group.toJson());
      expect(back.id, 'abc123');
      expect(back.name, 'Trại chính');
      expect(back.targets, '192.168.2.0/24');
      expect(back.creds.single.type, 'vnish');
      expect(back.autoscanEnabled, isTrue);
      expect(back.autoscanIntervalMin, 45);
      expect(back.lastScan?.found, 63);
      expect(back.isNew, isFalse);
    });

    test('defaults: no creds, autoscan off at 30, never scanned', () {
      final group = NetGroup.fromJson(const {
        'name': 'Kho phụ',
        'targets': '192.168.3.0/24',
      });
      expect(group.creds, isEmpty);
      expect(group.autoscanEnabled, isFalse);
      expect(group.autoscanIntervalMin, 30);
      expect(group.isNew, isTrue);
      expect(group.autoscanText, 'Tự quét: tắt');
    });

    test('last-scan summary line carries the counts', () {
      const scan = GroupLastScan(
        at: '2026-11-11T09:41:07+07:00',
        scanned: 254,
        found: 63,
        ok: 12,
        check: 51,
        error: 0,
      );
      // The clock time renders in the reader's LOCAL zone (the
      // core stamps +07:00 at the farm), so assert the zone-free
      // parts: the date and every count.
      expect(scan.summaryText, startsWith('Quét '));
      expect(
        scan.summaryText,
        contains('11/11: 63 máy • OK 12 • Kiểm tra 51 • Lỗi 0'),
      );
    });
  });

  group('autoscanDue', () {
    final group = NetGroup(
      id: 'g1',
      name: 'G',
      targets: '10.0.0.0/24',
      autoscanEnabled: true,
      autoscanIntervalMin: 30,
    );
    final t0 = DateTime(2026, 11, 11, 8, 0);

    test('not due before the interval, due at/after it', () {
      expect(autoscanDue(group, t0, t0.add(const Duration(minutes: 29))),
          isFalse);
      expect(autoscanDue(group, t0, t0.add(const Duration(minutes: 30))),
          isTrue);
    });

    test('never due when disabled or never run', () {
      final off = group.copy()..autoscanEnabled = false;
      expect(autoscanDue(off, t0, t0.add(const Duration(days: 1))),
          isFalse);
      expect(autoscanDue(group, null, t0), isFalse);
    });
  });

  group('GroupStore', () {
    late Directory tmp;
    late GroupStore store;

    setUp(() async {
      tmp = await Directory.systemTemp.createTemp('beesky_groups_test');
      store = GroupStore(
        primaryDir: Directory('${tmp.path}/app'),
        fallbackDir: Directory('${tmp.path}/fallback'),
      );
      await store.primaryDir.create(recursive: true);
    });

    tearDown(() async {
      if (await tmp.exists()) await tmp.delete(recursive: true);
    });

    test('missing file loads empty, with no source', () async {
      final (groups, source) = await store.load();
      expect(groups, isEmpty);
      expect(source, isNull);
    });

    test('save/load round-trip writes the versioned document',
        () async {
      final groups = demoGroups();
      final written = await store.save(groups);
      expect(written.path, store.primaryFile.path);
      final doc = jsonDecode(await written.readAsString())
          as Map<String, dynamic>;
      expect(doc['version'], 1);
      expect((doc['groups'] as List), hasLength(2));

      final (loaded, source) = await store.load();
      expect(source?.path, written.path);
      expect(loaded.map((g) => g.name), ['Trại chính', 'Kho phụ']);
      expect(loaded.first.lastScan?.found, 5);
      expect(loaded.last.isNew, isTrue);
    });
  });

  group('sidecar argv contract', () {
    test('group scan: --group with no positional target', () {
      expect(
        SidecarBridge.scanGroupArgs('Trại chính'),
        ['scan', '--group', 'Trại chính', '--json'],
      );
      expect(
        SidecarBridge.scanGroupArgs(
          'Trại chính',
          credsFile: '/app/beesky-creds.json',
          groupsFile: '/app/beesky-groups.json',
        ),
        [
          'scan',
          '--group',
          'Trại chính',
          '--json',
          '--creds-file',
          '/app/beesky-creds.json',
          '--groups-file',
          '/app/beesky-groups.json',
        ],
      );
    });
  });

  group('groups screen (mock shell)', () {
    // SYNC temp dirs: inside testWidgets the body runs in a fake-
    // async zone where dart:io futures never complete (the same
    // harness lesson as the creds tests).
    Directory tempDir() =>
        Directory.systemTemp.createTempSync('beesky_groups_ui');

    void deleteDir(Directory dir) {
      try {
        dir.deleteSync(recursive: true);
      } on Object {
        // best effort cleanup
      }
    }

    Future<GroupStore> pumpGroups(WidgetTester tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final store = GroupStore(primaryDir: tmp, fallbackDir: tmp);
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          theme: buildBeeSkyTheme(),
          home: HomePage(
            bridge: MockBridge(),
            credStore: CredStore(primaryDir: tmp, fallbackDir: tmp),
            groupStore: store,
          ),
        ),
      );
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 150)),
      );
      await tester.pump();
      return store;
    }

    /// Bounded pumps for flows where a field holds focus (a
    /// blinking cursor never lets pumpAndSettle settle).
    Future<void> beat(WidgetTester tester, [int ms = 350]) async {
      await tester.pump();
      await tester.pump(Duration(milliseconds: ms));
    }

    testWidgets(
      'opens on the demo groups; Quét nhóm scopes the miners view',
      (tester) async {
        await pumpGroups(tester);

        // The groups home: chips + both demo cards, the unscanned
        // one tagged MỚI and reading "Chưa quét".
        expect(find.text('Tổng 2 nhóm'), findsOneWidget);
        expect(find.text('Đã quét 1'), findsOneWidget);
        expect(find.text('Trại chính'), findsOneWidget);
        expect(find.text('Kho phụ'), findsOneWidget);
        expect(find.text('MỚI'), findsOneWidget);
        expect(find.text('Chưa quét'), findsOneWidget);
        expect(find.text('Tự quét: mỗi 30 phút'), findsOneWidget);
        expect(find.text('Tài khoản riêng: 1 bộ'), findsOneWidget);
        expect(
          find.textContaining('5 máy • OK 1 • Kiểm tra 3 • Lỗi 1'),
          findsOneWidget,
        );

        // Scan the main group: the miners view opens scoped, the
        // mock fleet lands, and the header names the group.
        await tester.tap(find.text('Quét nhóm').first);
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 700));
        await tester.pumpAndSettle();
        expect(find.text('Nhóm: Trại chính'), findsOneWidget);
        expect(find.text('192.168.2.102'), findsOneWidget);
        expect(find.text('14.54 MH/s'), findsOneWidget);
        expect(
          find.textContaining('Quét nhóm Trại chính xong'),
          findsOneWidget,
        );

        // Back on the groups screen the card now carries the fresh
        // pass (mock mode updates it in memory).
        await tester.tap(find.text('Nhóm mạng').first);
        await tester.pumpAndSettle();
        expect(find.text('Đã quét 1'), findsOneWidget);
        expect(
          find.textContaining('5 máy • OK 1 • Kiểm tra 3 • Lỗi 1'),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'editor: create a group with its own cred set, persisted',
      (tester) async {
        final store = await pumpGroups(tester);

        await tester.tap(find.text('Thêm nhóm').first);
        await tester.pumpAndSettle();
        final dialog = find.byType(AlertDialog);
        expect(dialog, findsOneWidget);

        // Fields in order: name, targets, interval, then the creds
        // editor's add button starts empty (0 sets).
        await tester.enterText(
          find.descendant(of: dialog, matching: find.byType(TextField))
              .at(0),
          'Trại mới',
        );
        await tester.enterText(
          find.descendant(of: dialog, matching: find.byType(TextField))
              .at(1),
          '10.0.0.0/24',
        );
        // One own cred set for the group.
        await tester.tap(
          find.descendant(of: dialog, matching: find.text('Thêm bộ')),
        );
        await beat(tester);
        final fields = find.descendant(
          of: dialog,
          matching: find.byType(TextField),
        );
        // name + targets + interval + label + user + password.
        expect(fields, findsNWidgets(6));
        await tester.enterText(fields.at(3), 'Riêng trại mới');
        await tester.enterText(fields.at(4), 'root');
        await tester.enterText(fields.at(5), 'pw-rieng');

        await tester.tap(
          find.descendant(of: dialog, matching: find.text('Lưu')),
        );
        await beat(tester);
        expect(find.byType(AlertDialog), findsNothing);
        expect(find.text('Trại mới'), findsOneWidget);
        expect(find.text('Tổng 3 nhóm'), findsOneWidget);

        // Persisted: the store file holds the group WITH its set.
        late List<dynamic> rawGroups;
        await tester.runAsync(() async {
          for (var i = 0; i < 40; i++) {
            try {
              final doc = jsonDecode(
                await store.primaryFile.readAsString(),
              ) as Map<String, dynamic>;
              rawGroups = doc['groups'] as List<dynamic>;
              if (rawGroups.length == 3) return;
            } on Object {
              // not written yet
            }
            await Future<void>.delayed(
              const Duration(milliseconds: 100),
            );
          }
          throw StateError('groups file never written');
        });
        final created = rawGroups
            .map((e) => e as Map<String, dynamic>)
            .firstWhere((g) => g['name'] == 'Trại mới');
        expect(created['targets'], '10.0.0.0/24');
        final sets = created['creds'] as List<dynamic>;
        expect(sets, hasLength(1));
        expect((sets.single as Map)['label'], 'Riêng trại mới');
      },
    );

    testWidgets('editor: rename a group; delete asks, then removes',
        (tester) async {
      await pumpGroups(tester);

      // Rename "Kho phụ" via its Sửa button (second card).
      await tester.tap(find.text('Sửa').last);
      await tester.pumpAndSettle();
      final dialog = find.byType(AlertDialog);
      await tester.enterText(
        find.descendant(of: dialog, matching: find.byType(TextField))
            .at(0),
        'Kho phụ 2',
      );
      await tester.tap(
        find.descendant(of: dialog, matching: find.text('Lưu')),
      );
      await beat(tester);
      expect(find.text('Kho phụ 2'), findsOneWidget);
      expect(find.text('Kho phụ'), findsNothing);

      // Delete asks first (HashCore names the group too), then the
      // card is gone.
      await tester.tap(find.byIcon(Icons.delete_outline).last);
      await tester.pumpAndSettle();
      expect(find.text('Xóa nhóm?'), findsOneWidget);
      expect(find.textContaining('Kho phụ 2'), findsWidgets);
      await tester.tap(find.text('Xóa'));
      await beat(tester);
      expect(find.text('Tổng 1 nhóm'), findsOneWidget);
    });
  });
}
