import 'dart:convert';
import 'dart:io';

import 'models.dart';
import 'presets.dart';

/// The data-grid miners list (v0.25) — the HashCore Toolkit's list
/// machinery ported per docs/grid-mapping.md: configurable columns,
/// three densities (the third is the Overview heat-grid), three
/// data modes, header sorting, text search, an AND filter builder
/// with saveable presets, grouping, and a checkbox selection model
/// (built for the v0.26 Operations bar to consume).
///
/// Everything in this file is pure model + persistence — no widgets
/// (the dialogs live in grid_dialogs.dart, the rendering in
/// home_page.dart) — so the whole pipeline is unit-testable.

// --------------------------------------------------------------------
// View axes (HashCore: miner_list_view_type × miner_list_view_mode)
// --------------------------------------------------------------------

/// Density / view type: comfortable rows, compact rows, or the
/// Overview heat-grid. HashCore names: Normal / Compact / Overview.
enum GridViewType { normal, compact, overview }

/// Data mode: the fixed Metric column set, the fixed Pools column
/// set, or the user's own Custom column configuration.
enum GridViewMode { metric, pools, custom }

/// What colours the Overview cells (HashCore miner_list_overview_mode).
enum OverviewColorMode { temperature, hashrate }

/// Overview cell size (HashCore miner_list_overview_size: small /
/// medium="Default" / large).
enum OverviewCellSize { small, medium, large }

// --------------------------------------------------------------------
// Columns
// --------------------------------------------------------------------

enum GridColumnKind { text, numeric, rate, temps, status }

/// One column of the grid universe. [dataGap] columns have no
/// BeeSky data source yet (docs/grid-mapping.md §9): they can be
/// enabled and honestly render "—", and the columns dialog tags
/// them "chưa có dữ liệu" instead of faking values.
class GridColumnDef {
  final String id;
  final String label;
  final int flex;
  final GridColumnKind kind;
  final bool dataGap;

  /// Combined per-board temperature cell (the v0.22 NHIỆT column) —
  /// rendered by the row's temp-cell widget, not a plain text cell.
  final bool isTemps;

  /// Status chip cell (OK / CHECK / ERROR pill).
  final bool isStatus;

  const GridColumnDef(
    this.id,
    this.label,
    this.flex, {
    this.kind = GridColumnKind.text,
    this.dataGap = false,
    this.isTemps = false,
    this.isStatus = false,
  });

  /// The cell's text for [rec] (temps/status columns render widgets
  /// in the table; this text still serves sort/filter/tests).
  String textOf(MinerRecord rec) => switch (id) {
        'ip' => rec.ip,
        'model' => rec.model,
        'firmware' => rec.sourceLabel,
        'hashrate' => rec.rateText,
        'chips' => rec.chipsText,
        'temps' => rec.boardTemps.isEmpty
            ? rec.tempText
            : rec.boardTemps.map((t) => '${t.toStringAsFixed(0)}°').join(' '),
        'fans' => rec.fansText,
        'status' => rec.statusLabel,
        'mac' => rec.mac ?? '—',
        'serial' => '—',
        'uptime' => rec.uptimeText,
        'hashrateRt' => rec.rateRtText,
        'efficiency' => rec.efficiencyText,
        'algorithm' => rec.algorithmLabel,
        'power' => rec.powerText,
        'boards' => '${rec.chains.length}',
        'badBoards' => '${rec.badBoards}',
        'errorCode' => rec.errorCodesText.isEmpty ? '—' : rec.errorCodesText,
        'boardTemp1' => rec.boardTempTextAt(0),
        'boardTemp2' => rec.boardTempTextAt(1),
        'boardTemp3' => rec.boardTempTextAt(2),
        'boardTemp4' => rec.boardTempTextAt(3),
        'credLabel' => rec.credLabel ?? '—',
        'pool1Url' => _dash(rec.poolUrlAt(0)),
        'pool1Worker' => _dash(rec.poolWorkerAt(0)),
        'pool2Url' => _dash(rec.poolUrlAt(1)),
        'pool2Worker' => _dash(rec.poolWorkerAt(1)),
        'pool3Url' => _dash(rec.poolUrlAt(2)),
        'pool3Worker' => _dash(rec.poolWorkerAt(2)),
        'note' => _dash(rec.note),
        _ => '—',
      };

  static String _dash(String s) => s.isEmpty ? '—' : s;

  /// Sort key for [rec]; null sorts last in BOTH directions.
  /// (Keys are heterogeneous — num, String, _IpKey, _RateKey —
  /// compared pairwise by [compareGridKeys].)
  Object? sortKeyOf(MinerRecord rec) => switch (id) {
        'ip' => _IpKey(rec.ip),
        'hashrate' => _RateKey(rec.rateSortKey),
        'hashrateRt' =>
          _RateKey(rec.rateRt == null ? null : (0, rec.rateRt!.$1 * 1e12)),
        'temps' => rec.maxTempC,
        'chips' => rec.chipsTotal == 0
            ? null
            : rec.chipsAlive * 1000000 + rec.chipsTotal,
        'fans' => rec.fansRpm.isEmpty
            ? null
            : rec.fansRpm.reduce((a, b) => a > b ? a : b),
        'status' => switch (rec.statusLabel) {
            'OK' => 0,
            'CHECK' => 1,
            _ => 2,
          },
        'uptime' => rec.elapsedS == 0 ? null : rec.elapsedS,
        'power' => rec.powerW,
        'efficiency' => rec.efficiencyJTh,
        'boards' => rec.chains.length,
        'badBoards' => rec.badBoards,
        'boardTemp1' => rec.boardTempAt(0),
        'boardTemp2' => rec.boardTempAt(1),
        'boardTemp3' => rec.boardTempAt(2),
        'boardTemp4' => rec.boardTempAt(3),
        _ => textOf(rec).toLowerCase(),
      };
}

/// IP sort key with octet-numeric comparison (models.compareIp).
class _IpKey implements Comparable<_IpKey> {
  final String ip;
  const _IpKey(this.ip);
  @override
  int compareTo(_IpKey other) => compareIp(ip, other.ip);
}

/// Rate sort key: family rank first, then value inside the family.
class _RateKey implements Comparable<_RateKey> {
  final (int, double)? key;
  const _RateKey(this.key);
  @override
  int compareTo(_RateKey other) {
    final a = key;
    final b = other.key;
    if (a == null && b == null) return 0;
    if (a == null) return 1;
    if (b == null) return -1;
    final byFamily = a.$1.compareTo(b.$1);
    return byFamily != 0 ? byFamily : a.$2.compareTo(b.$2);
  }
}

/// Pairwise comparison for the heterogeneous sort keys.
int compareGridKeys(Object a, Object b) {
  if (a is _IpKey && b is _IpKey) return a.compareTo(b);
  if (a is _RateKey && b is _RateKey) return a.compareTo(b);
  if (a is num && b is num) return a.compareTo(b);
  return '$a'.compareTo('$b');
}

/// The full column universe — every column BeeSky records can feed,
/// plus the named DATA-GAP columns (docs/grid-mapping.md §3.2).
/// Order here is the FACTORY order; the first eight are the v0.24
/// default set, in the v0.24 order, with the v0.24 flexes.
const List<GridColumnDef> gridColumnUniverse = [
  GridColumnDef('ip', 'IP', 3),
  GridColumnDef('model', 'MODEL', 4),
  GridColumnDef('firmware', 'NGUỒN', 3),
  GridColumnDef('hashrate', 'HASHRATE', 3, kind: GridColumnKind.rate),
  GridColumnDef('chips', 'CHIP', 2, kind: GridColumnKind.numeric),
  GridColumnDef('temps', 'NHIỆT', 3, isTemps: true),
  GridColumnDef('fans', 'QUẠT', 3),
  GridColumnDef('status', 'TRẠNG THÁI', 2, isStatus: true),
  GridColumnDef('mac', 'MAC', 3), // v0.35: core fills it from the ARP table
  GridColumnDef('serial', 'S/N', 3, dataGap: true),
  GridColumnDef('uptime', 'UPTIME', 2, kind: GridColumnKind.numeric),
  GridColumnDef('hashrateRt', 'HASHRATE RT', 3, kind: GridColumnKind.rate),
  GridColumnDef('efficiency', 'HIỆU SUẤT', 2, kind: GridColumnKind.numeric),
  GridColumnDef('algorithm', 'THUẬT TOÁN', 2),
  GridColumnDef('power', 'ĐIỆN', 2, kind: GridColumnKind.numeric),
  GridColumnDef('boards', 'BOARD', 1, kind: GridColumnKind.numeric),
  GridColumnDef('badBoards', 'BOARD LỖI', 2, kind: GridColumnKind.numeric),
  GridColumnDef('errorCode', 'MÃ LỖI', 3),
  GridColumnDef('boardTemp1', 'BOARD 1', 1, kind: GridColumnKind.numeric),
  GridColumnDef('boardTemp2', 'BOARD 2', 1, kind: GridColumnKind.numeric),
  GridColumnDef('boardTemp3', 'BOARD 3', 1, kind: GridColumnKind.numeric),
  GridColumnDef('boardTemp4', 'BOARD 4', 1, kind: GridColumnKind.numeric),
  GridColumnDef('credLabel', 'ĐĂNG NHẬP', 3),
  // Pool columns: a DATA-GAP until v0.27; since v0.28 the core
  // fills record pools for vnish + cgminer scans, so the gap
  // flags are OFF (stock rows still render "—" — no scan-time
  // source there, docs/presets-ipreport-mapping.md §4).
  GridColumnDef('pool1Url', 'POOL 1', 4),
  GridColumnDef('pool1Worker', 'POOL 1 WORKER', 3),
  GridColumnDef('pool2Url', 'POOL 2', 4),
  GridColumnDef('pool2Worker', 'POOL 2 WORKER', 3),
  GridColumnDef('pool3Url', 'POOL 3', 4),
  GridColumnDef('pool3Worker', 'POOL 3 WORKER', 3),
  // The device note (v0.27) as a column (v0.28): fed by the
  // app-side note decoration on the record, never the wire.
  GridColumnDef('note', 'GHI CHÚ', 4),
];

GridColumnDef? gridColumnById(String id) {
  for (final c in gridColumnUniverse) {
    if (c.id == id) return c;
  }
  return null;
}

/// The v0.24 default set — "Đặt lại mặc định" restores exactly
/// this visibility + the factory order above.
const List<String> gridDefaultVisible = [
  'ip',
  'model',
  'firmware',
  'hashrate',
  'chips',
  'temps',
  'fans',
  'status',
];

/// The fixed Pools-mode column set (IP and status stay for
/// orientation — HashCore's pools mode is pool-CENTRIC, and a row
/// you cannot identify or triage is useless).
const List<String> gridPoolsColumns = [
  'ip',
  'model',
  'status',
  'pool1Url',
  'pool1Worker',
  'pool2Url',
  'pool2Worker',
  'pool3Url',
  'pool3Worker',
];

// --------------------------------------------------------------------
// Sorting
// --------------------------------------------------------------------
class GridSort {
  String field; // column id
  bool ascending;
  GridSort({this.field = 'ip', this.ascending = true});

  Map<String, dynamic> toJson() => {'field': field, 'asc': ascending};

  factory GridSort.fromJson(Map<String, dynamic> json) => GridSort(
        field: (json['field'] as String?) ?? 'ip',
        ascending: (json['asc'] as bool?) ?? true,
      );
}

/// Compare two records by a column's sort key; null keys sort LAST
/// in both directions (an unknown value is never "smallest").
int compareByColumn(MinerRecord a, MinerRecord b, GridSort sort) {
  final def = gridColumnById(sort.field);
  if (def == null) return 0;
  final ka = def.sortKeyOf(a);
  final kb = def.sortKeyOf(b);
  final int c;
  if (ka == null && kb == null) {
    c = 0;
  } else if (ka == null) {
    return 1; // nulls last in BOTH directions
  } else if (kb == null) {
    return -1;
  } else {
    c = compareGridKeys(ka, kb);
  }
  return sort.ascending ? c : -c;
}

// --------------------------------------------------------------------
// Filters (HashCore MinerFilter: numeric / range / string / bool)
// --------------------------------------------------------------------

enum FilterFieldKind { numeric, text, bool }

enum FilterOp {
  greater,
  less,
  equals,
  notEquals,
  between,
  contains,
  notContains,
  anyOf,
  notIn,
  isTrue,
  isFalse,
}

extension FilterOpLabel on FilterOp {
  String get label => switch (this) {
        FilterOp.greater => 'Lớn hơn',
        FilterOp.less => 'Nhỏ hơn',
        FilterOp.equals => 'Bằng',
        FilterOp.notEquals => 'Khác',
        FilterOp.between => 'Trong khoảng',
        FilterOp.contains => 'Chứa',
        FilterOp.notContains => 'Không chứa',
        FilterOp.anyOf => 'Là một trong',
        FilterOp.notIn => 'Không thuộc',
        FilterOp.isTrue => 'Đúng (có)',
        FilterOp.isFalse => 'Sai (không)',
      };
}

List<FilterOp> filterOpsFor(FilterFieldKind kind) => switch (kind) {
      FilterFieldKind.numeric => const [
          FilterOp.greater,
          FilterOp.less,
          FilterOp.equals,
          FilterOp.notEquals,
          FilterOp.between,
        ],
      FilterFieldKind.text => const [
          FilterOp.contains,
          FilterOp.notContains,
          FilterOp.anyOf,
          FilterOp.notIn,
        ],
      FilterFieldKind.bool => const [FilterOp.isTrue, FilterOp.isFalse],
    };

/// One filterable field: how to read it off a record. A null value
/// matches NO operator (a Board-4 filter never matches a 3-board
/// machine) — BeeSky's stated rule; HashCore's is UNKNOWN.
class FilterFieldDef {
  final String id;
  final String label;
  final FilterFieldKind kind;
  final Object? Function(MinerRecord rec) read;
  const FilterFieldDef(this.id, this.label, this.kind, this.read);
}

final List<FilterFieldDef> gridFilterFields = [
  FilterFieldDef('ip', 'IP', FilterFieldKind.text, (r) => r.ip),
  FilterFieldDef('model', 'Model', FilterFieldKind.text, (r) => r.model),
  FilterFieldDef('firmware', 'Nguồn (firmware)', FilterFieldKind.text,
      (r) => '${r.sourceLabel} ${r.source}'),
  FilterFieldDef(
      'status', 'Trạng thái', FilterFieldKind.text, (r) => r.statusLabel),
  FilterFieldDef(
      'algorithm', 'Thuật toán', FilterFieldKind.text, (r) => r.algorithmLabel),
  FilterFieldDef(
      'errorCode', 'Mã lỗi', FilterFieldKind.text, (r) => r.errorCodesText),
  FilterFieldDef(
      'credLabel', 'Đăng nhập', FilterFieldKind.text, (r) => r.credLabel),
  FilterFieldDef('hashrate', 'Hashrate (đơn vị gốc)', FilterFieldKind.numeric,
      (r) => r.rateValue),
  FilterFieldDef('maxTemp', 'Nhiệt độ cao nhất (°C)', FilterFieldKind.numeric,
      (r) => r.maxTempC),
  FilterFieldDef('power', 'Điện (W)', FilterFieldKind.numeric, (r) => r.powerW),
  FilterFieldDef('efficiency', 'Hiệu suất (J/TH)', FilterFieldKind.numeric,
      (r) => r.efficiencyJTh),
  FilterFieldDef(
      'chipsAlive', 'Chip sống', FilterFieldKind.numeric, (r) => r.chipsAlive),
  FilterFieldDef('chipsMissing', 'Chip thiếu', FilterFieldKind.numeric,
      (r) => r.chipsTotal - r.chipsAlive),
  FilterFieldDef('uptimeH', 'Uptime (giờ)', FilterFieldKind.numeric,
      (r) => r.elapsedS == 0 ? null : r.elapsedS / 3600.0),
  FilterFieldDef('boardTemp1', 'Nhiệt Board 1 (°C)', FilterFieldKind.numeric,
      (r) => r.boardTempAt(0)),
  FilterFieldDef('boardTemp2', 'Nhiệt Board 2 (°C)', FilterFieldKind.numeric,
      (r) => r.boardTempAt(1)),
  FilterFieldDef('boardTemp3', 'Nhiệt Board 3 (°C)', FilterFieldKind.numeric,
      (r) => r.boardTempAt(2)),
  FilterFieldDef('boardTemp4', 'Nhiệt Board 4 (°C)', FilterFieldKind.numeric,
      (r) => r.boardTempAt(3)),
  FilterFieldDef('hasProblems', 'Có vấn đề', FilterFieldKind.bool,
      (r) => r.issues.isNotEmpty),
  FilterFieldDef('hasFetchError', 'Lỗi kết nối', FilterFieldKind.bool,
      (r) => r.hasFetchError),
  FilterFieldDef('isHot', 'Quá nhiệt (≥85 °C)', FilterFieldKind.bool,
      (r) => (r.maxTempC ?? 0) >= tempLimitC),
];

FilterFieldDef? filterFieldById(String id) {
  for (final f in gridFilterFields) {
    if (f.id == id) return f;
  }
  return null;
}

/// One filter row. [value2] is the upper bound for `between`.
/// Values are stored as typed text, exactly as the user entered
/// them; numeric parsing accepts "." or "," as decimal separator.
class GridFilter {
  String field;
  FilterOp op;
  String value;
  String value2;
  GridFilter({
    required this.field,
    required this.op,
    this.value = '',
    this.value2 = '',
  });

  GridFilter copy() =>
      GridFilter(field: field, op: op, value: value, value2: value2);

  Map<String, dynamic> toJson() => {
        'field': field,
        'op': op.name,
        'value': value,
        if (value2.isNotEmpty) 'value2': value2,
      };

  factory GridFilter.fromJson(Map<String, dynamic> json) {
    final field = (json['field'] as String?) ?? 'ip';
    final def = filterFieldById(field);
    final kind = def?.kind ?? FilterFieldKind.text;
    var op = FilterOp.values.asNameMap()[json['op'] as String?];
    if (op == null || !filterOpsFor(kind).contains(op)) {
      op = filterOpsFor(kind).first;
    }
    return GridFilter(
      field: field,
      op: op,
      value: (json['value'] as String?) ?? '',
      value2: (json['value2'] as String?) ?? '',
    );
  }

  static double? _num(String s) =>
      double.tryParse(s.trim().replaceAll(',', '.'));

  bool matches(MinerRecord rec) {
    final def = filterFieldById(field);
    if (def == null) return false;
    final raw = def.read(rec);
    if (raw == null) return false;
    return switch (def.kind) {
      FilterFieldKind.bool => op == FilterOp.isTrue ? raw == true : raw != true,
      FilterFieldKind.numeric => _matchNumeric((raw as num).toDouble()),
      FilterFieldKind.text => _matchText('$raw'),
    };
  }

  bool _matchNumeric(double actual) {
    final v = _num(value);
    if (v == null) return false;
    return switch (op) {
      FilterOp.greater => actual > v,
      FilterOp.less => actual < v,
      FilterOp.equals => actual == v,
      FilterOp.notEquals => actual != v,
      FilterOp.between => _between(actual, v),
      _ => false,
    };
  }

  bool _between(double actual, double lo) {
    final hi = _num(value2);
    if (hi == null) return false;
    return actual >= lo && actual <= hi;
  }

  bool _matchText(String actual) {
    final a = actual.toLowerCase();
    final v = value.trim().toLowerCase();
    List<String> parts() =>
        v.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
    return switch (op) {
      FilterOp.contains => a.contains(v),
      FilterOp.notContains => !a.contains(v),
      FilterOp.anyOf => parts().any((p) => a == p),
      FilterOp.notIn => !parts().any((p) => a == p),
      _ => false,
    };
  }
}

/// A named, saved filter set (HashCore FilterPreset: name +
/// optional description + the filter list).
class FilterPreset {
  String name;
  String description;
  List<GridFilter> filters;
  FilterPreset(
      {required this.name, this.description = '', required this.filters});

  Map<String, dynamic> toJson() => {
        'name': name,
        if (description.isNotEmpty) 'description': description,
        'filters': filters.map((f) => f.toJson()).toList(),
      };

  factory FilterPreset.fromJson(Map<String, dynamic> json) => FilterPreset(
        name: (json['name'] as String?) ?? '',
        description: (json['description'] as String?) ?? '',
        filters: ((json['filters'] as List<dynamic>?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(GridFilter.fromJson)
            .toList(),
      );

  FilterPreset copy() => FilterPreset(
        name: name,
        description: description,
        filters: filters.map((f) => f.copy()).toList(),
      );
}

// --------------------------------------------------------------------
// Selection + isolate (consumed by the v0.26 Operations bar)
// --------------------------------------------------------------------

enum IsolateMode { none, selected, errors }

/// The selection model: which miners are checkbox-selected, plus
/// the isolate mode. Keyed by IP (a record's identity in a scan).
/// v0.26's Operations bar reads [selectedIps] from here — it does
/// not re-derive selection from the widgets.
class MinerSelection {
  final Set<String> selectedIps = {};
  IsolateMode isolate = IsolateMode.none;

  bool isSelected(String ip) => selectedIps.contains(ip);

  void toggle(String ip) {
    if (!selectedIps.remove(ip)) selectedIps.add(ip);
  }

  void selectAll(Iterable<MinerRecord> records) {
    selectedIps.addAll(records.map((r) => r.ip));
  }

  void invert(Iterable<MinerRecord> records) {
    for (final r in records) {
      toggle(r.ip);
    }
  }

  /// Drop selections for miners no longer in the fleet (a rescan
  /// replaced the record list).
  void retainOnly(Iterable<MinerRecord> records) {
    final live = records.map((r) => r.ip).toSet();
    selectedIps.removeWhere((ip) => !live.contains(ip));
  }

  void clear() {
    selectedIps.clear();
    isolate = IsolateMode.none;
  }
}

// --------------------------------------------------------------------
// Grouping + the view pipeline
// --------------------------------------------------------------------

enum GridGroupBy { none, status, model, firmware }

extension GridGroupByLabel on GridGroupBy {
  String get label => switch (this) {
        GridGroupBy.none => 'Không nhóm',
        GridGroupBy.status => 'Trạng thái',
        GridGroupBy.model => 'Model',
        GridGroupBy.firmware => 'Firmware',
      };

  /// Group key for a record (null when grouping is off).
  String? keyOf(MinerRecord rec) => switch (this) {
        GridGroupBy.none => null,
        GridGroupBy.status => rec.statusLabel,
        GridGroupBy.model => rec.model,
        GridGroupBy.firmware => rec.sourceLabel,
      };

  /// Display order of group keys: statuses in health order
  /// (OK → CHECK → ERROR), everything else alphabetical.
  int keyRank(String key) => switch (this) {
        GridGroupBy.status => switch (key) {
            'OK' => 0,
            'CHECK' => 1,
            _ => 2,
          },
        _ => 0,
      };
}

/// One rendered group: header key + its miners (sorted).
class MinerGroup {
  final String key;
  final List<MinerRecord> records;
  const MinerGroup(this.key, this.records);
}

/// The visible result of the whole pipeline — what the table /
/// heat-grid renders and what the result-count line reads.
class GridViewResult {
  /// Records after search + filters + isolate, sorted. Grouping
  /// does not change this list, only its presentation.
  final List<MinerRecord> visible;

  /// Presentation groups (empty when grouping is off).
  final List<MinerGroup> groups;

  /// How many records the last scan produced (pre-pipeline).
  final int total;

  const GridViewResult({
    required this.visible,
    required this.groups,
    required this.total,
  });

  bool get isGrouped => groups.isNotEmpty;
}

/// The pipeline, in HashCore's mental order: text search, then the
/// filter builder (rows AND-ed), then isolate, then sort, then
/// grouping for presentation. Pure — the widget layer just renders.
GridViewResult applyGridView(
  List<MinerRecord> records, {
  String search = '',
  List<GridFilter> filters = const [],
  MinerSelection? selection,
  GridSort? sort,
  GridGroupBy groupBy = GridGroupBy.none,
}) {
  var out = records;
  final q = search.trim().toLowerCase();
  if (q.isNotEmpty) {
    out = out.where((r) => r.searchHaystack.contains(q)).toList();
  }
  if (filters.isNotEmpty) {
    out = out
        .where((r) => filters.every((f) => f.matches(r)))
        .toList(growable: false);
  }
  final sel = selection;
  if (sel != null && sel.isolate == IsolateMode.selected) {
    out = out.where((r) => sel.isSelected(r.ip)).toList();
  } else if (sel != null && sel.isolate == IsolateMode.errors) {
    out = out.where((r) => !r.isOk).toList();
  }
  final sorted = [...out];
  if (sort != null) {
    sorted.sort((a, b) => compareByColumn(a, b, sort));
  }
  var groups = <MinerGroup>[];
  if (groupBy != GridGroupBy.none) {
    final byKey = <String, List<MinerRecord>>{};
    for (final r in sorted) {
      byKey.putIfAbsent(groupBy.keyOf(r)!, () => []).add(r);
    }
    final keys = byKey.keys.toList()
      ..sort((a, b) {
        final rank = groupBy.keyRank(a).compareTo(groupBy.keyRank(b));
        return rank != 0 ? rank : a.compareTo(b);
      });
    groups = [for (final k in keys) MinerGroup(k, byKey[k]!)];
  }
  return GridViewResult(visible: sorted, groups: groups, total: records.length);
}

// --------------------------------------------------------------------
// Grid configuration + persistence (beesky-grid.json)
// --------------------------------------------------------------------

/// Everything about the grid that survives a restart. The ACTIVE
/// filter rows are session-only (HashCore's persistence of them is
/// UNKNOWN) — presets are the durable form of a filter.
class GridConfig {
  List<String> columnOrder; // every known column id, display order
  Set<String> visibleColumns; // the Custom-mode set
  GridViewType viewType;
  GridViewMode viewMode;
  OverviewColorMode overviewColor;
  OverviewCellSize overviewSize;
  GridSort sort;
  GridGroupBy groupBy;
  List<FilterPreset> filterPresets;

  /// Pool presets (v0.28) share this store with the filter
  /// presets — HashCore's Presets center holds both kinds in
  /// one place; BeeSky's one file mirrors that (mapping §3).
  List<PoolPreset> poolPresets;

  GridConfig({
    List<String>? columnOrder,
    Set<String>? visibleColumns,
    this.viewType = GridViewType.normal,
    this.viewMode = GridViewMode.metric,
    this.overviewColor = OverviewColorMode.temperature,
    this.overviewSize = OverviewCellSize.medium,
    GridSort? sort,
    this.groupBy = GridGroupBy.none,
    List<FilterPreset>? filterPresets,
    List<PoolPreset>? poolPresets,
  })  : columnOrder = columnOrder ?? _factoryOrder(),
        visibleColumns = visibleColumns ?? {...gridDefaultVisible},
        sort = sort ?? GridSort(),
        filterPresets = filterPresets ?? [],
        poolPresets = poolPresets ?? [];

  static List<String> _factoryOrder() =>
      gridColumnUniverse.map((c) => c.id).toList();

  /// The columns the CURRENT mode shows, in display order: the
  /// fixed set for Metric/Pools, the user's set for Custom.
  List<GridColumnDef> get activeColumns {
    final ids = switch (viewMode) {
      GridViewMode.metric => gridDefaultVisible,
      GridViewMode.pools => gridPoolsColumns,
      GridViewMode.custom =>
        columnOrder.where((id) => visibleColumns.contains(id)).toList(),
    };
    return [
      for (final id in ids)
        if (gridColumnById(id) != null) gridColumnById(id)!,
    ];
  }

  /// "Đặt lại mặc định" — restores the factory column order +
  /// the v0.24 default set. Touches columns ONLY (HashCore's
  /// columns_reset lives in the columns menu).
  void resetColumns() {
    columnOrder = _factoryOrder();
    visibleColumns = {...gridDefaultVisible};
  }

  /// Move a column one step up (-1) or down (+1) in the order.
  void moveColumn(String id, int delta) {
    final i = columnOrder.indexOf(id);
    final j = i + delta;
    if (i < 0 || j < 0 || j >= columnOrder.length) return;
    columnOrder[i] = columnOrder[j];
    columnOrder[j] = id;
  }

  Map<String, dynamic> toJson() => {
        'version': 1,
        'columns': {'order': columnOrder, 'visible': visibleColumns.toList()},
        'view_type': viewType.name,
        'view_mode': viewMode.name,
        'overview': {'color': overviewColor.name, 'size': overviewSize.name},
        'sort': sort.toJson(),
        'group_by': groupBy.name,
        'filter_presets': filterPresets.map((p) => p.toJson()).toList(),
        'pool_presets': poolPresets.map((p) => p.toJson()).toList(),
      };

  factory GridConfig.fromJson(Map<String, dynamic> json) {
    final cfg = GridConfig();
    final cols = json['columns'] as Map<String, dynamic>?;
    if (cols != null) {
      final order = ((cols['order'] as List<dynamic>?) ?? const [])
          .whereType<String>()
          .where((id) => gridColumnById(id) != null)
          .toList();
      // Columns a newer build adds join the tail of the order.
      for (final def in gridColumnUniverse) {
        if (!order.contains(def.id)) order.add(def.id);
      }
      if (order.isNotEmpty) cfg.columnOrder = order;
      final visible = ((cols['visible'] as List<dynamic>?) ?? const [])
          .whereType<String>()
          .where((id) => gridColumnById(id) != null)
          .toSet();
      if (visible.isNotEmpty) cfg.visibleColumns = visible;
    }
    cfg.viewType =
        GridViewType.values.asNameMap()[json['view_type']] ?? cfg.viewType;
    cfg.viewMode =
        GridViewMode.values.asNameMap()[json['view_mode']] ?? cfg.viewMode;
    final ov = json['overview'] as Map<String, dynamic>?;
    if (ov != null) {
      cfg.overviewColor = OverviewColorMode.values.asNameMap()[ov['color']] ??
          cfg.overviewColor;
      cfg.overviewSize =
          OverviewCellSize.values.asNameMap()[ov['size']] ?? cfg.overviewSize;
    }
    if (json['sort'] is Map<String, dynamic>) {
      cfg.sort = GridSort.fromJson(json['sort'] as Map<String, dynamic>);
    }
    cfg.groupBy =
        GridGroupBy.values.asNameMap()[json['group_by']] ?? cfg.groupBy;
    cfg.filterPresets = ((json['filter_presets'] as List<dynamic>?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(FilterPreset.fromJson)
        .where((p) => p.name.isNotEmpty)
        .toList();
    cfg.poolPresets = ((json['pool_presets'] as List<dynamic>?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(PoolPreset.fromJson)
        .where((p) => p.name.isNotEmpty)
        .toList();
    return cfg;
  }
}

/// Persistence for the grid file — the CredStore strategy mirrored:
/// `beesky-grid.json` NEXT TO the app executable, with
/// `%APPDATA%\BeeSky\` as the fallback. A corrupt file reads as
/// factory defaults (a view-settings file must never brick the app).
class GridStore {
  final Directory primaryDir;
  final Directory fallbackDir;

  const GridStore({required this.primaryDir, required this.fallbackDir});

  factory GridStore.appDefault() {
    final exeDir = File(Platform.resolvedExecutable).parent;
    final appData = Platform.environment['APPDATA'];
    final fallback = (appData != null && appData.isNotEmpty)
        ? Directory('$appData${Platform.pathSeparator}BeeSky')
        : Directory(
            '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
    return GridStore(primaryDir: exeDir, fallbackDir: fallback);
  }

  static const fileName = 'beesky-grid.json';

  File get primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  /// (config, source) — source is the file read, or null when no
  /// file exists yet / none parsed.
  Future<(GridConfig, File?)> load() async {
    for (final file in [primaryFile, fallbackFile]) {
      try {
        if (!file.existsSync()) continue;
        final decoded = jsonDecode(file.readAsStringSync());
        if (decoded is Map<String, dynamic>) {
          return (GridConfig.fromJson(decoded), file);
        }
      } on Object {
        // Corrupt settings: fall through to the next candidate,
        // then to factory defaults.
      }
    }
    return (GridConfig(), null);
  }

  /// Writes to the primary file, falling back when the bundle
  /// folder refuses (Program Files installs). Returns the file
  /// written. Throws FileSystemException when both refuse.
  Future<File> save(GridConfig config) async {
    final text = const JsonEncoder.withIndent('  ').convert(config.toJson());
    for (final file in [primaryFile, fallbackFile]) {
      try {
        await file.parent.create(recursive: true);
        await file.writeAsString(text);
        return file;
      } on FileSystemException {
        // Try the fallback location.
      }
    }
    throw const FileSystemException('không ghi được beesky-grid.json');
  }
}
