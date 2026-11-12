import 'package:beesky_app/creds.dart';
import 'package:beesky_app/grid.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.30 vendor coverage (docs/vendor-coverage-mapping.md): the
/// cred family set grows to HashCore's vendor universe — the new
/// tags round-trip through the shared --creds-file schema, the
/// cred dialog offers the new family labels, and a Whatsminer
/// record (the one family with a fully dissected read contract)
/// renders in the grid pipeline + detail inspect shapes with its
/// native unit and honest 0/0 chip counts.
void main() {
  group('cred families (v0.30)', () {
    test('the six new family tags round-trip', () {
      for (final type in [
        'whatsminer',
        'avalon',
        'iceriver',
        'jasminer',
        'braiins',
        'luxos',
        'epic',
        'auradine',
        'sealminer',
      ]) {
        final set = CredSet(label: 'Kho', user: 'root', secret: 'pw', type: type);
        expect(CredSet.fromJson(set.toJson()).type, type, reason: type);
      }
    });

    test('the label map covers the whole family set', () {
      expect(credTypeLabels.keys, [
        'any',
        'stock',
        'vnish',
        'whatsminer',
        'avalon',
        'iceriver',
        'jasminer',
        'braiins',
        'luxos',
        'epic',
        'auradine',
        'sealminer',
      ]);
      expect(credTypeLabels['whatsminer'], 'Whatsminer (MicroBT)');
      expect(credTypeLabels['avalon'], 'Avalon (Canaan)');
      expect(credTypeLabels['iceriver'], 'IceRiver');
      expect(credTypeLabels['jasminer'], 'Jasminer (SunLune)');
      expect(credTypeLabels['braiins'], 'Braiins OS');
      expect(credTypeLabels['luxos'], 'LuxOS');
      expect(credTypeLabels['epic'], 'Epic');
      expect(credTypeLabels['auradine'], 'Auradine');
      expect(credTypeLabels['sealminer'], 'Sealminer (Bitdeer)');
    });

    testWidgets('the cred editor shows the Whatsminer family label',
        (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: CredSetsEditor(initial: [
            CredSet(
              label: 'WM trại',
              user: 'root',
              secret: 'pw',
              type: 'whatsminer',
            ),
          ]),
        ),
      ));
      await tester.pumpAndSettle();
      expect(find.text('Whatsminer (MicroBT)'), findsOneWidget);
    });

    test('group creds keep a new family tag verbatim', () {
      final group = NetGroup(
        id: 'g1',
        name: 'Trại WM',
        targets: '192.168.2.0/24',
        creds: [
          CredSet(label: 'B', user: 'root', secret: 'pw', type: 'braiins'),
        ],
      );
      final back = NetGroup.fromJson(group.toJson());
      expect(back.creds.single.type, 'braiins');
    });
  });

  group('records for the new families', () {
    test('an avalon record labels itself Avalon (Canaan)', () {
      final rec = MinerRecord.fromJson(const {
        'ip': '192.168.2.120',
        'model': 'AvalonMiner 1246',
        'source': 'avalon',
        'chains': [],
        'fans_rpm': [],
        'chips_alive': 0,
        'chips_total': 0,
        'status': 'OK',
        'rate_value': 90.0,
        'rate_unit': 'TH/s',
        'ths': 90.0,
      });
      expect(rec.sourceLabel, 'Avalon (Canaan)');
      expect(rec.rateText, '90.00 TH/s');
    });

    test('the mock fleet carries a whatsminer record, native unit',
        () async {
      final result = await MockBridge().scan('192.168.2.0/24');
      expect(result.found, 5);
      final wm = result.records.singleWhere((r) => r.ip == '192.168.2.105');
      expect(wm.source, 'whatsminer');
      expect(wm.sourceLabel, 'Whatsminer');
      expect(wm.model, 'WhatsMiner M30S');
      expect(wm.rateText, '111.80 TH/s');
      expect(wm.chipsAlive, 0);
      expect(wm.chipsTotal, 0);
      expect(wm.maxTempC, 87.0);
      expect(wm.fansRpm, [4560, 4620]);
      expect(wm.pools.single.worker, 'wmworker.001');
    });

    test('firmware grouping gains a Whatsminer bucket', () async {
      final result = await MockBridge().scan('192.168.2.0/24');
      final view = applyGridView(
        result.records,
        groupBy: GridGroupBy.firmware,
      );
      final keys = view.groups.map((g) => g.key).toList();
      expect(keys, contains('Whatsminer'));
      final wmGroup =
          view.groups.singleWhere((g) => g.key == 'Whatsminer');
      expect(wmGroup.records.single.ip, '192.168.2.105');
    });

    test('mock inspect for the whatsminer: temps, no chip grades',
        () async {
      final insp = await MockBridge().inspect('192.168.2.105');
      expect(insp.source, 'whatsminer');
      expect(insp.boards.supported, isTrue);
      expect(insp.boards.boards.map((b) => b.tempC), [62.0, 87.0, 65.0]);
      expect(insp.boards.boards.every((b) => !b.hasGrades), isTrue);
      expect(insp.boards.boards.every((b) => b.chipsTotal == 0), isTrue);
      expect(insp.fans.fans.map((f) => f.rpm), [4560, 4620]);
      expect(insp.pools.pools.single.status, 'Alive');
    });
  });
}
