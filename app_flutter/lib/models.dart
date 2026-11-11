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

/// One pool slot as a future core may emit it (wire key `pools`).
/// Today's records carry NO pool data (see docs/grid-mapping.md
/// §3.2) — the parse is defensive so the grid's pool columns light
/// up unchanged when the core grows the field.
class PoolInfo {
  final String url;
  final String worker;
  const PoolInfo({required this.url, required this.worker});

  factory PoolInfo.fromJson(Map<String, dynamic> json) => PoolInfo(
        url: (json['url'] ?? '') as String,
        worker: (json['worker'] ?? json['user'] ?? '') as String,
      );
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

  /// Label of the saved credential set that authenticated to this
  /// miner (v0.23, wire key `cred_label`). Null for cgminer-RPC
  /// miners (no auth), anonymous/default-cred reads and error
  /// records — the detail panel only shows a login that was proven.
  final String? credLabel;

  /// Seconds since boot (wire `elapsed_s`, on the wire since the
  /// core's first record schema, parsed by the app only in v0.25).
  final int elapsedS;

  /// cgminer "GHS 5s" (wire `ghs_5s`) — GH/s-family terms ONLY;
  /// see [rateRtText] for how the realtime column uses it honestly.
  final double? ghs5s;

  /// Wall power in watts (wire `power_w`) when the source reports
  /// one (VNish dashd, some cgminer stats); null on classic
  /// Bitmain bmminer, whose firmware reports no power at all.
  final double? powerW;

  /// MAC address — a DATA-GAP today (nothing in the core emits
  /// one); parsed so the column/search light up if it ever lands.
  final String? mac;

  /// Pool slots (wire `pools`) — a DATA-GAP today: scan records
  /// carry no pool data. Empty until the core grows the field.
  final List<PoolInfo> pools;

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
    this.credLabel,
    this.elapsedS = 0,
    this.ghs5s,
    this.powerW,
    this.mac,
    this.pools = const [],
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
      credLabel: json['cred_label'] as String?,
      elapsedS: ((json['elapsed_s'] as num?) ?? 0).toInt(),
      ghs5s: (json['ghs_5s'] as num?)?.toDouble(),
      powerW: (json['power_w'] as num?)?.toDouble(),
      mac: json['mac'] as String?,
      pools: ((json['pools'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(PoolInfo.fromJson)
          .toList(),
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

  // ------------------------------------------------------------------
  // Grid accessors (v0.25) — everything the data-grid columns, sort,
  // search and filters read. Derived values are arithmetic on real
  // record fields; gaps stay null and render "—" (docs/grid-mapping.md).
  // ------------------------------------------------------------------

  /// "3d 4h 12m" / "4h 12m" / "12m" — compact uptime from [elapsedS].
  String get uptimeText {
    if (elapsedS <= 0) return '—';
    final d = elapsedS ~/ 86400;
    final h = (elapsedS % 86400) ~/ 3600;
    final m = (elapsedS % 3600) ~/ 60;
    if (d > 0) return '${d}d ${h}h';
    if (h > 0) return '${h}h ${m}m';
    return '${m}m';
  }

  String get powerText =>
      powerW == null ? '—' : '${powerW!.toStringAsFixed(0)} W';

  /// Efficiency in J/TH — DERIVED (power_w / ths) for TH/s records
  /// that report power; null everywhere else (a J/TH figure for a
  /// Scrypt/Equihash unit would be a fabrication).
  double? get efficiencyJTh {
    final w = powerW;
    final ths = legacyThs;
    if (w == null || ths == null || ths <= 0) return null;
    return w / ths;
  }

  String get efficiencyText {
    final e = efficiencyJTh;
    return e == null ? '—' : '${e.toStringAsFixed(1)} J/TH';
  }

  /// Realtime rate for the HASHRATE RT column — PARTIAL by data:
  /// the wire's `ghs_5s` is GH/s-family only, so it is shown (as
  /// TH/s) solely for TH/s-family records; other units have no
  /// separate realtime value on the wire and honestly read null.
  (double, String)? get rateRt {
    final g = ghs5s;
    if (g == null) return null;
    final unit = rate?.$2 ?? 'TH/s';
    if (unit != 'TH/s') return null;
    return (g / 1000.0, 'TH/s');
  }

  String get rateRtText {
    final r = rateRt;
    return r == null ? '—' : formatRate(r.$1, r.$2);
  }

  /// Algorithm — DERIVED from the native rate unit using the same
  /// family conventions as the core's `_native_rate` calibration.
  String get algorithmLabel => switch (rateUnit) {
        'ksol/s' || 'sol/s' => 'Equihash',
        'MH/s' => 'Scrypt',
        'TH/s' || 'GH/s' => 'SHA-256',
        _ => '—',
      };

  /// Boards with at least one missing chip — DERIVED badChainsCount.
  int get badBoards => chains.where((c) => c.chipsTotal > c.chipsAlive).length;

  /// Problem codes joined for the MÃ LỖI column / filters / search.
  String get errorCodesText => issues.map((p) => p.code).toSet().join(', ');

  /// Chain [i]'s temperature, or null when the board is absent or
  /// reported none (a Board-4 filter never matches a 3-board unit).
  double? boardTempAt(int i) =>
      (i >= 0 && i < chains.length) ? chains[i].tempC : null;

  String boardTempTextAt(int i) {
    final t = boardTempAt(i);
    return t == null ? '—' : '${t.toStringAsFixed(0)}°';
  }

  /// Pool slot [i]'s URL / worker — empty strings while the record
  /// carries no pool data (the v0.25 DATA-GAP).
  String poolUrlAt(int i) => (i < pools.length) ? pools[i].url : '';
  String poolWorkerAt(int i) => (i < pools.length) ? pools[i].worker : '';

  /// Sort/comparison key for rates: (family rank, value in the
  /// family's smallest unit). Rates are NEVER compared across units
  /// (the v0.20 lesson) — families order by the canonical unit
  /// order, values compare inside the family.
  (int, double)? get rateSortKey {
    final r = rate;
    if (r == null) return null;
    final rank = rateUnitOrder.indexOf(r.$2);
    final base = switch (r.$2) {
      'TH/s' => r.$1 * 1e12,
      'GH/s' => r.$1 * 1e9,
      'MH/s' => r.$1 * 1e6,
      'ksol/s' => r.$1 * 1e3,
      _ => r.$1, // sol/s and anything unknown: already the base
    };
    return (rank < 0 ? rateUnitOrder.length : rank, base);
  }

  /// Everything the grid search matches against (HashCore: "Search
  /// by IP / MAC, Pool or Worker"; BeeSky adds model + worker from
  /// every slot). MAC/pool parts are empty while they are gaps.
  String get searchHaystack => [
        ip,
        mac ?? '',
        model,
        for (final p in pools) ...[p.url, p.worker],
      ].join(' ').toLowerCase();
}

/// Numeric IP comparison (octet by octet) — lexicographic ordering
/// would put 192.168.2.99 after 192.168.2.101. Non-IP strings fall
/// back to plain string order, after parseable IPs.
int compareIp(String a, String b) {
  List<int>? parse(String s) {
    final parts = s.split('.');
    if (parts.length != 4) return null;
    final out = <int>[];
    for (final p in parts) {
      final v = int.tryParse(p);
      if (v == null) return null;
      out.add(v);
    }
    return out;
  }

  final pa = parse(a);
  final pb = parse(b);
  if (pa == null && pb == null) return a.compareTo(b);
  if (pa == null) return 1;
  if (pb == null) return -1;
  for (var i = 0; i < 4; i++) {
    final c = pa[i].compareTo(pb[i]);
    if (c != 0) return c;
  }
  return 0;
}

/// "1,234" style integer grouping for counts in grid chrome.
String formatCount(int value) {
  final s = '$value';
  final buf = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
    buf.write(s[i]);
  }
  return buf.toString();
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
