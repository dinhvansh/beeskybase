/// Device detail data (v0.27) — the HashCore device-info dialog's
/// tabs ported per docs/device-detail-mapping.md.
///
/// Three data sources, three honesty rules:
///   * INSPECT — pools / fans / per-board detail fetched on demand
///     for ONE device through the core's `inspect --json` bridge
///     (the scan record does not carry them). Every section is
///     explicitly supported or unsupported-with-a-reason; nothing
///     renders as data that the core did not report.
///   * HISTORY — LOCAL chart samples: one per device per finished
///     scan, persisted to beesky-history.json. A device's series
///     is drawn alone, in its own native unit — never aggregated
///     across units (the v0.20 lesson).
///   * NOTES — per-device notes in beesky-notes.json, keyed like
///     history (MAC when a record ever carries one, else IP).
library;

import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'models.dart';
import 'theme.dart';

// --------------------------------------------------------------------
// Inspect wire models (beesky/core/inspect.py is the producer)
// --------------------------------------------------------------------

class InspectChip {
  final int pos;
  final double? hr;
  final String? grade; // vnish: grey | orange | red
  final double? temp;
  const InspectChip({required this.pos, this.hr, this.grade, this.temp});

  factory InspectChip.fromJson(Map<String, dynamic> json) => InspectChip(
        pos: ((json['pos'] as num?) ?? 0).toInt(),
        hr: (json['hr'] as num?)?.toDouble(),
        grade: json['grade'] as String?,
        temp: (json['temp'] as num?)?.toDouble(),
      );
}

class InspectBoard {
  final int index;
  final int chipsTotal;

  /// cgminer/stock: chips the acs string reports alive ('o').
  /// Null on vnish boards, which report grade buckets instead.
  final int? chipsOk;

  /// vnish grade buckets (grey/orange/red) — HashCore's
  /// STABLE / SLOW / CRITICAL. Null on cgminer/stock boards:
  /// the acs alphabet has no documented grade semantics, so
  /// the split is a structural DATA-GAP there (mapping §5.1).
  final int? stable;
  final int? slow;
  final int? critical;

  final List<int> deadPositions;
  final double? chipTempC;
  final double? pcbTempC; // vnish only
  final double? tempC; // cgminer/stock chain temp
  final String? acs; // cgminer/stock raw per-chip string
  final Map<String, int> otherChars; // non-'o' acs character counts
  final List<InspectChip>? chips; // vnish /boards list, when served

  const InspectBoard({
    required this.index,
    required this.chipsTotal,
    this.chipsOk,
    this.stable,
    this.slow,
    this.critical,
    this.deadPositions = const [],
    this.chipTempC,
    this.pcbTempC,
    this.tempC,
    this.acs,
    this.otherChars = const {},
    this.chips,
  });

  bool get hasGrades => stable != null;

  factory InspectBoard.fromJson(Map<String, dynamic> json) => InspectBoard(
        index: ((json['index'] as num?) ?? 0).toInt(),
        chipsTotal: ((json['chips_total'] as num?) ?? 0).toInt(),
        chipsOk: (json['chips_ok'] as num?)?.toInt(),
        stable: (json['stable'] as num?)?.toInt(),
        slow: (json['slow'] as num?)?.toInt(),
        critical: (json['critical'] as num?)?.toInt(),
        deadPositions: ((json['dead_positions'] as List<dynamic>?) ?? const [])
            .map((e) => (e as num).toInt())
            .toList(),
        chipTempC: (json['chip_temp_c'] as num?)?.toDouble(),
        pcbTempC: (json['pcb_temp_c'] as num?)?.toDouble(),
        tempC: (json['temp_c'] as num?)?.toDouble(),
        acs: json['acs'] as String?,
        otherChars: ((json['other_chars'] as Map<String, dynamic>?) ??
                const {})
            .map((k, v) => MapEntry(k, (v as num).toInt())),
        chips: (json['chips'] as List<dynamic>?)
            ?.whereType<Map<String, dynamic>>()
            .map(InspectChip.fromJson)
            .toList(),
      );
}

class InspectBoards {
  final bool supported;
  final String? reason;
  final List<InspectBoard> boards;
  const InspectBoards({
    required this.supported,
    this.reason,
    this.boards = const [],
  });

  factory InspectBoards.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const InspectBoards(supported: false, reason: 'no data');
    }
    return InspectBoards(
      supported: json['supported'] == true,
      reason: json['reason'] as String?,
      boards: ((json['boards'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(InspectBoard.fromJson)
          .toList(),
    );
  }
}

class InspectPool {
  final int? id;
  final String? url;
  final String? user;
  final String? status;
  final int? accepted;
  final int? rejected;
  final int? stale;
  final int? ping;
  const InspectPool({
    this.id,
    this.url,
    this.user,
    this.status,
    this.accepted,
    this.rejected,
    this.stale,
    this.ping,
  });

  factory InspectPool.fromJson(Map<String, dynamic> json) => InspectPool(
        id: (json['id'] as num?)?.toInt(),
        url: json['url'] as String?,
        user: json['user'] as String?,
        status: json['status'] as String?,
        accepted: (json['accepted'] as num?)?.toInt(),
        rejected: (json['rejected'] as num?)?.toInt(),
        stale: (json['stale'] as num?)?.toInt(),
        ping: (json['ping'] as num?)?.toInt(),
      );
}

class InspectPools {
  final bool supported;
  final String? reason;
  final List<InspectPool> pools;
  const InspectPools({
    required this.supported,
    this.reason,
    this.pools = const [],
  });

  factory InspectPools.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const InspectPools(supported: false, reason: 'no data');
    }
    return InspectPools(
      supported: json['supported'] == true,
      reason: json['reason'] as String?,
      pools: ((json['pools'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(InspectPool.fromJson)
          .toList(),
    );
  }
}

class InspectFan {
  final int id;
  final int? rpm;
  final String? status; // vnish: ok | lost
  final int? maxRpm;
  const InspectFan({required this.id, this.rpm, this.status, this.maxRpm});

  factory InspectFan.fromJson(Map<String, dynamic> json) => InspectFan(
        id: ((json['id'] as num?) ?? 0).toInt(),
        rpm: (json['rpm'] as num?)?.toInt(),
        status: json['status'] as String?,
        maxRpm: (json['max_rpm'] as num?)?.toInt(),
      );
}

class InspectFans {
  final bool supported;
  final String? reason;

  /// Fan mode (vnish cooling settings: auto | manual |
  /// immersion). Null when the firmware reports speeds only —
  /// cgminer/stock have no mode source (mapping §5.2).
  final String? mode;
  final int? modeParam;
  final int? dutyPct; // vnish fan_duty
  final List<InspectFan> fans;
  const InspectFans({
    required this.supported,
    this.reason,
    this.mode,
    this.modeParam,
    this.dutyPct,
    this.fans = const [],
  });

  factory InspectFans.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const InspectFans(supported: false, reason: 'no data');
    }
    return InspectFans(
      supported: json['supported'] == true,
      reason: json['reason'] as String?,
      mode: json['mode'] as String?,
      modeParam: (json['mode_param'] as num?)?.toInt(),
      dutyPct: (json['duty_pct'] as num?)?.toInt(),
      fans: ((json['fans'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(InspectFan.fromJson)
          .toList(),
    );
  }
}

/// One `inspect --json` document. An unclaimed device carries
/// [error] (and a null [source]) instead of sections.
class InspectResult {
  final String ip;
  final String? source;
  final String? model;
  final String? credLabel;
  final String? error;
  final InspectBoards boards;
  final InspectPools pools;
  final InspectFans fans;

  const InspectResult({
    required this.ip,
    this.source,
    this.model,
    this.credLabel,
    this.error,
    required this.boards,
    required this.pools,
    required this.fans,
  });

  bool get claimed => source != null;

  /// A bridge-level failure (sidecar died, bad JSON) rendered in
  /// the same shape as a core error document, so the tabs show
  /// the message instead of spinning forever.
  factory InspectResult.failure(String ip, String message) => InspectResult(
        ip: ip,
        error: message,
        boards: InspectBoards(supported: false, reason: message),
        pools: InspectPools(supported: false, reason: message),
        fans: InspectFans(supported: false, reason: message),
      );

  factory InspectResult.fromJson(Map<String, dynamic> json) => InspectResult(
        ip: (json['ip'] ?? '') as String,
        source: json['source'] as String?,
        model: json['model'] as String?,
        credLabel: json['cred_label'] as String?,
        error: json['error'] as String?,
        boards:
            InspectBoards.fromJson(json['boards'] as Map<String, dynamic>?),
        pools: InspectPools.fromJson(json['pools'] as Map<String, dynamic>?),
        fans: InspectFans.fromJson(json['fans'] as Map<String, dynamic>?),
      );
}

// --------------------------------------------------------------------
// History — local per-device chart samples
// --------------------------------------------------------------------

/// Storage key for history and notes: the record's MAC when it
/// carries one ("when present" — no adapter emits one today, so
/// IP is the working key; the rule is written once, here).
String deviceKeyFor(MinerRecord rec) =>
    (rec.mac != null && rec.mac!.isNotEmpty) ? rec.mac! : rec.ip;

/// Samples kept per device; older ones drop off the front.
const int historyCapPerDevice = 300;

class HistorySample {
  final DateTime ts;
  final double? rateValue;
  final String? rateUnit;
  final double? maxTempC;
  final double? powerW;
  const HistorySample({
    required this.ts,
    this.rateValue,
    this.rateUnit,
    this.maxTempC,
    this.powerW,
  });

  Map<String, dynamic> toJson() => {
        'ts': ts.toIso8601String(),
        'rate_value': rateValue,
        'rate_unit': rateUnit,
        'max_temp_c': maxTempC,
        'power_w': powerW,
      };

  factory HistorySample.fromJson(Map<String, dynamic> json) => HistorySample(
        ts: DateTime.tryParse((json['ts'] ?? '') as String) ??
            DateTime.fromMillisecondsSinceEpoch(0),
        rateValue: (json['rate_value'] as num?)?.toDouble(),
        rateUnit: json['rate_unit'] as String?,
        maxTempC: (json['max_temp_c'] as num?)?.toDouble(),
        powerW: (json['power_w'] as num?)?.toDouble(),
      );
}

/// Append one sample for [rec] at [ts] (pure apart from the map
/// mutation — the chart rules live here so tests can pin them):
/// the rate rides the record's OWN native unit via [MinerRecord.rate]
/// (legacy `ths` reads as TH/s, exactly like the core's
/// record_rate), and the per-device list prunes to the cap.
void appendHistorySample(
  Map<String, List<HistorySample>> history,
  MinerRecord rec,
  DateTime ts,
) {
  final rate = rec.rate;
  final list = history.putIfAbsent(deviceKeyFor(rec), () => []);
  list.add(HistorySample(
    ts: ts,
    rateValue: rate?.$1,
    rateUnit: rate?.$2,
    maxTempC: rec.maxTempC,
    powerW: rec.powerW,
  ));
  if (list.length > historyCapPerDevice) {
    list.removeRange(0, list.length - historyCapPerDevice);
  }
}

/// Demo history for the MOCK shell only: a handful of samples
/// for the sample fleet so every chart tab renders in tests and
/// demos (the mock's scans would otherwise need six runs to
/// draw a line). Times are relative to [now] so the chart's
/// time axis always looks alive.
Map<String, List<HistorySample>> demoHistory(DateTime now) {
  List<HistorySample> series(
    List<double> rates,
    String unit,
    List<double> temps,
    List<double?> powers,
  ) =>
      [
        for (var i = 0; i < rates.length; i++)
          HistorySample(
            ts: now.subtract(Duration(minutes: 25 - 5 * i)),
            rateValue: rates[i],
            rateUnit: unit,
            maxTempC: temps[i],
            powerW: powers[i],
          ),
      ];
  return {
    '192.168.2.101': series(
      [109.2, 110.1, 109.6, 110.8, 110.3, 110.5],
      'TH/s',
      [63, 64, 64, 65, 64, 65],
      [3180.0, 3205.0, 3195.0, 3220.0, 3200.0, 3210.0],
    ),
    '192.168.2.102': series(
      [13.9, 14.3, 14.1, 14.6, 14.4, 14.54],
      'MH/s',
      [57, 58, 57, 59, 58, 59],
      [null, null, null, null, null, null],
    ),
    '192.168.2.103': series(
      [1088.0, 1095.0, 1102.0, 1098.0, 1104.0, 1101.0],
      'ksol/s',
      [84, 86, 87, 85, 88, 88],
      [null, null, null, null, null, null],
    ),
  };
}

// --------------------------------------------------------------------
// Chart data prep (pure) + the hand-drawn chart widget
// --------------------------------------------------------------------

class ChartPoint {
  final DateTime ts;
  final double value;
  const ChartPoint(this.ts, this.value);
}

/// One metric's line: samples lacking the metric are SKIPPED
/// (a gap in the data is not a zero). Per-device only — the
/// caller passes one device's samples; units never mix because
/// a device's samples all carry that device's native unit.
List<ChartPoint> ratePoints(List<HistorySample> samples) => [
      for (final s in samples)
        if (s.rateValue != null) ChartPoint(s.ts, s.rateValue!),
    ];

List<ChartPoint> tempPoints(List<HistorySample> samples) => [
      for (final s in samples)
        if (s.maxTempC != null) ChartPoint(s.ts, s.maxTempC!),
    ];

List<ChartPoint> powerPoints(List<HistorySample> samples) => [
      for (final s in samples)
        if (s.powerW != null) ChartPoint(s.ts, s.powerW!),
    ];

/// The unit a device's rate chart is labelled with: the most
/// recent sample that carries one (a device's unit is stable;
/// if it ever changed, the label follows the latest sample and
/// the older points are that device's own history, still never
/// another device's).
String? rateUnitOf(List<HistorySample> samples) {
  for (final s in samples.reversed) {
    if (s.rateUnit != null) return s.rateUnit;
  }
  return null;
}

/// A small line chart, hand-drawn (the app's zero-dependency
/// rule — HashCore uses fl_chart; the behaviour, one labelled
/// series with min/max context, is what ports). A single point
/// draws as a lone dot: one sample is a fact, not a trend.
class MiniChart extends StatelessWidget {
  final String title;
  final String unit;
  final List<ChartPoint> points;
  final Color color;
  const MiniChart({
    super.key,
    required this.title,
    required this.unit,
    required this.points,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final latest = points.isEmpty ? null : points.last.value;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: BeeSkyColors.muted,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            if (latest != null)
              Text(
                unit.isEmpty
                    ? latest.toStringAsFixed(1)
                    : '${latest.toStringAsFixed(1)} $unit',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
          ],
        ),
        const SizedBox(height: 4),
        SizedBox(
          height: 84,
          width: double.infinity,
          child: CustomPaint(painter: _ChartPainter(points, color)),
        ),
      ],
    );
  }
}

class _ChartPainter extends CustomPainter {
  final List<ChartPoint> points;
  final Color color;
  _ChartPainter(this.points, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty || size.width <= 0 || size.height <= 0) return;
    var minV = points.first.value;
    var maxV = points.first.value;
    for (final p in points) {
      minV = math.min(minV, p.value);
      maxV = math.max(maxV, p.value);
    }
    // A flat series still gets a visible band (pad the range),
    // and a varying one gets headroom so the line never clips.
    var span = maxV - minV;
    if (span <= 0) span = math.max(1, maxV.abs() * 0.05);
    final lo = minV - span * 0.15;
    final hi = maxV + span * 0.15;

    final t0 = points.first.ts.millisecondsSinceEpoch;
    final t1 = points.last.ts.millisecondsSinceEpoch;
    final tSpan = t1 - t0;
    double xOf(int i) {
      if (points.length == 1) return size.width / 2;
      if (tSpan <= 0) return size.width * i / (points.length - 1);
      final t = points[i].ts.millisecondsSinceEpoch;
      return size.width * (t - t0) / tSpan;
    }

    double yOf(double v) =>
        size.height - (v - lo) / (hi - lo) * size.height;

    // Faint horizontal guides at min / mid / max of the DATA
    // (not the padded scale), so the eye has honest anchors.
    final gridPaint = Paint()
      ..color = BeeSkyColors.border.withValues(alpha: 0.6)
      ..strokeWidth = 1;
    for (final v in {minV, (minV + maxV) / 2, maxV}) {
      final y = yOf(v);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    if (points.length == 1) {
      canvas.drawCircle(
        Offset(xOf(0), yOf(points.first.value)),
        3.5,
        Paint()..color = color,
      );
      return;
    }
    final path = Path();
    for (var i = 0; i < points.length; i++) {
      final o = Offset(xOf(i), yOf(points[i].value));
      if (i == 0) {
        path.moveTo(o.dx, o.dy);
      } else {
        path.lineTo(o.dx, o.dy);
      }
    }
    canvas.drawPath(
      path,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.8
        ..strokeJoin = StrokeJoin.round,
    );
    final last = Offset(xOf(points.length - 1), yOf(points.last.value));
    canvas.drawCircle(last, 3, Paint()..color = color);
  }

  @override
  bool shouldRepaint(_ChartPainter old) =>
      old.points != points || old.color != color;
}

// --------------------------------------------------------------------
// Stores — beesky-history.json / beesky-notes.json beside the exe
// (the CredStore strategy: bundle dir first, %APPDATA%\BeeSky
// fallback; a corrupt file reads as empty, never bricks the app)
// --------------------------------------------------------------------

abstract class _JsonStore {
  final Directory primaryDir;
  final Directory fallbackDir;
  const _JsonStore({required this.primaryDir, required this.fallbackDir});

  String get fileName;

  File get primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  /// The decoded document, or null when no readable copy exists.
  Map<String, dynamic>? loadDoc() {
    for (final file in [primaryFile, fallbackFile]) {
      try {
        if (!file.existsSync()) continue;
        final decoded = jsonDecode(file.readAsStringSync());
        if (decoded is Map<String, dynamic>) return decoded;
      } on FileSystemException {
        continue;
      } on FormatException {
        continue;
      }
    }
    return null;
  }

  /// Writes the document; returns the file actually written.
  Future<File> saveDoc(Map<String, dynamic> doc) async {
    final text = const JsonEncoder.withIndent('  ').convert(doc);
    try {
      primaryDir.createSync(recursive: true);
      primaryFile.writeAsStringSync(text);
      return primaryFile;
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      fallbackFile.writeAsStringSync(text);
      return fallbackFile;
    }
  }
}

(Directory, Directory) _storeDirs() {
  final exeDir = File(Platform.resolvedExecutable).parent;
  final appData = Platform.environment['APPDATA'];
  final fallback = (appData != null && appData.isNotEmpty)
      ? Directory('$appData${Platform.pathSeparator}BeeSky')
      : Directory(
          '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
  return (exeDir, fallback);
}

class HistoryStore extends _JsonStore {
  const HistoryStore({required super.primaryDir, required super.fallbackDir});

  factory HistoryStore.appDefault() {
    final (primary, fallback) = _storeDirs();
    return HistoryStore(primaryDir: primary, fallbackDir: fallback);
  }

  @override
  String get fileName => 'beesky-history.json';

  Future<Map<String, List<HistorySample>>> load() async {
    final doc = loadDoc();
    final devices = doc?['devices'];
    if (devices is! Map<String, dynamic>) return {};
    return devices.map((key, raw) => MapEntry(
          key,
          ((raw as List<dynamic>?) ?? const [])
              .whereType<Map<String, dynamic>>()
              .map(HistorySample.fromJson)
              .toList(),
        ));
  }

  Future<File> save(Map<String, List<HistorySample>> history) => saveDoc({
        'version': 1,
        'devices': history.map(
          (key, samples) => MapEntry(
            key,
            samples.map((s) => s.toJson()).toList(),
          ),
        ),
      });
}

class NoteStore extends _JsonStore {
  const NoteStore({required super.primaryDir, required super.fallbackDir});

  factory NoteStore.appDefault() {
    final (primary, fallback) = _storeDirs();
    return NoteStore(primaryDir: primary, fallbackDir: fallback);
  }

  @override
  String get fileName => 'beesky-notes.json';

  Future<Map<String, String>> load() async {
    final doc = loadDoc();
    final notes = doc?['notes'];
    if (notes is! Map<String, dynamic>) return {};
    return notes.map((key, value) => MapEntry(key, '$value'));
  }

  Future<File> save(Map<String, String> notes) =>
      saveDoc({'version': 1, 'notes': notes});
}
