/// The five views v0.32 lands (docs/views-mapping.md): Bản đồ
/// nhiệt, Điện năng, Lịch sử sửa, Sự kiện, Cài đặt. Each ports an
/// EXISTING BeeSky implementation — the `beesky serve` web
/// dashboard's heat map, the cloud energy report's shapes over
/// local data, the ticket files, the core EventEngine's log, and
/// the settings that actually persist — instead of inventing new
/// semantics. Pure helpers live at the top so tests pin them
/// without a widget tree.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import 'detail.dart';
import 'models.dart';
import 'theme.dart';

// --------------------------------------------------------------------
// Shared helpers
// --------------------------------------------------------------------

/// The web heat map's band colours (beesky/web/dashboard.html
/// `heatColor`), hex for hex: <60 green, 60–70 olive, 70–80 amber,
/// 80–90 burnt orange, ≥90 dark red, no reading grey.
Color heatBandColor(double? tempC) {
  if (tempC == null) return const Color(0xFF2C2C2C);
  if (tempC < 60) return const Color(0xFF14532D);
  if (tempC < 70) return const Color(0xFF4A5D23);
  if (tempC < 80) return const Color(0xFF7A5A12);
  if (tempC < 90) return const Color(0xFF8A4512);
  return const Color(0xFF8A1F1A);
}

/// The tooltip status word the web heat map uses.
String heatStatusWord(MinerRecord rec) {
  if (rec.hasFetchError) return 'Mất kết nối';
  return rec.isOk ? 'OK' : 'Cần kiểm tra';
}

/// Fleet power right now, honestly counted: only miners whose
/// source reports a wattage contribute (classic bmminer reports
/// none — the coverage count says so instead of hiding it).
class FleetPower {
  final double totalW;
  final int reporting;
  final int total;
  const FleetPower(this.totalW, this.reporting, this.total);

  double get kw => totalW / 1000.0;
  double get kwhPerDay => kw * 24;
}

FleetPower fleetPower(List<MinerRecord> records) {
  var w = 0.0;
  var n = 0;
  for (final rec in records) {
    final p = rec.powerW;
    if (p != null) {
      w += p;
      n++;
    }
  }
  return FleetPower(w, n, records.length);
}

/// Energy integrated from saved scan samples (the Điện năng
/// view's history section): per interval, energy = the EARLIER
/// sample's power × Δt. Intervals longer than [maxGap] are
/// skipped (the state in between is unknown), samples outside
/// the [days]-day window ending at [now] are ignored, and each
/// interval is attributed to its start sample's local day — the
/// local analogue of the cloud's energy_hours integration.
class EnergyIntegration {
  final double totalKwh;
  final Map<String, double> perDay; // 'yyyy-MM-dd' -> kWh
  final Map<String, double> perDevice; // device key -> kWh
  const EnergyIntegration(this.totalKwh, this.perDay, this.perDevice);

  bool get isEmpty => totalKwh <= 0;
}

String dayKeyOf(DateTime t) =>
    '${t.year.toString().padLeft(4, '0')}-'
    '${t.month.toString().padLeft(2, '0')}-'
    '${t.day.toString().padLeft(2, '0')}';

EnergyIntegration integrateEnergy(
  Map<String, List<HistorySample>> history, {
  required DateTime now,
  int days = 7,
  Duration maxGap = const Duration(minutes: 30),
}) {
  final windowStart = now.subtract(Duration(days: days));
  var total = 0.0;
  final perDay = <String, double>{};
  final perDevice = <String, double>{};
  history.forEach((key, samples) {
    final sorted = [...samples]..sort((a, b) => a.ts.compareTo(b.ts));
    for (var i = 0; i + 1 < sorted.length; i++) {
      final a = sorted[i];
      final b = sorted[i + 1];
      if (a.ts.isBefore(windowStart)) continue;
      final power = a.powerW;
      if (power == null) continue;
      final dt = b.ts.difference(a.ts);
      if (dt <= Duration.zero || dt > maxGap) continue;
      final kwh = power * dt.inSeconds / 3600.0 / 1000.0;
      total += kwh;
      perDay.update(dayKeyOf(a.ts), (v) => v + kwh, ifAbsent: () => kwh);
      perDevice.update(key, (v) => v + kwh, ifAbsent: () => kwh);
    }
  });
  return EnergyIntegration(total, perDay, perDevice);
}

/// Vietnamese money format: '.' thousand separators, no decimals
/// (energy costs are estimates; cents would be theatre).
String formatVnd(num value) {
  final digits = value.round().abs().toString();
  final buf = StringBuffer(value < 0 ? '-' : '');
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) buf.write('.');
    buf.write(digits[i]);
  }
  return '$buf ₫';
}

/// 'dd/MM/yyyy HH:mm' for ticket stamps; unparseable input passes
/// through unchanged (better than hiding a real file).
String formatTicketStamp(String iso) {
  final t = DateTime.tryParse(iso);
  if (t == null) return iso;
  String two(int v) => v.toString().padLeft(2, '0');
  return '${two(t.day)}/${two(t.month)}/${t.year} '
      '${two(t.hour)}:${two(t.minute)}';
}

// --------------------------------------------------------------------
// App settings (beesky-settings.json) — Cài đặt's store
// --------------------------------------------------------------------

/// The settings that persist AND take effect (nothing decorative):
/// the default scan target and the electricity price (v0.32), plus
/// the v0.34 Timeouts/Advanced/scale/IP-Report fields
/// (docs/settings-mapping.md §2). Defaults mirror the rest of
/// BeeSky: no target override (= sysinfo's auto-detected subnet),
/// 2000 VNĐ/kWh (the cloud's electricity_price_vnd default),
/// probe 1.5s / request 3.0s (the core's own defaults), stagger
/// 0 (no pause), 64 scan workers / 4 ops workers (the core's
/// defaults), scale 1.0, IP-Report listening off (opt-in — it
/// opens UDP ports). fromJson tolerates files saved by older
/// versions (every new key defaults when absent).
class AppSettings {
  final String defaultTarget;
  final double priceVndKwh;
  final double probeTimeoutS;
  final double requestTimeoutS;
  final double opsStaggerS;
  final int scanWorkers;
  final int opsWorkers;
  final double scale;
  final bool ipReportEnabled;

  const AppSettings({
    this.defaultTarget = '',
    this.priceVndKwh = 2000,
    this.probeTimeoutS = 1.5,
    this.requestTimeoutS = 3.0,
    this.opsStaggerS = 0.0,
    this.scanWorkers = 64,
    this.opsWorkers = 4,
    this.scale = 1.0,
    this.ipReportEnabled = false,
  });

  static double _num(Map<String, dynamic> json, String key, double dflt) =>
      ((json[key] as num?) ?? dflt).toDouble();

  static int _int(Map<String, dynamic> json, String key, int dflt) =>
      ((json[key] as num?) ?? dflt).toInt();

  factory AppSettings.fromJson(Map<String, dynamic> json) => AppSettings(
        defaultTarget: (json['default_target'] ?? '') as String,
        priceVndKwh: _num(json, 'price_vnd_kwh', 2000),
        probeTimeoutS: _num(json, 'probe_timeout_s', 1.5),
        requestTimeoutS: _num(json, 'request_timeout_s', 3.0),
        opsStaggerS: _num(json, 'ops_stagger_s', 0.0),
        scanWorkers: _int(json, 'scan_workers', 64),
        opsWorkers: _int(json, 'ops_workers', 4),
        scale: _num(json, 'scale', 1.0),
        ipReportEnabled: (json['ip_report_enabled'] as bool?) ?? false,
      );

  Map<String, dynamic> toJson() => {
        'default_target': defaultTarget,
        'price_vnd_kwh': priceVndKwh,
        'probe_timeout_s': probeTimeoutS,
        'request_timeout_s': requestTimeoutS,
        'ops_stagger_s': opsStaggerS,
        'scan_workers': scanWorkers,
        'ops_workers': opsWorkers,
        'scale': scale,
        'ip_report_enabled': ipReportEnabled,
      };

  /// One field changed, everything else kept — the tab editors
  /// and the zoom hotkeys build the next settings this way.
  AppSettings copyWith({
    String? defaultTarget,
    double? priceVndKwh,
    double? probeTimeoutS,
    double? requestTimeoutS,
    double? opsStaggerS,
    int? scanWorkers,
    int? opsWorkers,
    double? scale,
    bool? ipReportEnabled,
  }) =>
      AppSettings(
        defaultTarget: defaultTarget ?? this.defaultTarget,
        priceVndKwh: priceVndKwh ?? this.priceVndKwh,
        probeTimeoutS: probeTimeoutS ?? this.probeTimeoutS,
        requestTimeoutS: requestTimeoutS ?? this.requestTimeoutS,
        opsStaggerS: opsStaggerS ?? this.opsStaggerS,
        scanWorkers: scanWorkers ?? this.scanWorkers,
        opsWorkers: opsWorkers ?? this.opsWorkers,
        scale: scale ?? this.scale,
        ipReportEnabled: ipReportEnabled ?? this.ipReportEnabled,
      );
}

/// One app data file for the Logs tab (v0.34): label + size in
/// bytes (null when the file does not exist yet).
class StoreFileInfo {
  final String label;
  final int? bytes;
  const StoreFileInfo(this.label, this.bytes);

  String get sizeText {
    if (bytes == null) return 'chưa có file';
    if (bytes! < 1024) return '${bytes!} B';
    if (bytes! < 1024 * 1024) return '${(bytes! / 1024).toStringAsFixed(1)} KB';
    return '${(bytes! / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

(Directory, Directory) _viewStoreDirs() {
  final exe = File(Platform.resolvedExecutable);
  final local = Platform.environment['LOCALAPPDATA'];
  final fallback = local != null && local.isNotEmpty
      ? Directory('$local${Platform.pathSeparator}BeeSky')
      : Directory(
          '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
  return (exe.parent, fallback);
}

class SettingsStore {
  final Directory primaryDir;
  final Directory fallbackDir;
  static const fileName = 'beesky-settings.json';
  const SettingsStore({required this.primaryDir, required this.fallbackDir});

  factory SettingsStore.appDefault() {
    final (primary, fallback) = _viewStoreDirs();
    return SettingsStore(primaryDir: primary, fallbackDir: fallback);
  }

  File get _primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get _fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  /// The live settings file, or null before the first save.
  File? get file => _primaryFile.existsSync()
      ? _primaryFile
      : _fallbackFile.existsSync()
          ? _fallbackFile
          : null;

  AppSettings load() {
    for (final f in [_primaryFile, _fallbackFile]) {
      try {
        if (!f.existsSync()) continue;
        final doc = jsonDecode(f.readAsStringSync());
        if (doc is Map<String, dynamic>) return AppSettings.fromJson(doc);
      } on FormatException {
        continue;
      } on FileSystemException {
        continue;
      }
    }
    return const AppSettings();
  }

  void save(AppSettings settings) {
    final text = jsonEncode(settings.toJson());
    try {
      _primaryFile.writeAsStringSync(text);
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      _fallbackFile.writeAsStringSync(text);
    }
  }
}

// --------------------------------------------------------------------
// Event log (beesky-events.json) + per-target engine state files
// --------------------------------------------------------------------

/// The app's PERSISTENT event log: the core engine's state is
/// per-target and lives in state files; the events it emits come
/// back inside each scan's payload and accumulate HERE (newest
/// first, capped) — the local analogue of serve's in-memory ring,
/// except it survives restarts.
class EventLogStore {
  final Directory primaryDir;
  final Directory fallbackDir;
  static const fileName = 'beesky-events.json';
  static const cap = 500;
  const EventLogStore({required this.primaryDir, required this.fallbackDir});

  factory EventLogStore.appDefault() {
    final (primary, fallback) = _viewStoreDirs();
    return EventLogStore(primaryDir: primary, fallbackDir: fallback);
  }

  File get _primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get _fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  List<FleetEvent> load() {
    for (final f in [_primaryFile, _fallbackFile]) {
      try {
        if (!f.existsSync()) continue;
        final doc = jsonDecode(f.readAsStringSync());
        final list = doc is Map<String, dynamic> ? doc['events'] : doc;
        if (list is List) {
          return list
              .whereType<Map<String, dynamic>>()
              .map(FleetEvent.fromJson)
              .toList();
        }
      } on FormatException {
        continue;
      } on FileSystemException {
        continue;
      }
    }
    return [];
  }

  void save(List<FleetEvent> events) {
    final text = jsonEncode({
      'events': events.take(cap).map((e) => e.toJson()).toList(),
    });
    try {
      _primaryFile.writeAsStringSync(text);
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      _fallbackFile.writeAsStringSync(text);
    }
  }

  /// The EventEngine state file for ONE scan target (ad-hoc target
  /// string or a group's targets): one engine per watched target,
  /// exactly like separate `watch --state` invocations — pointing
  /// a second target at the same state would fire false OFFLINEs
  /// for the first target's fleet. FNV-1a keeps the file name
  /// stable and filesystem-safe.
  String stateFilePathFor(String target) {
    var hash = 0x811c9dc5;
    for (final byte in utf8.encode(target)) {
      hash ^= byte;
      hash = (hash * 0x01000193) & 0xffffffff;
    }
    final dir = _primaryFile.parent;
    return '${dir.path}${Platform.pathSeparator}'
        'beesky-events-state-${hash.toRadixString(16).padLeft(8, '0')}.json';
  }
}

// --------------------------------------------------------------------
// Shared view chrome
// --------------------------------------------------------------------

Widget viewHeader(String title, String subtitle) {
  return Container(
    padding: const EdgeInsets.fromLTRB(18, 16, 18, 12),
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: BeeSkyColors.border)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
        const SizedBox(height: 3),
        Text(subtitle,
            style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12)),
      ],
    ),
  );
}

Widget viewEmptyState(IconData icon, String title, String hint) {
  return Padding(
    padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
    child: GlassCard(
      padding: EdgeInsets.zero,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: BeeSkyColors.muted),
            const SizedBox(height: 14),
            Text(title,
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(hint,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: BeeSkyColors.muted)),
            ),
          ],
        ),
      ),
    ),
  );
}

// --------------------------------------------------------------------
// 1. Bản đồ nhiệt — the web dashboard's heat map over current records
// --------------------------------------------------------------------

class HeatMapView extends StatelessWidget {
  final List<MinerRecord> records;
  final bool scanned;
  final void Function(MinerRecord) onSelect;
  const HeatMapView({
    super.key,
    required this.records,
    required this.scanned,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    if (!scanned) {
      return viewEmptyState(Icons.grid_on, 'Chưa quét',
          'Bản đồ nhiệt vẽ theo lần quét gần nhất — bấm Quét ngay '
          'ở màn hình Máy đào trước.');
    }
    if (records.isEmpty) {
      // The web dashboard's own empty text.
      return viewEmptyState(Icons.grid_on, 'Chưa phát hiện máy nào',
          'Chưa phát hiện máy nào — kiểm tra lại mục tiêu quét.');
    }
    final sorted = [...records]..sort((a, b) => compareIp(a.ip, b.ip));
    return GridView.builder(
      padding: const EdgeInsets.all(14),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 168,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: 1.45,
      ),
      itemCount: sorted.length,
      itemBuilder: (context, i) => _tile(sorted[i]),
    );
  }

  Widget _tile(MinerRecord rec) {
    final offline = rec.hasFetchError;
    final problem = !offline && !rec.isOk;
    final band = offline ? const Color(0xFF2C2C2C) : heatBandColor(rec.maxTempC);
    final octet = rec.ip.split('.').last;
    final tooltip = StringBuffer('${rec.ip} · ${rec.model} · '
        '${heatStatusWord(rec)}');
    if (rec.issues.isNotEmpty) {
      tooltip.write(' · ${rec.issues.length} vấn đề');
    }
    return Tooltip(
      message: tooltip.toString(),
      child: InkWell(
        // Named divergence: the web original is display-only;
        // the click selects the miner and jumps to Máy đào.
        onTap: () => onSelect(rec),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: band.withValues(alpha: 0.88),
            border: Border.all(
              color: problem ? BeeSkyColors.bad : Colors.transparent,
              width: problem ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      octet,
                      style: TextStyle(
                        fontSize: 21,
                        fontWeight: FontWeight.w800,
                        color:
                            offline ? BeeSkyColors.muted : BeeSkyColors.text,
                      ),
                    ),
                  ),
                  Flexible(
                    child: Text(
                      offline
                          ? 'Offline'
                          : rec.maxTempC == null
                              ? '—'
                              : '${rec.maxTempC!.toStringAsFixed(0)}°C',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color:
                            offline ? BeeSkyColors.muted : BeeSkyColors.text,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Text(
                '${rec.ip} · ${offline ? '—' : rec.rateText}',
                style: const TextStyle(
                  fontSize: 11,
                  color: Color(0xD9FFFFFF),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------
// 2. Điện năng — the cloud report's shapes over local data
// --------------------------------------------------------------------

class EnergyView extends StatelessWidget {
  final List<MinerRecord> records;
  final Map<String, List<HistorySample>> history;
  final double priceVndKwh;
  const EnergyView({
    super.key,
    required this.records,
    required this.history,
    required this.priceVndKwh,
  });

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final fleet = fleetPower(records);
    final energy = integrateEnergy(history, now: now);
    final hasAny = fleet.reporting > 0 || !energy.isEmpty;
    if (!hasAny) {
      // The cloud panel's honest empty state, adapted.
      return viewEmptyState(Icons.bolt, 'Chưa có dữ liệu điện',
          'Chưa có dữ liệu điện — nguồn máy chưa báo công suất. '
          'Máy chạy VNish (dashd) có báo watts; máy stock cổ điển '
          'thì không.');
    }
    final dayRows = energy.perDay.entries.toList()
      ..sort((a, b) => b.key.compareTo(a.key));
    final deviceRows = energy.perDevice.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
      children: [
        _sectionCard('Hiện tại — theo lần quét gần nhất', [
          if (fleet.reporting == 0)
            const Text(
              'Chưa máy nào trong lần quét này báo công suất.',
              style: TextStyle(color: BeeSkyColors.muted),
            )
          else ...[
            _kv('Tổng công suất', '${fleet.kw.toStringAsFixed(2)} kW'),
            _kv('Ước tính mỗi ngày',
                '${fleet.kwhPerDay.toStringAsFixed(1)} kWh'),
            _kv('Ước tính tiền điện/ngày',
                formatVnd(fleet.kwhPerDay * priceVndKwh)),
          ],
          _kv('Máy có báo công suất', '${fleet.reporting}/${fleet.total} máy'),
          _kv('Giá điện đang dùng', '${formatVnd(priceVndKwh)}/kWh'),
        ]),
        const SizedBox(height: 12),
        _sectionCard('7 ngày qua — tích lũy từ các mẫu đã lưu', [
          if (energy.isEmpty)
            const Text(
              'Chưa đủ mẫu liên tiếp để tích lũy — điện năng cộng '
              'dồn theo các lần quét cách nhau tối đa 30 phút.',
              style: TextStyle(color: BeeSkyColors.muted),
            )
          else ...[
            _kv('Tổng', '${energy.totalKwh.toStringAsFixed(1)} kWh'),
            _kv('Ước tính tiền điện',
                formatVnd(energy.totalKwh * priceVndKwh)),
            const Divider(color: BeeSkyColors.border, height: 18),
            for (final e in dayRows)
              _kv(_dayLabel(e.key),
                  '${e.value.toStringAsFixed(1)} kWh · '
                  '≈ ${formatVnd(e.value * priceVndKwh)}'),
            const Divider(color: BeeSkyColors.border, height: 18),
            for (final e in deviceRows.take(10))
              _kv(e.key, '${e.value.toStringAsFixed(1)} kWh'),
          ],
        ]),
        const SizedBox(height: 10),
        const Text(
          'Phạm vi: ước tính từ công suất máy báo về + các mẫu quét '
          'đã lưu trên máy này. Số liệu theo giờ của bản cloud (do '
          'agent ở trại đẩy lên) xem trên web cloud.',
          style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ),
      ],
    );
  }

  String _dayLabel(String key) {
    final t = DateTime.tryParse(key);
    if (t == null) return key;
    String two(int v) => v.toString().padLeft(2, '0');
    return '${two(t.day)}/${two(t.month)}/${t.year}';
  }

  Widget _sectionCard(String title, List<Widget> children) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style:
                  const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          ...children,
        ],
      ),
    );
  }

  Widget _kv(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(
            child: Text(label,
                style: const TextStyle(color: BeeSkyColors.muted)),
          ),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

// --------------------------------------------------------------------
// 3. Lịch sử sửa — the exported ticket files, listed by the core verb
// --------------------------------------------------------------------

class RepairsView extends StatefulWidget {
  final Future<List<TicketInfo>> Function() loader;
  final String ticketsDir;
  const RepairsView({super.key, required this.loader, required this.ticketsDir});

  @override
  State<RepairsView> createState() => _RepairsViewState();
}

class _RepairsViewState extends State<RepairsView> {
  late Future<List<TicketInfo>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.loader();
  }

  void _reload() => setState(() => _future = widget.loader());

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<TicketInfo>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return viewEmptyState(Icons.build, 'Không đọc được phiếu',
              'Lỗi: ${snap.error}');
        }
        final tickets = snap.data ?? const <TicketInfo>[];
        if (tickets.isEmpty) {
          return viewEmptyState(
            Icons.build,
            'Chưa có phiếu sửa nào',
            'Xuất phiếu bằng nút "Xuất phiếu sửa" ở màn hình Máy '
            'đào — mỗi máy có vấn đề thành một file .txt trong '
            'thư mục phiếu.',
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      'Thư mục: ${widget.ticketsDir}',
                      style: const TextStyle(
                          color: BeeSkyColors.muted, fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    onPressed: _reload,
                    icon: const Icon(Icons.refresh, size: 18),
                    tooltip: 'Tải lại',
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.fromLTRB(18, 6, 18, 12),
                itemCount: tickets.length,
                itemBuilder: (context, i) => _row(tickets[i]),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _row(TicketInfo t) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: InkWell(
          onTap: () => _open(t),
          child: Row(
            children: [
              const Icon(Icons.description_outlined,
                  color: BeeSkyColors.muted, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(t.ip,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Text(
                      t.model.isEmpty ? t.file : t.model,
                      style: const TextStyle(
                          color: BeeSkyColors.muted, fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (t.problems.isNotEmpty)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: BeeSkyColors.bad.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(radiusPill),
                  ),
                  child: Text(
                    '${t.problems.length} vấn đề',
                    style: const TextStyle(
                        color: BeeSkyColors.bad, fontSize: 11.5),
                  ),
                ),
              const SizedBox(width: 10),
              Text(
                formatTicketStamp(t.modified),
                style:
                    const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _open(TicketInfo t) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Phiếu sửa — ${t.ip}'),
        content: SizedBox(
          width: 560,
          child: SingleChildScrollView(
            child: SelectableText(
              t.text,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12.5),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Đóng'),
          ),
        ],
      ),
    );
  }
}

// --------------------------------------------------------------------
// 4. Sự kiện — the engine's emissions, accumulated by the app
// --------------------------------------------------------------------

class EventsView extends StatelessWidget {
  final List<FleetEvent> events;
  const EventsView({super.key, required this.events});

  static Color severityColor(String severity) => switch (severity) {
        'critical' => BeeSkyColors.bad,
        'major' => const Color(0xFFF59E0B),
        'warning' => BeeSkyColors.warn,
        _ => BeeSkyColors.muted,
      };

  @override
  Widget build(BuildContext context) {
    if (events.isEmpty) {
      return viewEmptyState(
        Icons.notifications_none,
        'Chưa có sự kiện nào',
        'Sự kiện sinh ra khi các lần quét liên tiếp thay đổi: máy '
        'mất kết nối, sụt hashrate, quá nhiệt, mất chip, board '
        'ngắt. Lần quét đầu tiên chỉ ghi mốc nền.',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 12),
      itemCount: events.length,
      itemBuilder: (context, i) => _row(events[i]),
    );
  }

  Widget _row(FleetEvent e) {
    final color = severityColor(e.severity);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(radiusPill),
              ),
              child: Text(
                e.severityLabel,
                style: TextStyle(color: color, fontSize: 11.5),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${e.typeLabel} · ${e.ip} · ${e.model}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Text(
                    e.detail,
                    style: const TextStyle(
                        color: BeeSkyColors.muted, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Text(
              e.time,
              style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------
// 5. Cài đặt — settings that persist and take effect, nothing else
// --------------------------------------------------------------------

class SettingsView extends StatefulWidget {
  final AppSettings settings;
  final ValueChanged<AppSettings> onSave;
  final int credCount;
  final VoidCallback onOpenCreds;
  final VoidCallback onOpenGroups;
  final String ticketsDir;
  final String? coreVersion;
  final bool sidecarMissing;
  // Logs tab (v0.34): the data directory + the real store files
  // living there, and the two clear actions (each deletes its
  // file; the parent reports the result in the status line).
  final String dataDir;
  final List<StoreFileInfo> storeFiles;
  final VoidCallback onClearOpsHistory;
  final VoidCallback onClearEvents;
  const SettingsView({
    super.key,
    required this.settings,
    required this.onSave,
    required this.credCount,
    required this.onOpenCreds,
    required this.onOpenGroups,
    required this.ticketsDir,
    required this.coreVersion,
    required this.sidecarMissing,
    required this.dataDir,
    required this.storeFiles,
    required this.onClearOpsHistory,
    required this.onClearEvents,
  });

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends State<SettingsView> {
  late final TextEditingController _targetCtrl;
  late final TextEditingController _priceCtrl;
  late final TextEditingController _probeCtrl;
  late final TextEditingController _requestCtrl;
  late final TextEditingController _staggerCtrl;
  late final TextEditingController _scanWorkersCtrl;
  late final TextEditingController _opsWorkersCtrl;
  late bool _ipReport;
  late double _scale;
  String? _error;

  @override
  void initState() {
    super.initState();
    final s = widget.settings;
    _targetCtrl = TextEditingController(text: s.defaultTarget);
    _priceCtrl = TextEditingController(text: _numText(s.priceVndKwh));
    _probeCtrl = TextEditingController(text: _numText(s.probeTimeoutS));
    _requestCtrl =
        TextEditingController(text: _numText(s.requestTimeoutS));
    _staggerCtrl = TextEditingController(text: _numText(s.opsStaggerS));
    _scanWorkersCtrl =
        TextEditingController(text: '${s.scanWorkers}');
    _opsWorkersCtrl = TextEditingController(text: '${s.opsWorkers}');
    _ipReport = s.ipReportEnabled;
    _scale = s.scale;
  }

  @override
  void dispose() {
    _targetCtrl.dispose();
    _priceCtrl.dispose();
    _probeCtrl.dispose();
    _requestCtrl.dispose();
    _staggerCtrl.dispose();
    _scanWorkersCtrl.dispose();
    _opsWorkersCtrl.dispose();
    super.dispose();
  }

  static String _numText(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toString();

  double? _parseNum(TextEditingController c) {
    final text = c.text.trim().replaceAll(',', '.');
    return double.tryParse(text);
  }

  int? _parseInt(TextEditingController c) =>
      int.tryParse(c.text.trim());

  void _fail(String message) => setState(() => _error = message);

  void _save() {
    final price = _parseNum(_priceCtrl);
    if (price == null || price < 0) {
      _fail('Giá điện phải là một số ≥ 0 (VNĐ/kWh).');
      return;
    }
    final probe = _parseNum(_probeCtrl);
    if (probe == null || probe < 0.2 || probe > 10) {
      _fail('Probe timeout phải từ 0,2 đến 10 giây.');
      return;
    }
    final request = _parseNum(_requestCtrl);
    if (request == null || request < 0.2 || request > 120) {
      _fail('Request timeout phải từ 0,2 đến 120 giây.');
      return;
    }
    final stagger = _parseNum(_staggerCtrl);
    if (stagger == null || stagger < 0 || stagger > 60) {
      _fail('Dừng giữa các máy phải từ 0 đến 60 giây.');
      return;
    }
    final scanWorkers = _parseInt(_scanWorkersCtrl);
    if (scanWorkers == null || scanWorkers < 1 || scanWorkers > 256) {
      _fail('Số luồng quét phải từ 1 đến 256.');
      return;
    }
    final opsWorkers = _parseInt(_opsWorkersCtrl);
    if (opsWorkers == null || opsWorkers < 1 || opsWorkers > 8) {
      _fail('Song song thao tác phải từ 1 đến 8.');
      return;
    }
    setState(() => _error = null);
    widget.onSave(AppSettings(
      defaultTarget: _targetCtrl.text.trim(),
      priceVndKwh: price,
      probeTimeoutS: probe,
      requestTimeoutS: request,
      opsStaggerS: stagger,
      scanWorkers: scanWorkers,
      opsWorkers: opsWorkers,
      scale: _scale,
      ipReportEnabled: _ipReport,
    ));
  }

  @override
  Widget build(BuildContext context) {
    // Five tabs like HashCore's Settings dialog (General, Unlock,
    // Timeouts, Logs, Advanced — docs/settings-mapping.md §1);
    // each tab holds only settings BeeSky really has. One Lưu
    // button at the bottom saves every tab at once.
    return DefaultTabController(
      length: 5,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            tabs: [
              Tab(text: 'Chung'),
              Tab(text: 'Tài khoản'),
              Tab(text: 'Thời gian chờ'),
              Tab(text: 'Nhật ký'),
              Tab(text: 'Nâng cao'),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _generalTab(),
                _unlockTab(),
                _timeoutsTab(),
                _logsTab(),
                _advancedTab(),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(_error!,
                        style:
                            const TextStyle(color: BeeSkyColors.bad)),
                  ),
                FilledButton.icon(
                  onPressed: _save,
                  icon: const Icon(Icons.save_outlined, size: 17),
                  label: const Text('Lưu cài đặt'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _tabScroll(Widget child) => ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
        children: [child],
      );

  Widget _section(String title, List<Widget> children) => GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      );

  static const _fieldPad =
      EdgeInsets.symmetric(horizontal: 12, vertical: 10);

  Widget _generalTab() => _tabScroll(
        _section('Quét & điện', [
          TextField(
            controller: _targetCtrl,
            decoration: const InputDecoration(
              labelText: 'Mục tiêu quét mặc định',
              hintText: 'Để trống = tự nhận diện subnet như hiện tại',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _priceCtrl,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Giá điện (VNĐ/kWh)',
              hintText: 'Mặc định toàn BeeSky: 2000',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Expanded(
                child: Text('Tỉ lệ giao diện',
                    style: TextStyle(fontWeight: FontWeight.w600)),
              ),
              IconButton(
                icon: const Icon(Icons.remove, size: 18),
                tooltip: 'Thu nhỏ (Ctrl+-)',
                onPressed: _scale <= 0.9
                    ? null
                    : () => setState(
                        () => _scale = (_scale - 0.05).clamp(0.9, 1.3)),
              ),
              SizedBox(
                width: 52,
                child: Text(
                  '${(_scale * 100).round()}%',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.add, size: 18),
                tooltip: 'Phóng to (Ctrl+=)',
                onPressed: _scale >= 1.3
                    ? null
                    : () => setState(
                        () => _scale = (_scale + 0.05).clamp(0.9, 1.3)),
              ),
            ],
          ),
          const Text(
            'Phóng to/thu nhỏ chữ trong bảng và nhãn (90–130%). '
            'Khung cố định (sidebar, chiều cao hàng) không đổi.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Switch(
                value: _ipReport,
                onChanged: (v) => setState(() => _ipReport = v),
              ),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Nghe IP Report',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    Text(
                      'Lắng nghe máy đào bấm nút IP Report trên '
                      'mạng (UDP 14235/8888) — panel ở màn hình '
                      'Nhóm mạng.',
                      style: TextStyle(
                          color: BeeSkyColors.muted, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ]),
      );

  Widget _unlockTab() => _tabScroll(
        _section('Tài khoản máy đào', [
          const Text(
            'Cách mở khóa theo từng hãng nằm ở đây — cùng một bộ '
            'cài đặt dùng cho quét, xem chi tiết và thao tác.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 6),
          _linkRow(
            Icons.key_outlined,
            'Tài khoản máy đào',
            '${widget.credCount} bộ đã lưu',
            widget.onOpenCreds,
          ),
          _linkRow(
            Icons.device_hub_outlined,
            'Nhóm mạng',
            'Dải IP, tài khoản riêng và lịch tự quét theo nhóm',
            widget.onOpenGroups,
          ),
        ]),
      );

  Widget _timeoutsTab() => _tabScroll(
        _section('Thời gian chờ', [
          const Text(
            'Timeout càng lớn quét càng chậm nhưng càng ít sót máy; '
            'quá nhỏ sẽ bỏ sót máy trả lời chậm.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _probeCtrl,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Probe timeout — quét tìm máy (giây)',
              hintText: 'Mặc định: 1,5',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _requestCtrl,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Request timeout — xem chi tiết / thao tác (giây)',
              hintText: 'Mặc định: 3',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _staggerCtrl,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Dừng giữa các máy khi thao tác hàng loạt (giây)',
              hintText: 'Mặc định: 0 — chạy liền nhau',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Dừng giữa các máy: mỗi lệnh thao tác bắt đầu cách nhau '
            'khoảng này, tránh dồn máy cùng lúc.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
        ]),
      );

  Widget _logsTab() => _tabScroll(
        Column(
          children: [
            _section('Thư mục dữ liệu', [
              _info('Thư mục', widget.dataDir),
              const SizedBox(height: 6),
              for (final f in widget.storeFiles) _info(f.label, f.sizeText),
              const SizedBox(height: 6),
              _info('Thư mục phiếu sửa', widget.ticketsDir),
            ]),
            const SizedBox(height: 12),
            _section('Dọn dẹp', [
              const Text(
                'Xóa lịch sử thao tác hoặc nhật ký sự kiện đã lưu '
                'trên máy này. Máy đào và nhóm mạng không bị ảnh hưởng.',
                style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: () => _confirmClear(
                      'Xóa lịch sử thao tác?',
                      'Toàn bộ lịch sử thao tác đã chạy sẽ bị xóa.',
                      widget.onClearOpsHistory,
                    ),
                    icon: const Icon(Icons.delete_outline, size: 17),
                    label: const Text('Xóa lịch sử thao tác'),
                  ),
                  const SizedBox(width: 10),
                  OutlinedButton.icon(
                    onPressed: () => _confirmClear(
                      'Xóa nhật ký sự kiện?',
                      'Toàn bộ sự kiện đã ghi giữa các lần quét sẽ '
                      'bị xóa.',
                      widget.onClearEvents,
                    ),
                    icon: const Icon(Icons.delete_outline, size: 17),
                    label: const Text('Xóa nhật ký sự kiện'),
                  ),
                ],
              ),
            ]),
          ],
        ),
      );

  Widget _advancedTab() => _tabScroll(
        _section('Nâng cao', [
          const Text(
            'Sai số ở đây có thể làm quét chậm hoặc bỏ sót máy. '
            'Mặc định đã hợp với trại vài trăm máy.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _scanWorkersCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Số luồng quét (1–256)',
              hintText: 'Mặc định: 64',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _opsWorkersCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Thao tác song song (1–8)',
              hintText: 'Mặc định: 4',
              contentPadding: _fieldPad,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Thao tác song song: số máy được thao tác cùng lúc '
            'trong một tác vụ (quét vẫn dò song song theo số luồng '
            'quét).',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 16),
          const Text('Giới thiệu',
              style:
                  TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          _info('Phiên bản app', 'BeeSky v$beeskyAppVersion'),
          _info(
            'Ruột quét (beesky.exe)',
            widget.sidecarMissing
                ? 'Chưa có (thiếu beesky.exe)'
                : widget.coreVersion != null
                    ? 'v${widget.coreVersion}'
                    : 'Chưa đọc được',
          ),
        ]),
      );

  Future<void> _confirmClear(
      String title, String message, VoidCallback onConfirm) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: BeeSkyColors.panel,
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed == true) onConfirm();
  }

  Widget _linkRow(
      IconData icon, String title, String sub, VoidCallback onTap) {
    // A hand-rolled row, not a ListTile: inside a GlassCard the
    // tile's Material-ancestor assertion fires (the card's
    // DecoratedBox hides tile ink), so the app draws its own.
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Row(
          children: [
            Icon(icon, color: BeeSkyColors.muted, size: 21),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title),
                  Text(sub,
                      style: const TextStyle(
                          color: BeeSkyColors.muted, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: BeeSkyColors.muted),
          ],
        ),
      ),
    );
  }

  Widget _info(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 190,
            child: Text(label,
                style: const TextStyle(color: BeeSkyColors.muted)),
          ),
          Expanded(child: SelectableText(value)),
        ],
      ),
    );
  }
}
