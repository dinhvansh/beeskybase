/// Data models for the BeeSky JSON bridge.
///
/// The wire format is NOT invented here: it is the record dict the Python
/// core already serialises for the agent/cloud path (beesky/core/report.py
/// `build_record`), carried over the `scan --json` envelope:
/// {"records": [...], "scanned": N, "found": M, "elapsed_s": X}.
/// Records carry their NATIVE hashrate unit since v0.20
/// (rate_value + rate_unit: TH/s, GH/s, MH/s, ksol/s or sol/s).
library;

/// Canonical unit order — mirrors beesky.core.report.RATE_UNIT_ORDER.
const List<String> rateUnitOrder = ['TH/s', 'GH/s', 'MH/s', 'ksol/s', 'sol/s'];

/// A hashboard at or above this temperature is flagged hot — mirrors
/// beesky.core.report.TEMP_LIMIT_C, the same threshold that already
/// makes the core emit a per-chain OVER_TEMP problem.
const double tempLimitC = 85;

/// "1101.0, ksol/s" -> "1,101.00 ksol/s" — mirrors Python's f"{v:,.2f}".
String formatRateNum(double value) {
  final fixed = value.toStringAsFixed(2);
  final dot = fixed.indexOf('.');
  var intPart = dot < 0 ? fixed : fixed.substring(0, dot);
  final frac = dot < 0 ? '00' : fixed.substring(dot + 1);
  var sign = '';
  if (intPart.startsWith('-')) {
    sign = '-';
    intPart = intPart.substring(1);
  }
  final buf = StringBuffer(sign);
  for (var i = 0; i < intPart.length; i++) {
    if (i > 0 && (intPart.length - i) % 3 == 0) buf.write(',');
    buf.write(intPart[i]);
  }
  return '$buf.$frac';
}

String formatRate(double value, String unit) => '${formatRateNum(value)} $unit';

class Problem {
  final String code;
  final String severity;
  final String detail;
  const Problem({
    required this.code,
    required this.severity,
    required this.detail,
  });

  factory Problem.fromJson(Map<String, dynamic> json) => Problem(
        code: (json['code'] ?? '') as String,
        severity: (json['severity'] ?? '') as String,
        detail: (json['detail'] ?? '') as String,
      );
}

class ChainInfo {
  final int index;
  final double? tempC;
  final int chipsAlive;
  final int chipsTotal;
  const ChainInfo({
    required this.index,
    required this.tempC,
    required this.chipsAlive,
    required this.chipsTotal,
  });

  factory ChainInfo.fromJson(Map<String, dynamic> json) => ChainInfo(
        index: (json['index'] as num).toInt(),
        tempC: (json['temp_c'] as num?)?.toDouble(),
        chipsAlive: (json['chips_alive'] as num).toInt(),
        chipsTotal: (json['chips_total'] as num).toInt(),
      );

  /// At/over the core's TEMP_LIMIT_C — the board renders red wherever
  /// per-board temps are shown (table NHIỆT cell, detail board lines).
  bool get isHot => tempC != null && tempC! >= tempLimitC;
}

class MinerRecord {
  final String ip;
  final String model;
  final String source;
  final List<ChainInfo> chains;
  final List<int> fansRpm;
  final int chipsAlive;
  final int chipsTotal;
  final double? maxTempC;

  /// The wire key is `problems` (renamed from `issues` in the v0.20
  /// Python core); mapped here once so the UI just says `issues`.
  final List<Problem> issues;
  final String status; // "OK" | "CHECK"
  final double? rateValue;
  final String? rateUnit;
  final double? legacyThs;

  const MinerRecord({
    required this.ip,
    required this.model,
    required this.source,
    required this.chains,
    required this.fansRpm,
    required this.chipsAlive,
    required this.chipsTotal,
    required this.maxTempC,
    required this.issues,
    required this.status,
    required this.rateValue,
    required this.rateUnit,
    required this.legacyThs,
  });

  factory MinerRecord.fromJson(Map<String, dynamic> json) {
    return MinerRecord(
      ip: (json['ip'] ?? '') as String,
      model: (json['model'] ?? '—') as String,
      source: (json['source'] ?? '') as String,
      chains: ((json['chains'] as List<dynamic>?) ?? const [])
          .map((e) => ChainInfo.fromJson(e as Map<String, dynamic>))
          .toList(),
      fansRpm: ((json['fans_rpm'] as List<dynamic>?) ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
      chipsAlive: ((json['chips_alive'] as num?) ?? 0).toInt(),
      chipsTotal: ((json['chips_total'] as num?) ?? 0).toInt(),
      maxTempC: (json['max_temp_c'] as num?)?.toDouble(),
      issues: ((json['problems'] as List<dynamic>?) ?? const [])
          .map((e) => Problem.fromJson(e as Map<String, dynamic>))
          .toList(),
      status: (json['status'] ?? 'CHECK') as String,
      rateValue: (json['rate_value'] as num?)?.toDouble(),
      rateUnit: json['rate_unit'] as String?,
      legacyThs: (json['ths'] as num?)?.toDouble(),
    );
  }

  bool get hasFetchError => issues.any((p) => p.code == 'FETCH_ERROR');
  bool get isOk => status == 'OK';

  /// Table status chip — same rule as the Tk table: an unreachable miner
  /// (FETCH_ERROR) shows ERROR, a clean one OK, anything else CHECK.
  String get statusLabel => hasFetchError ? 'ERROR' : (isOk ? 'OK' : 'CHECK');

  /// (value, unit) with the legacy fallback — mirrors report.record_rate:
  /// native rate first, then the pre-0.21 `ths` field read as TH/s.
  (double, String)? get rate {
    if (rateValue != null) return (rateValue!, rateUnit ?? 'TH/s');
    if (legacyThs != null) return (legacyThs!, 'TH/s');
    return null;
  }

  String get rateText {
    final r = rate;
    return r == null ? '—' : formatRate(r.$1, r.$2);
  }

  String get chipsText => '$chipsAlive/$chipsTotal';

  String get tempText =>
      maxTempC == null ? '—' : '${maxTempC!.toStringAsFixed(0)} °C';

  /// Per-board temperatures in chain order — only the chains that
  /// actually reported one. Empty when the record carries no per-chain
  /// temps at all; the table then falls back to [tempText] (the single
  /// max temp), exactly as before this rule existed.
  List<double> get boardTemps => [
        for (final c in chains)
          if (c.tempC != null) c.tempC!,
      ];

  String get fansText {
    final live = fansRpm.where((f) => f > 0).toList();
    return live.isEmpty ? '—' : live.join(' / ');
  }

  /// Display label for the wire source token (mirrors gui.SOURCE_LABEL).
  String get sourceLabel => switch (source) {
        'cgminer' => 'cgminer RPC',
        'vnish' => 'VNish',
        'stock' => 'Bitmain gốc',
        _ => source,
      };
}

/// Grouped fleet total — a direct port of report.fleet_rate_totals +
/// format_rate_totals: sums per native unit in canonical order, joined
/// with " · ". Records with no resolvable rate are skipped; an empty
/// fleet formats as "0.00 TH/s" exactly like the Python side.
String fleetRateTotalsText(List<MinerRecord> records) {
  final totals = <String, double>{};
  for (final rec in records) {
    final r = rec.rate;
    if (r != null) totals[r.$2] = (totals[r.$2] ?? 0) + r.$1;
  }
  final parts = <String>[
    for (final unit in rateUnitOrder)
      if (totals.containsKey(unit)) formatRate(totals[unit]!, unit),
    // Units outside the canonical order (should not happen) keep Python's
    // insertion-order behaviour as a tail.
    for (final e in totals.entries)
      if (!rateUnitOrder.contains(e.key)) formatRate(e.value, e.key),
  ];
  return parts.isEmpty ? formatRate(0, 'TH/s') : parts.join(' · ');
}

double? fleetMaxTempC(List<MinerRecord> records) {
  double? best;
  for (final rec in records) {
    final t = rec.maxTempC;
    if (t != null && (best == null || t > best)) best = t;
  }
  return best;
}

int fleetProblemCount(List<MinerRecord> records) =>
    records.where((r) => !r.isOk).length;

/// Count of records whose table chip reads [label]
/// ("OK" | "CHECK" | "ERROR") — drives the header stat chips.
int fleetStatusCount(List<MinerRecord> records, String label) =>
    records.where((r) => r.statusLabel == label).length;

class ScanResult {
  final List<MinerRecord> records;
  final int scanned;
  final int found;
  final double elapsedS;
  const ScanResult({
    required this.records,
    required this.scanned,
    required this.found,
    required this.elapsedS,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) => ScanResult(
        records: ((json['records'] as List<dynamic>?) ?? const [])
            .map((e) => MinerRecord.fromJson(e as Map<String, dynamic>))
            .toList(),
        scanned: ((json['scanned'] as num?) ?? 0).toInt(),
        found: ((json['found'] as num?) ?? 0).toInt(),
        elapsedS: ((json['elapsed_s'] as num?) ?? 0).toDouble(),
      );
}

class SysInfo {
  final String version;
  final String defaultTarget;
  const SysInfo({required this.version, required this.defaultTarget});

  factory SysInfo.fromJson(Map<String, dynamic> json) => SysInfo(
        version: (json['version'] ?? '') as String,
        defaultTarget: (json['default_target'] ?? '') as String,
      );
}
