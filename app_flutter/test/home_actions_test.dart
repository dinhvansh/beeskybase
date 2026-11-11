import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.23 interactions on the main window:
///  * double-clicking a miner row opens that miner's web admin
///    (http://<ip>) through the injected opener;
///  * the creds dialog renders the saved sets with their machine-
///    type dropdowns (the vnish row shows its API-key field), rows
///    can be added / edited / deleted, and Save persists everything
///    — types and api_key included — to the store file.
void main() {
  // SYNC temp dirs: inside testWidgets the body runs in a fake-
  // async zone where dart:io futures never complete — an awaited
  // createTemp() there hangs the test until the runner timeout.
  Directory tempDir() =>
      Directory.systemTemp.createTempSync('beesky_home_actions');

  void deleteDir(Directory dir) {
    try {
      dir.deleteSync(recursive: true);
    } on Object {
      // best effort cleanup
    }
  }

  Future<void> pumpHome(
    WidgetTester tester, {
    required CredStore store,
    Future<void> Function(String url)? opener,
  }) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        theme: buildBeeSkyTheme(),
        home: HomePage(
          bridge: MockBridge(),
          credStore: store,
          urlOpener: opener,
        ),
      ),
    );
    // Cred load is real IO (a temp file); let it land, then render.
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 150)),
    );
    await tester.pump();
  }

  Future<void> runMockScan(WidgetTester tester) async {
    await tester.tap(find.text('Quét ngay').first);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();
  }

  testWidgets('double-click a row opens http://<ip> in the browser',
      (tester) async {
    final tmp = tempDir();
    addTearDown(() => deleteDir(tmp));
    final opened = <String>[];
    await pumpHome(
      tester,
      store: CredStore(primaryDir: tmp, fallbackDir: tmp),
      opener: (url) async => opened.add(url),
    );
    await runMockScan(tester);
    expect(find.text('192.168.2.102'), findsOneWidget);

    // Two quick taps = a double-tap (this Flutter SDK's tester has
    // no doubleTap helper).
    final row = find.text('192.168.2.102');
    await tester.tap(row);
    await tester.pump(const Duration(milliseconds: 60));
    await tester.tap(row);
    await tester.pumpAndSettle();

    expect(opened, ['http://192.168.2.102']);
    // …and the row still selects (detail panel for the L9).
    expect(find.text('192.168.2.102 • cgminer RPC'), findsOneWidget);
  });

  testWidgets(
    'creds dialog: mixed-type rows render, add/edit/delete persist',
    (tester) async {
      final tmp = tempDir();
      addTearDown(() => deleteDir(tmp));
      final store = CredStore(primaryDir: tmp, fallbackDir: tmp);
      await pumpHome(tester, store: store);

      // Mock mode seeds 3 demo sets (vnish / stock / any).
      expect(find.text('Tài khoản: 3 bộ'), findsOneWidget);
      await tester.tap(find.text('Tài khoản: 3 bộ'));
      await tester.pumpAndSettle();

      final dialog = find.byType(AlertDialog);
      expect(dialog, findsOneWidget);
      // The three type labels are all on screen (dropdown values).
      expect(
        find.descendant(of: dialog, matching: find.text('VNish')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: dialog, matching: find.text('Antminer gốc')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: dialog, matching: find.text('Mọi loại máy')),
        findsOneWidget,
      );
      // Only the vnish row carries an API-key field.
      expect(find.text('API key (không bắt buộc)'), findsOneWidget);
      // 3 rows: vnish row has 4 text fields, the others 3 each.
      final fieldsInDialog = find.descendant(
        of: dialog,
        matching: find.byType(TextField),
      );
      expect(fieldsInDialog, findsNWidgets(10));

      // Add a row -> +3 fields (a fresh 'any' row has no api key).
      await tester.tap(find.text('Thêm bộ'));
      await tester.pumpAndSettle();
      expect(fieldsInDialog, findsNWidgets(13));

      // Delete the fresh row again -> back to 10. (The new row is
      // below the dialog list's fold — scroll it into view first,
      // or the tap lands on the dialog surface behind it.)
      await tester.ensureVisible(find.byIcon(Icons.delete_outline).last);
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.delete_outline).last);
      await tester.pumpAndSettle();
      expect(fieldsInDialog, findsNWidgets(10));

      // Edit: rename the vnish set + give it an API key. From here
      // on a TextField holds focus and its cursor blinks forever,
      // so pumpAndSettle would never settle — bounded pumps only.
      Future<void> beat([int ms = 350]) async {
        await tester.pump();
        await tester.pump(Duration(milliseconds: ms));
      }

      await tester.enterText(fieldsInDialog.at(0), 'VNish trại B');
      await tester.enterText(fieldsInDialog.at(3), 'key-xyz');
      // Retag the stock set to "any" through its dropdown.
      await tester.tap(
        find.descendant(of: dialog, matching: find.text('Antminer gốc')),
      );
      await beat();
      await tester.tap(find.text('Mọi loại máy').last);
      await beat();

      await tester.tap(find.text('Lưu'));
      await beat();
      expect(find.byType(AlertDialog), findsNothing);

      // The save is real IO started in the fake zone; poll the
      // file in real time until the write lands, then assert.
      late List<dynamic> raw;
      await tester.runAsync(() async {
        for (var i = 0; i < 40; i++) {
          try {
            raw = jsonDecode(await store.primaryFile.readAsString())
                as List<dynamic>;
            if (raw.length == 3) return;
          } on Object {
            // not written yet
          }
          await Future<void>.delayed(const Duration(milliseconds: 100));
        }
        throw StateError('creds file never written');
      });
      final sets = [for (final e in raw) e as Map<String, dynamic>];
      expect(sets, hasLength(3));
      final vnish = sets.firstWhere((s) => s['label'] == 'VNish trại B');
      expect(vnish['type'], 'vnish');
      expect(vnish['api_key'], 'key-xyz');
      final retagged = sets.firstWhere((s) => s['label'] == 'Kho S19 gốc');
      expect(retagged['type'], 'any');
      // Button count reflects the persisted list.
      expect(find.text('Tài khoản: 3 bộ'), findsOneWidget);
    },
  );
}
