/// Pool presets + worker-pattern expansion (v0.28) — the
/// HashCore Toolkit's pool presets ported per
/// docs/presets-ipreport-mapping.md §1/§3.
///
/// A pool preset is a NAMED set of up to 3 pool slots
/// ({url, worker, password}); worker strings may carry the
/// dissected pattern tokens ({n}, {ip4}, {account}, …),
/// expanded PER DEVICE by the core runner at apply time —
/// the app expands them only for the editor's live Preview,
/// through [expandWorkerPattern], a deliberate mirror of
/// beesky/core/patterns.py pinned to the same case table by
/// both test suites.
library;

import 'models.dart';

/// One pool slot of a preset. An empty slot (url AND worker
/// blank) is an editor artefact — it is never stored
/// ([PoolPreset] drops empties, so slot position = pool_id).
class PoolSlot {
  String url;
  String worker;
  String password;
  PoolSlot({this.url = '', this.worker = '', this.password = ''});

  bool get isEmpty => url.trim().isEmpty && worker.trim().isEmpty;

  /// The ops-job form (core switch_pool pools payload):
  /// worker rides RAW — patterns expand core-side per device.
  Map<String, dynamic> toJobJson() => {
        'url': url.trim(),
        'user': worker.trim(),
        if (password.isNotEmpty) 'password': password,
      };

  Map<String, dynamic> toJson() => {
        'url': url,
        'worker': worker,
        'password': password,
      };

  factory PoolSlot.fromJson(Map<String, dynamic> json) => PoolSlot(
        url: (json['url'] ?? '') as String,
        worker: (json['worker'] ?? json['user'] ?? '') as String,
        password: (json['password'] ?? '') as String,
      );

  PoolSlot copy() =>
      PoolSlot(url: url, worker: worker, password: password);
}

/// A named pool preset (HashCore PoolPreset: name + optional
/// description + the slot list; its storage keys are BeeSky's
/// own — the original's are UNKNOWN, mapping §1.1).
class PoolPreset {
  String name;
  String description;
  List<PoolSlot> slots;

  PoolPreset({
    required this.name,
    this.description = '',
    required this.slots,
  });

  /// The slots that apply: stored slots are non-empty by
  /// construction; the filter keeps hand-edited files honest.
  List<PoolSlot> get activeSlots =>
      slots.where((s) => !s.isEmpty).toList();

  Map<String, dynamic> toJson() => {
        'name': name,
        if (description.isNotEmpty) 'description': description,
        'slots': activeSlots.map((s) => s.toJson()).toList(),
      };

  factory PoolPreset.fromJson(Map<String, dynamic> json) =>
      PoolPreset(
        name: (json['name'] ?? '') as String,
        description: (json['description'] ?? '') as String,
        slots: ((json['slots'] as List<dynamic>?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(PoolSlot.fromJson)
            .toList(),
      );

  PoolPreset copy() => PoolPreset(
        name: name,
        description: description,
        slots: slots.map((s) => s.copy()).toList(),
      );
}

// --------------------------------------------------------------------
// Worker pattern expansion — the Dart mirror of
// beesky/core/patterns.py (same tokens, same failures).
// --------------------------------------------------------------------

/// A worker pattern cannot be expanded for this device —
/// the message names the missing data (never a silent guess).
class PatternException implements Exception {
  final String message;
  const PatternException(this.message);
  @override
  String toString() => message;
}

/// Everything an expansion may read for one device.
class PatternContext {
  final String ip;
  final int index; // 0-based position in the task's target list
  final String? currentUser; // current pool-1 worker
  final String? currentUrl; // current pool-1 URL
  final String? mac; // no BeeSky source yet
  final String? host; // not carried on records
  const PatternContext({
    required this.ip,
    this.index = 0,
    this.currentUser,
    this.currentUrl,
    this.mac,
    this.host,
  });

  /// The context for the editor Preview: a record's first
  /// pool slot supplies the "current" values (HashCore's
  /// pool-change dialog shows the FIRST selected device's
  /// data — the preview follows the same rule).
  factory PatternContext.ofRecord(
    MinerRecord record, {
    required int index,
  }) =>
      PatternContext(
        ip: record.ip,
        index: index,
        currentUser:
            record.pools.isEmpty ? null : record.pools.first.worker,
        currentUrl:
            record.pools.isEmpty ? null : record.pools.first.url,
      );
}

final RegExp _tokenRe = RegExp(r'\{([^{}]*)\}');

const List<String> _currentPoolTokens = [
  'account',
  'worker',
  'pool-host',
  'port',
  'proto-str',
];

/// True when expanding [template] reads the current pool.
bool patternNeedsCurrentPool(String template) {
  for (final m in _tokenRe.allMatches(template)) {
    final head = m.group(1)!.trim().split(':').first;
    if (_currentPoolTokens.contains(head)) return true;
  }
  return false;
}

(String, String, int) _currentUrlParts(PatternContext ctx, String token) {
  final url = ctx.currentUrl;
  if (url == null || url.isEmpty) {
    throw PatternException(
      'pattern {$token} needs the device\'s current pool, '
      'and none is known for this device',
    );
  }
  final uri = Uri.tryParse(url);
  if (uri == null || uri.host.isEmpty || uri.port == 0) {
    throw PatternException(
      'pattern {$token}: current pool URL $url carries no host:port',
    );
  }
  return (uri.scheme, uri.host, uri.port);
}

String _expandToken(String token, PatternContext ctx) {
  final body = token.trim();
  if (body.startsWith('ip:')) {
    final div = body.substring(3);
    return ctx.ip.replaceAll('.', div.isEmpty ? '.' : div);
  }
  if (const {'ip1', 'ip2', 'ip3', 'ip4'}.contains(body)) {
    final octets = ctx.ip.split('.');
    if (octets.length != 4) {
      throw PatternException(
        'pattern {$token}: ${ctx.ip} is not an IPv4 address',
      );
    }
    return octets[int.parse(body[2]) - 1];
  }
  final head = body.split(':').first;
  if (head == 'n' || head == 'nn' || head == 'nnn') {
    final parts = body.split(':');
    if (parts.length > 3) {
      throw PatternException('pattern {$token}: too many \':\' parts');
    }
    final start =
        (parts.length > 1 && parts[1].isNotEmpty) ? int.tryParse(parts[1]) : 1;
    final step =
        (parts.length > 2 && parts[2].isNotEmpty) ? int.tryParse(parts[2]) : 1;
    if (start == null || step == null) {
      throw PatternException(
        'pattern {$token}: start/step must be integers',
      );
    }
    final value = start + ctx.index * step;
    return switch (head) {
      'nn' => value.toString().padLeft(2, '0'),
      'nnn' => value.toString().padLeft(3, '0'),
      _ => '$value',
    };
  }
  if (body == 'account' || body == 'worker') {
    final user = ctx.currentUser;
    if (user == null) {
      throw PatternException(
        'pattern {$token} needs the device\'s current pool '
        'worker, and none is known for this device',
      );
    }
    final dot = user.indexOf('.');
    if (body == 'account') return dot < 0 ? user : user.substring(0, dot);
    return dot < 0 ? '' : user.substring(dot + 1);
  }
  if (body == 'pool-host' || body == 'port' || body == 'proto-str') {
    final (scheme, host, port) = _currentUrlParts(ctx, token);
    return switch (body) {
      'pool-host' => host,
      'port' => '$port',
      _ => scheme,
    };
  }
  if (body == 'mac') {
    final mac = ctx.mac;
    if (mac == null || mac.isEmpty) {
      throw const PatternException(
        'pattern {mac} needs the device\'s MAC address, '
        'which BeeSky\'s scan data does not carry',
      );
    }
    return mac.replaceAll(':', '').replaceAll('-', '');
  }
  if (body == 'host' || body == 'h') {
    final host = ctx.host;
    if (host == null || host.isEmpty) {
      throw PatternException(
        'pattern {$token} needs the device\'s hostname, '
        'which BeeSky\'s scan data does not carry',
      );
    }
    return host;
  }
  throw PatternException('unknown pattern {$token}');
}

/// Expand every pattern token in [template] against [ctx].
/// Literal text passes through untouched. Throws
/// [PatternException] on unknown/malformed tokens and on
/// tokens whose source data the context does not carry —
/// the same contract as the core expander.
String expandWorkerPattern(String template, PatternContext ctx) {
  return template.replaceAllMapped(
    _tokenRe,
    (m) => _expandToken(m.group(1)!, ctx),
  );
}

/// The pattern help — HashCore's "Show available patterns"
/// list (mapping §1.4), Vietnamese labels, tokens verbatim.
const List<(String, String)> patternHelp = [
  ('{account}', 'Tài khoản pool hiện tại (phần trước dấu . đầu tiên)'),
  ('{worker}', 'Worker hiện tại (phần sau dấu . đầu tiên)'),
  ('{ip:.}', 'IP của máy, các octet cách nhau bằng dấu .'),
  ('{ip1}…{ip4}', 'Từng octet của IP máy'),
  ('{n:1:1}', 'Số thứ tự của máy trong danh sách tác vụ (bắt đầu : bước nhảy)'),
  ('{nn} / {nnn}', 'Số thứ tự có thêm 1 / 2 số 0 ở đầu'),
  ('{pool-host}', 'Địa chỉ pool hiện tại của máy'),
  ('{port}', 'Cổng pool hiện tại của máy'),
  ('{proto-str}', 'Giao thức của pool hiện tại (stratum+tcp…)'),
  ('{mac}', 'Địa chỉ MAC (không dấu :) — dữ liệu quét chưa có, máy sẽ báo lỗi'),
  ('{host}', 'Hostname — dữ liệu quét chưa có, máy sẽ báo lỗi'),
];
