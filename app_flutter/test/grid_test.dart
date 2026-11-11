import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/grid.dart';
import 'package:beesky_app/groups.dart';
import 'package:beesky_app/home_page.dart';
import 'package:beesky_app/models.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:beesky_app/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.25.0 — the data-grid miners list (docs/grid-mapping.md):
/// model extensions, the column system + persistence, sorting,
/// search, the filter builder + presets, grouping, the selection
/// model + isolate, and the widget-level grid behaviours.

MinerRecord fakeMiner({
  required String ip,
  String model = 'Antminer S19 Pro',
  String source = 'vnish',
  List<double?> boardTemps = const [60, 61, 62],
  int chipsAlive = 342,
  int chipsTotal = 342,
  List<Problem> issues = const [],
  String status = 'OK',
  double? rateValue = 110.0,
  String? rateUnit = 'TH/s',
  double? ths,
  int elapsedS = 0,
  double? ghs5s,
  double? powerW,
  String? mac,
  List<PoolInfo> pools = const [],
  String? credLabel,
}) {
  final chains = <ChainInfo>[
    for (var i = 0; i < boardTemps.length; i++)
      ChainInfo(
        index: i,
        tempC: boardTemps[i],
        chipsAlive: chipsTotal == 0
            ? 0
            : (chipsAlive ~/ (boardTemps.isEmpty ? 1 : boardTemps.length)),
        chipsTotal: chipsTotal == 0
            ? 0
            : (chipsTotal ~/ (boardTemps.isEmpty ? 1 : boardTemps.length)),
      ),
  ];
  final temps = boardTemps.whereType<double>().toList();
  return MinerRecord(
    ip: ip,
    model: model,
    source: source,
    chains: chains,
    fansRpm: const [4000, 4100],
    chipsAlive: chipsAlive,
    chipsTotal: chipsTotal,
    maxTempC: temps.isEmpty ? null : temps.reduce((a, b) => a > b ? a : b),
    issues: issues,
    status: status,
    rateValue: rateValue,
    rateUnit: rateUnit,
    legacyThs: ths ?? (rateUnit == 'TH/s' ? rateValue : null),
    credLabel: credLabel,
    elapsedS: elapsedS,
    ghs5s: ghs5s,
    powerW: powerW,
    mac: mac,
    pools: pools,
  );
}

/// A 63-miner fleet in the shape of the owner's real farm scan
/// (mixed models, mixed statuses, one hot board in seventeen,
/// one unreachable unit) — the grid's scale exercise.
List<MinerRecord> generatedFleet() {
  const models = ['Antminer S19 Pro', 'Antminer L9', 'Antminer Z15'];
  return [
    for (var i = 0; i < 63; i++)
      if (i == 62)
        fakeMiner(
          ip: '192.168.2.${100 + i}',
          model: '—',
          source: 'cgminer',
          boardTemps: const [],
          chipsAlive: 0,
          chipsTotal: 0,
          issues: const [
            Problem(code: 'FETCH_ERROR', severity: 'error', detail: 'x'),
          ],
          status: 'CHECK',
          rateValue: null,
          rateUnit: null,
        )
      else
        fakeMiner(
          ip: '192.168.2.${100 + i}',
          model: models[i % 3],
          source: i % 3 == 0 ? 'vnish' : 'cgminer',
          boardTemps: [
            55.0 + (i % 30),
            i % 17 == 0 ? 88.0 : 56.0 + (i % 28),
            57.0 + (i % 25),
          ],
          chipsAlive: i % 5 == 0 ? 300 : 342,
          issues: i % 5 == 0
              ? const [
                  Problem(code: 'MISSING_CHIPS', severity: 'warn', detail: 'x'),
                ]
              : const [],
          status: i % 5 == 0 ? 'CHECK' : 'OK',
          rateValue: switch (i % 3) {
            0 => 110.0,
            1 => 14.54,
            _ => 1101.0,
          },
          rateUnit: switch (i % 3) {
            0 => 'TH/s',
            1 => 'MH/s',
            _ => 'ksol/s',
          },
          elapsedS: 3600 * (i + 1),
          powerW: i % 3 == 0 ? 3210 : null,
        ),
  ];
}

void main() {
  registerGridWidgetTests();

  group('models: v0.25 wire extensions', () {
    test('elapsed/power/ghs parse; derived getters stay honest', () {
      final rec = MinerRecord.fromJson({
        'ip': '10.0.0.1',
        'model': 'Antminer S19 Pro',
        'source': 'vnish',
        'elapsed_s': 90061,
        'ghs_5s': 109000.0,
        'ghs_av': 110000.0,
        'ths': 110.5,
        'rate_value': 110.5,
        'rate_unit': 'TH/s',
        'power_w': 3210.0,
        'chains': [
          {'index': 0, 'temp_c': 61.0, 'chips_alive': 100, 'chips_total': 114},
          {'index': 1, 'temp_c': 88.0, 'chips_alive': 90, 'chips_total': 114},
        ],
        'fans_rpm': [4000],
        'chips_alive': 190,
        'chips_total': 228,
        'max_temp_c': 88.0,
        'problems': [
          {'code': 'OVER_TEMP', 'severity': 'warn', 'detail': 'x'},
        ],
        'status': 'CHECK',
      });
      expect(rec.uptimeText, '1d 1h');
      expect(rec.powerText, '3210 W');
      expect(rec.efficiencyJTh!, closeTo(29.05, 0.01));
      expect(rec.efficiencyText, '29.0 J/TH');
      expect(rec.rateRtText, '109.00 TH/s');
      expect(rec.algorithmLabel, 'SHA-256');
      expect(rec.badBoards, 2);
      expect(rec.errorCodesText, 'OVER_TEMP');
      expect(rec.boardTempAt(1), 88.0);
      expect(rec.boardTempAt(3), isNull);
    });

    test('realtime rate is TH/s-only; efficiency needs power + TH/s', () {
      final l9 = MinerRecord.fromJson({
        'ip': '10.0.0.2',
        'model': 'Antminer L9',
        'source': 'cgminer',
        'ghs_5s': null,
        'ths': null,
        'rate_value': 14.54,
        'rate_unit': 'MH/s',
        'power_w': 3000.0,
        'chains': [],
        'fans_rpm': [],
        'chips_alive': 0,
        'chips_total': 0,
        'max_temp_c': null,
        'problems': [],
        'status': 'OK',
      });
      expect(l9.rateRt, isNull);
      expect(l9.rateRtText, '—');
      expect(l9.efficiencyJTh, isNull);
      expect(l9.algorithmLabel, 'Scrypt');
      expect(l9.powerText, '3000 W');
      expect(l9.uptimeText, '—');
    });

    test('pools parse defensively (absent today, ready when core grows)', () {
      final rec = MinerRecord.fromJson({
        'ip': '10.0.0.3',
        'model': 'X',
        'source': 'stock',
        'chains': [],
        'fans_rpm': [],
        'chips_alive': 0,
        'chips_total': 0,
        'max_temp_c': null,
        'problems': [],
        'status': 'OK',
        'pools': [
          {'url': 'stratum+tcp://pool.example:3333', 'worker': 'farm.001'},
          {'url': 'stratum+tcp://backup:3333', 'user': 'farm.002'},
        ],
      });
      expect(rec.poolUrlAt(0), 'stratum+tcp://pool.example:3333');
      expect(rec.poolWorkerAt(0), 'farm.001');
      expect(rec.poolWorkerAt(1), 'farm.002');
      expect(rec.poolUrlAt(2), '');
      expect(rec.searchHaystack, contains('farm.001'));
    });
  });

  group('columns: config, modes, persistence', () {
    test('defaults reproduce the v0.24 set/order (metric mode)', () {
      final cfg = GridConfig();
      expect(
        cfg.activeColumns.map((c) => c.id).toList(),
        [
          'ip',
          'model',
          'firmware',
          'hashrate',
          'chips',
          'temps',
          'fans',
          'status'
        ],
      );
      expect(
        cfg.activeColumns.map((c) => c.flex).toList(),
        [3, 4, 3, 3, 2, 3, 3, 2],
      );
    });

    test('pools mode is the fixed pool-centric set', () {
      final cfg = GridConfig()..viewMode = GridViewMode.pools;
      expect(
        cfg.activeColumns.map((c) => c.id).toList(),
        containsAll(['pool1Url', 'pool1Worker', 'pool2Url', 'pool3Worker']),
      );
      expect(cfg.activeColumns.first.id, 'ip');
    });

    test('toggle + reorder land in custom mode order; reset restores', () {
      final cfg = GridConfig()..viewMode = GridViewMode.custom;
      cfg.visibleColumns.remove('fans');
      expect(cfg.activeColumns.map((c) => c.id), isNot(contains('fans')));
      cfg.visibleColumns.add('uptime');
      expect(cfg.activeColumns.map((c) => c.id), contains('uptime'));
      cfg.moveColumn('ip', 1); // swaps IP and MODEL in the order
      expect(cfg.activeColumns.map((c) => c.id).take(2), ['model', 'ip']);
      cfg.resetColumns();
      expect(cfg.columnOrder, gridColumnUniverse.map((c) => c.id).toList());
      expect(cfg.visibleColumns, {...gridDefaultVisible});
    });

    test('JSON round-trip keeps everything; unknown ids dropped', () {
      final cfg = GridConfig()
        ..viewType = GridViewType.overview
        ..viewMode = GridViewMode.custom
        ..overviewColor = OverviewColorMode.hashrate
        ..overviewSize = OverviewCellSize.large
        ..sort = GridSort(field: 'temps', ascending: false)
        ..groupBy = GridGroupBy.model
        ..visibleColumns = {'ip', 'uptime', 'bogus-column'}
        ..filterPresets = [
          FilterPreset(name: 'Nóng', filters: [
            GridFilter(field: 'maxTemp', op: FilterOp.greater, value: '80'),
          ]),
        ];
      final back = GridConfig.fromJson(
        jsonDecode(jsonEncode(cfg.toJson())) as Map<String, dynamic>,
      );
      expect(back.viewType, GridViewType.overview);
      expect(back.viewMode, GridViewMode.custom);
      expect(back.overviewColor, OverviewColorMode.hashrate);
      expect(back.overviewSize, OverviewCellSize.large);
      expect(back.sort.field, 'temps');
      expect(back.sort.ascending, isFalse);
      expect(back.groupBy, GridGroupBy.model);
      expect(back.visibleColumns, {'ip', 'uptime'});
      expect(back.filterPresets.single.name, 'Nóng');
      expect(back.filterPresets.single.filters.single.op, FilterOp.greater);
      // Columns a future build adds still join the order's tail.
      expect(back.columnOrder.length, gridColumnUniverse.length);
    });

    test('GridStore round-trips via the primary file; corrupt = defaults',
        () async {
      final tmp = Directory.systemTemp.createTempSync('beesky_grid_store');
      addTearDown(() => tmp.deleteSync(recursive: true));
      final store = GridStore(primaryDir: tmp, fallbackDir: tmp);
      final cfg = GridConfig()..groupBy = GridGroupBy.status;
      final file = await store.save(cfg);
      expect(file.path, contains('beesky-grid.json'));
      final (loaded, source) = await store.load();
      expect(source, isNotNull);
      expect(loaded.groupBy, GridGroupBy.status);

      await file.writeAsString('{not json');
      final (fallback, source2) = await store.load();
      expect(source2, isNull);
      expect(fallback.groupBy, GridGroupBy.none);
    });
  });

  group('sorting', () {
    final a = fakeMiner(ip: '192.168.2.101', boardTemps: [65, 66, 67]);
    final b = fakeMiner(ip: '192.168.2.99', boardTemps: [59, 58, 57]);
    final c = fakeMiner(
      ip: '192.168.2.103',
      boardTemps: [71, 88, 73],
      issues: const [
        Problem(code: 'OVER_TEMP', severity: 'warn', detail: 'x'),
      ],
      status: 'CHECK',
    );
    final dead = fakeMiner(
      ip: '192.168.2.104',
      boardTemps: const [],
      chipsAlive: 0,
      chipsTotal: 0,
      rateValue: null,
      rateUnit: null,
    );

    List<String> order(List<MinerRecord> rs, GridSort s) {
      final sorted = [...rs]..sort((x, y) => compareByColumn(x, y, s));
      return sorted.map((r) => r.ip).toList();
    }

    test('IP sorts octet-numerically, not lexicographically', () {
      expect(
        order([a, b, c], GridSort(field: 'ip')),
        ['192.168.2.99', '192.168.2.101', '192.168.2.103'],
      );
    });

    test('temps: nulls last in BOTH directions', () {
      expect(
        order([a, dead, c], GridSort(field: 'temps')),
        ['192.168.2.101', '192.168.2.103', '192.168.2.104'],
      );
      expect(
        order([a, dead, c], GridSort(field: 'temps', ascending: false)),
        ['192.168.2.103', '192.168.2.101', '192.168.2.104'],
      );
    });

    test('status sorts OK < CHECK < ERROR', () {
      final err = fakeMiner(
        ip: '192.168.2.105',
        issues: const [
          Problem(code: 'FETCH_ERROR', severity: 'error', detail: 'x'),
        ],
        status: 'CHECK',
      );
      expect(
        order([err, c, a], GridSort(field: 'status')),
        ['192.168.2.101', '192.168.2.103', '192.168.2.105'],
      );
    });

    test('rates never compare across units (families stay ordered)', () {
      final l9 =
          fakeMiner(ip: '192.168.2.102', rateValue: 14.54, rateUnit: 'MH/s');
      final z15 =
          fakeMiner(ip: '192.168.2.106', rateValue: 1101, rateUnit: 'ksol/s');
      expect(
        order([z15, l9, a], GridSort(field: 'hashrate')),
        ['192.168.2.101', '192.168.2.102', '192.168.2.106'],
      );
    });
  });

  group('search + filters', () {
    final fleet = generatedFleet();

    test('search matches IP substring and model', () {
      final byIp = applyGridView(fleet, search: '192.168.2.15');
      expect(byIp.visible.length, 10); // .150–.159
      final byModel = applyGridView(fleet, search: 'z15');
      expect(byModel.visible.length, 20); // i%3==2, minus the dead unit
      expect(byModel.visible.every((r) => r.model.contains('Z15')), isTrue);
    });

    test('numeric filters: greater / between / equals / not-equals', () {
      final hot = applyGridView(fleet, filters: [
        GridFilter(field: 'maxTemp', op: FilterOp.greater, value: '85'),
      ]);
      // Boards at 88: i % 17 == 0 → i in {0,17,34,51} (i=62 is the
      // dead unit, excluded earlier in the generator).
      expect(hot.visible.length, 4);
      final mid = applyGridView(fleet, filters: [
        GridFilter(
            field: 'maxTemp', op: FilterOp.between, value: '80', value2: '90'),
      ]);
      // maxTemp in [80,90]: board-1 >= 80 for i%30 in 25..29,
      // board-2 >= 80 for i%28 in 24..27 or at 88 (i%17==0),
      // board-3 >= 80 for i%25 in 23..24 — the union is 21 units.
      expect(mid.visible.length, 21);
      expect(mid.visible, containsAll(hot.visible));
      final exact = applyGridView(fleet, filters: [
        GridFilter(field: 'chipsAlive', op: FilterOp.equals, value: '300'),
      ]);
      expect(exact.visible.length, 13); // i % 5 == 0 (dead unit not in the set)
      final notExact = applyGridView(fleet, filters: [
        GridFilter(field: 'chipsAlive', op: FilterOp.notEquals, value: '300'),
      ]);
      expect(notExact.visible.length, 63 - 13);
    });

    test('text filters: contains / anyOf / notIn; bool filters', () {
      final vnish = applyGridView(fleet, filters: [
        GridFilter(field: 'firmware', op: FilterOp.contains, value: 'vnish'),
      ]);
      expect(vnish.visible.length, 21);
      final statuses = applyGridView(fleet, filters: [
        GridFilter(field: 'status', op: FilterOp.anyOf, value: 'OK, ERROR'),
      ]);
      expect(statuses.visible.length, 49 + 1);
      final notOk = applyGridView(fleet, filters: [
        GridFilter(field: 'status', op: FilterOp.notIn, value: 'OK'),
      ]);
      expect(notOk.visible.length, 14);
      final problems = applyGridView(fleet, filters: [
        GridFilter(field: 'hasProblems', op: FilterOp.isTrue),
      ]);
      expect(problems.visible.length, 14); // 13 sick + the dead unit
      final noProblems = applyGridView(fleet, filters: [
        GridFilter(field: 'hasProblems', op: FilterOp.isFalse),
      ]);
      expect(noProblems.visible.length, 49);
    });

    test('a filter on a missing value matches nothing (Board 4 rule)', () {
      final b4 = applyGridView(fleet, filters: [
        GridFilter(field: 'boardTemp4', op: FilterOp.greater, value: '0'),
      ]);
      expect(b4.visible, isEmpty); // the fleet is all 3-board units
      final bad = applyGridView(fleet, filters: [
        GridFilter(field: 'maxTemp', op: FilterOp.greater, value: 'abc'),
      ]);
      expect(bad.visible, isEmpty); // unparseable number: no match
    });

    test('rows AND together; preset JSON round-trips', () {
      final both = applyGridView(fleet, filters: [
        GridFilter(field: 'maxTemp', op: FilterOp.greater, value: '85'),
        GridFilter(field: 'firmware', op: FilterOp.contains, value: 'vnish'),
      ]);
      // Hot units are i in {0,17,34,51}; vnish when i % 3 == 0 → {0, 51}.
      expect(both.visible.map((r) => r.ip).toSet(),
          {'192.168.2.100', '192.168.2.151'});
      final preset = FilterPreset(name: 'Nóng + VNish', filters: [
        GridFilter(field: 'maxTemp', op: FilterOp.greater, value: '85'),
      ]);
      final back = FilterPreset.fromJson(
        jsonDecode(jsonEncode(preset.toJson())) as Map<String, dynamic>,
      );
      expect(back.name, 'Nóng + VNish');
      expect(back.filters.single.field, 'maxTemp');
    });
  });

  group('grouping + selection + isolate', () {
    final fleet = generatedFleet();

    test('group by status: health order, counts sum to the fleet', () {
      final view = applyGridView(fleet, groupBy: GridGroupBy.status);
      expect(view.groups.map((g) => g.key).toList(), ['OK', 'CHECK', 'ERROR']);
      expect(view.groups.map((g) => g.records.length).toList(), [49, 13, 1]);
      expect(view.visible.length, 63);
    });

    test('group by model / firmware', () {
      final byModel = applyGridView(fleet, groupBy: GridGroupBy.model);
      expect(byModel.groups.length, 4); // 3 models + the dead unit's —
      final byFw = applyGridView(fleet, groupBy: GridGroupBy.firmware);
      expect(
        byFw.groups.map((g) => g.key).toSet(),
        {'VNish', 'cgminer RPC'},
      );
    });

    test('selection model: toggle / all / invert / retain / clear', () {
      final sel = MinerSelection();
      sel.toggle('10.0.0.1');
      sel.toggle('10.0.0.2');
      sel.toggle('10.0.0.1');
      expect(sel.selectedIps, {'10.0.0.2'});
      sel.selectAll(fleet.take(3));
      expect(sel.selectedIps.length, 4); // 10.0.0.2 + the fleet's first 3
      sel.invert(fleet.take(3));
      expect(sel.selectedIps, {'10.0.0.2'});
      sel.retainOnly([fakeMiner(ip: '10.0.0.9')]);
      expect(sel.selectedIps, isEmpty);
      sel.toggle('10.0.0.5');
      sel.clear();
      expect(sel.selectedIps, isEmpty);
      expect(sel.isolate, IsolateMode.none);
    });

    test('isolate selected / errors compose with the pipeline', () {
      final sel = MinerSelection()
        ..toggle('192.168.2.100')
        ..toggle('192.168.2.103')
        ..isolate = IsolateMode.selected;
      final only = applyGridView(fleet, selection: sel);
      expect(only.visible.map((r) => r.ip).toSet(),
          {'192.168.2.100', '192.168.2.103'});
      sel.isolate = IsolateMode.errors;
      final errors = applyGridView(fleet, selection: sel);
      expect(errors.visible.length, 14); // 13 CHECK + 1 ERROR
      expect(errors.visible.every((r) => !r.isOk), isTrue);
    });
  });
}

/// A bridge whose fleet is the generated 63-miner set — the
/// grid's scale exercise at widget level.
class _FleetBridge extends MockBridge {
  @override
  Future<ScanResult> scan(String target, {String? credsFile}) async =>
      ScanResult(
        records: generatedFleet(),
        scanned: 254,
        found: 63,
        elapsedS: 1.2,
      );

  @override
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
  }) =>
      scan(name);
}

Directory _tempDir() =>
    Directory.systemTemp.createTempSync('beesky_grid_widget');

Future<void> _pumpHome(
  WidgetTester tester, {
  required Directory tmp,
  BeeSkyBridge? bridge,
}) async {
  tester.view.physicalSize = const Size(1280, 800);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      theme: buildBeeSkyTheme(),
      home: HomePage(
        bridge: bridge ?? MockBridge(),
        credStore: CredStore(primaryDir: tmp, fallbackDir: tmp),
        groupStore: GroupStore(primaryDir: tmp, fallbackDir: tmp),
        gridStore: GridStore(primaryDir: tmp, fallbackDir: tmp),
      ),
    ),
  );
  // Store loads are real IO; let them land, then render.
  await tester.runAsync(
    () => Future<void>.delayed(const Duration(milliseconds: 150)),
  );
  await tester.pump();
  await tester.tap(find.text('Máy đào'));
  await tester.pumpAndSettle();
}

Future<void> _runScan(WidgetTester tester) async {
  await tester.tap(find.text('Quét ngay').first);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 700));
  await tester.pumpAndSettle();
}

/// Let pending store IO land: dart:io completions arrive on the
/// real event loop while their continuations sit on the test's
/// fake microtask queue, so alternate runAsync windows and pumps.
Future<void> _flushIo(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 60)),
    );
    await tester.pump();
  }
}

/// IPs in on-screen top-to-bottom order (the detail panel never
/// renders a bare IP, so text order == row order).
List<String> _ipOrder(WidgetTester tester, List<String> ips) {
  final entries = [
    for (final ip in ips) (ip, tester.getTopLeft(find.text(ip)).dy),
  ]..sort((a, b) => a.$2.compareTo(b.$2));
  return [for (final e in entries) e.$1];
}

void _deleteDir(Directory dir) {
  try {
    dir.deleteSync(recursive: true);
  } on Object {
    // best effort cleanup
  }
}

void registerGridWidgetTests() {
  testWidgets(
      'densities: Gọn keeps the table; Tổng quan is the heat-grid '
      'with the 85 °C red rule; a cell click opens the detail', (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);

    await tester.tap(find.text('Tổng quan'));
    await tester.pumpAndSettle();
    // Overview chrome: colour-metric + cell-size controls appear.
    expect(find.text('Màu: Nhiệt độ'), findsOneWidget);
    expect(find.text('Ô M'), findsOneWidget);
    // The Z15's cell carries its max temp, tinted with the hot red.
    final hot = tester.widget<Text>(find.text('88 °C'));
    expect(hot.style!.color, BeeSkyColors.hotTemp);
    // The S19's 65 °C shows in its cell AND the detail panel.
    expect(find.text('65 °C'), findsWidgets);

    // Clicking the Z15 cell selects it — the detail panel opens.
    await tester.tap(find.text('192.168.2.103'));
    await tester.pumpAndSettle();
    expect(find.text('192.168.2.103 • cgminer RPC'), findsOneWidget);

    // Back to a table density: the familiar rows return.
    await tester.tap(find.text('Gọn'));
    await tester.pumpAndSettle();
    expect(find.text('330/369'), findsOneWidget);
    await tester.tap(find.text('Thoải mái'));
    await tester.pumpAndSettle();
    // The Z15's rate shows in its table row AND the detail panel.
    expect(find.text('1,101.00 ksol/s'), findsWidgets);
  });

  testWidgets('header click sorts (temps asc/desc, nulls last)',
      (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);
    // Close the detail panel: with it open, the NHIỆT header sits
    // past the table's horizontal scroll edge and taps miss it.
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    const ips = [
      '192.168.2.101',
      '192.168.2.102',
      '192.168.2.103',
      '192.168.2.104',
      '192.168.2.105',
    ];
    expect(_ipOrder(tester, ips), ips); // default: IP ascending

    await tester.tap(find.text('NHIỆT'));
    await tester.pumpAndSettle();
    // maxTemp: L9 59 < S19 65 < Whatsminer 87 < Z15 88 < dead
    // (null, last).
    expect(
      _ipOrder(tester, ips),
      [
        '192.168.2.102',
        '192.168.2.101',
        '192.168.2.105',
        '192.168.2.103',
        '192.168.2.104',
      ],
    );
    await tester.tap(find.text('NHIỆT'));
    await tester.pumpAndSettle();
    expect(
      _ipOrder(tester, ips),
      [
        '192.168.2.103',
        '192.168.2.105',
        '192.168.2.101',
        '192.168.2.102',
        '192.168.2.104',
      ],
    );
  });

  testWidgets('search narrows the list and the count line follows',
      (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);
    expect(find.text('Đang hiển thị 5 / 5 máy'), findsOneWidget);

    await tester.enterText(find.byType(TextField).at(1), 'z15');
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 1 / 5 máy'), findsOneWidget);
    expect(find.text('192.168.2.103'), findsOneWidget);
    expect(find.text('192.168.2.102'), findsNothing);
  });

  testWidgets('checkbox selection + isolate modes + hotkeys', (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);

    // Checkbox order: header first, then rows in display order.
    await tester.tap(find.byType(Checkbox).at(2)); // the L9's row
    await tester.pumpAndSettle();
    expect(find.text('Đã chọn 1'), findsOneWidget);

    await tester.tap(find.text('Cô lập: đã chọn'));
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 1 / 5 máy'), findsOneWidget);
    expect(find.text('192.168.2.102'), findsOneWidget);
    expect(find.text('192.168.2.101'), findsNothing);

    await tester.tap(find.text('Cô lập: lỗi'));
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 4 / 5 máy'), findsOneWidget);

    await tester.tap(find.text('Cô lập: lỗi'));
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 5 / 5 máy'), findsOneWidget);

    // Ctrl+A selects everything visible; Esc clears it again.
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.keyA);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.keyA);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pumpAndSettle();
    expect(find.text('Đã chọn 5'), findsOneWidget);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.escape);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.escape);
    await tester.pumpAndSettle();
    expect(find.text('Đã chọn 5'), findsNothing);

    // Ctrl+F puts the keyboard in the search field.
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.keyF);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.keyF);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pumpAndSettle();
    final search = tester.widget<TextField>(find.byType(TextField).at(1));
    expect(search.focusNode!.hasFocus, isTrue);
  });

  testWidgets('filter builder: apply, save a preset, re-apply it',
      (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);

    await tester.tap(find.text('Bộ lọc'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Thêm điều kiện'));
    await tester.pumpAndSettle();
    // The new row defaults to hashrate / "Lớn hơn" — its value
    // field is the dialog's first text field.
    final dialogFields = find.descendant(
      of: find.byType(AlertDialog),
      matching: find.byType(TextField),
    );
    await tester.enterText(dialogFields.first, '100');
    await tester.tap(find.text('Áp dụng'));
    await tester.pumpAndSettle();
    // Native-unit values over 100: the S19 (110.5), the Z15
    // (1101) and the Whatsminer (111.8).
    expect(find.text('Đang hiển thị 3 / 5 máy'), findsOneWidget);
    expect(find.text('Bộ lọc (1)'), findsOneWidget);

    // Save the rows as a named preset, then clear and re-apply.
    await tester.tap(find.text('Bộ lọc (1)'));
    await tester.pumpAndSettle();
    await tester.enterText(dialogFields.last, 'Hashrate cao');
    await tester.tap(find.text('Lưu bộ lọc'));
    await tester.pumpAndSettle();
    expect(find.text('Hashrate cao (1 điều kiện)'), findsOneWidget);
    await tester.tap(find.text('Xóa hết điều kiện'));
    // Two "Áp dụng" now exist (the preset's + the dialog's own);
    // the dialog's action is the last one.
    await tester.tap(find.text('Áp dụng').last);
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 5 / 5 máy'), findsOneWidget);

    await tester.tap(find.text('Bộ lọc'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Áp dụng').first); // the preset's button
    await tester.pumpAndSettle();
    await tester.tap(find.text('Áp dụng').last); // the dialog's button
    await tester.pumpAndSettle();
    expect(find.text('Đang hiển thị 3 / 5 máy'), findsOneWidget);

    // The preset is durable: it is in the grid file on disk.
    await _flushIo(tester);
    final saved = File('${tmp.path}/beesky-grid.json').readAsStringSync();
    expect(saved, contains('Hashrate cao'));
    // Saving a filter preset does not touch the column mode.
    expect(saved, contains('"view_mode": "metric"'));
  });

  testWidgets('columns dialog: enable UPTIME, reset restores defaults',
      (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp);
    await _runScan(tester);
    expect(find.text('UPTIME'), findsNothing);

    await tester.tap(find.text('Cột'));
    await tester.pumpAndSettle();
    // DATA-GAP columns are tagged, never hidden.
    expect(find.text('CHƯA CÓ DỮ LIỆU'), findsWidgets);
    await tester.scrollUntilVisible(
      find.text('UPTIME'),
      120,
      scrollable: find
          .descendant(
            of: find.byType(AlertDialog),
            matching: find.byType(Scrollable),
          )
          .first,
    );
    final row = find.ancestor(
      of: find.text('UPTIME'),
      matching: find.byType(Row),
    );
    await tester.tap(
      find.descendant(of: row, matching: find.byType(Checkbox)),
    );
    await tester.tap(find.text('Lưu'));
    await tester.pumpAndSettle();
    expect(find.text('UPTIME'), findsOneWidget); // the table header

    await _flushIo(tester);
    final saved = File('${tmp.path}/beesky-grid.json').readAsStringSync();
    expect(saved, contains('"uptime"'));

    await tester.tap(find.text('Cột'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Đặt lại mặc định'));
    await tester.tap(find.text('Lưu'));
    await tester.pumpAndSettle();
    expect(find.text('UPTIME'), findsNothing);
  });

  testWidgets(
      'grouping by status renders header rows with counts '
      '(63-miner fleet)', (tester) async {
    final tmp = _tempDir();
    addTearDown(() => _deleteDir(tmp));
    await _pumpHome(tester, tmp: tmp, bridge: _FleetBridge());
    await _runScan(tester);
    expect(find.text('Đang hiển thị 63 / 63 máy'), findsOneWidget);

    await tester.tap(find.text('Nhóm: Không nhóm'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Nhóm: Trạng thái'));
    await tester.pumpAndSettle();
    expect(find.text('49 máy'), findsOneWidget);
    // The later group headers sit below 49 rows of lazy list —
    // scroll each into existence before asserting on it.
    await tester.scrollUntilVisible(
      find.text('13 máy'),
      200,
      scrollable: find.descendant(
        of: find.byType(ListView).first,
        matching: find.byType(Scrollable),
      ),
    );
    expect(find.text('13 máy'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('1 máy'),
      200,
      scrollable: find.descendant(
        of: find.byType(ListView).first,
        matching: find.byType(Scrollable),
      ),
    );
    expect(find.text('1 máy'), findsOneWidget);
  });
}
