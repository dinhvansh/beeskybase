import 'dart:convert';
import 'dart:io';

/// The product version this app reports (header pill — the Tk
/// window takes it from the Python package; here it mirrors the
/// package version, pinned by the release process).
const String agentAppVersion = '0.35.0';

/// The agent config file — a Dart mirror of the Python core's
/// `beesky/agent_config.py`, which stays the spec and the owner of
/// the format (docs/agent-app-mapping.md §1.2):
///
///   * one JSON object; the form edits exactly five fields
///     (cloud_url, key, site, target, interval); every other field
///     is carried through a save untouched, exactly like the Tk
///     window's `current_config()` (disk config as base + the five
///     form values on top);
///   * load is tolerant the way `AgentConfig.from_dict` is: unknown
///     keys ignored, scalars coerced, a non-dict `notify_config`
///     dropped to null;
///   * on disk: indented JSON, the core's field order, trailing
///     newline.
///
/// KEY HANDLING (mapping divergence D2): the file IS the channel,
/// as in Tk — but the core's Windows save DPAPI-protects the key
/// (`key_protected`, machine scope) and Dart has no DPAPI. So:
/// a stored protected blob loads as key STATE "protected" (the
/// field shows empty + a keep-or-replace hint); saving with the
/// field untouched keeps the blob verbatim (the core's own
/// no-plain-key save path); typing a key stores the core's legacy
/// plain-text form, which the core migrates to DPAPI on its next
/// save. No key is ever written anywhere else.
class AgentConfig {
  String target;
  String cloudUrl;
  String key;
  String keyProtected;
  String site;
  double interval;
  Object? notifyConfig;
  bool autoUpdate;
  double timeout;
  int workers;
  String user;
  String password;
  Object? apiKey;
  Object? token;
  int httpPort;
  int cgminerPort;
  Object? updateUrl;

  AgentConfig({
    this.target = '',
    this.cloudUrl = '',
    this.key = '',
    this.keyProtected = '',
    this.site = '',
    this.interval = 30.0,
    this.notifyConfig,
    this.autoUpdate = false,
    this.timeout = 1.5,
    this.workers = 64,
    this.user = 'root',
    this.password = 'root',
    this.apiKey,
    this.token,
    this.httpPort = 80,
    this.cgminerPort = 4028,
    this.updateUrl,
  });

  /// True when the file carries a DPAPI blob and no plain key —
  /// the key exists but this app cannot display it (D2).
  bool get hasProtectedKey => keyProtected.isNotEmpty && key.isEmpty;

  /// The key counts as present for validation when either form
  /// carries it (the Tk load would have decrypted the blob).
  bool get hasKey => key.isNotEmpty || keyProtected.isNotEmpty;

  static String _asString(Object? v) {
    // Mirrors from_dict's str() coercion of the string fields.
    if (v == null) return '';
    if (v is String) return v;
    return v.toString();
  }

  /// A string field the way from_dict resolves it: an ABSENT key
  /// keeps the dataclass default ('root' for user/password), a
  /// present one is coerced (present-null -> '').
  static String _strField(Map<String, dynamic> data, String name,
          String fallback) =>
      data.containsKey(name) ? _asString(data[name]) : fallback;

  static double _asDouble(Object? v, double fallback) {
    // Mirrors `float(x or fallback)`: null / 0 / '' fall back.
    if (v is num) return v == 0 ? fallback : v.toDouble();
    if (v is String) {
      final parsed = double.tryParse(v);
      if (parsed != null && parsed != 0) return parsed;
    }
    return fallback;
  }

  static int _asInt(Object? v, int fallback) {
    if (v is num) return v == 0 ? fallback : v.toInt();
    if (v is String) {
      final parsed = int.tryParse(v);
      if (parsed != null && parsed != 0) return parsed;
    }
    return fallback;
  }

  /// Tolerant parse, mirroring `AgentConfig.from_dict`.
  factory AgentConfig.fromJson(Map<String, dynamic> data) {
    final notify = data['notify_config'];
    return AgentConfig(
      target: _strField(data, 'target', ''),
      cloudUrl: _strField(data, 'cloud_url', ''),
      key: _strField(data, 'key', ''),
      keyProtected: _strField(data, 'key_protected', ''),
      site: _strField(data, 'site', ''),
      interval: _asDouble(data['interval'], 30.0),
      notifyConfig: notify is Map ? notify : null,
      autoUpdate: data['auto_update'] == true,
      timeout: _asDouble(data['timeout'], 1.5),
      workers: _asInt(data['workers'], 64),
      user: _strField(data, 'user', 'root'),
      password: _strField(data, 'password', 'root'),
      apiKey: data['api_key'],
      token: data['token'],
      httpPort: _asInt(data['http_port'], 80),
      cgminerPort: _asInt(data['cgminer_port'], 4028),
      updateUrl: data['update_url'],
    );
  }

  /// The on-disk document, in the core's field order.
  Map<String, dynamic> toJson() => <String, dynamic>{
        'target': target,
        'cloud_url': cloudUrl,
        'key': key,
        'key_protected': keyProtected,
        'site': site,
        'interval': interval,
        'notify_config': notifyConfig,
        'auto_update': autoUpdate,
        'timeout': timeout,
        'workers': workers,
        'user': user,
        'password': password,
        'api_key': apiKey,
        'token': token,
        'http_port': httpPort,
        'cgminer_port': cgminerPort,
        'update_url': updateUrl,
      };

  /// Required-but-empty fields, in the core's fix order
  /// (`missing_fields`: target, cloud_url, key, site). Key
  /// presence counts a stored DPAPI blob (see [hasKey]).
  List<String> missingFields() => <String>[
        if (target.trim().isEmpty) 'target',
        if (cloudUrl.trim().isEmpty) 'cloud_url',
        if (!hasKey) 'key',
        if (site.trim().isEmpty) 'site',
      ];

  String encode() =>
      '${const JsonEncoder.withIndent('  ').convert(toJson())}\n';

  static AgentConfig decode(String raw) {
    final data = jsonDecode(raw);
    if (data is! Map<String, dynamic>) {
      throw const FormatException('agent config is not a JSON object');
    }
    return AgentConfig.fromJson(data);
  }
}

/// The core's `default_scan_target` companion: interval rendering
/// (`30` when integral, else the raw float — the Tk load does
/// `str(int(i)) if i == int(i) else i`).
String formatInterval(double value) =>
    value == value.truncateToDouble() ? value.toInt().toString() : '$value';

/// The core's `default_config_path`, mirrored:
/// `$BEESKY_AGENT_CONFIG` → `%APPDATA%\BeeSky\agent-config.json`
/// (Windows) → `~/.beesky/agent-config.json`. Injectable for tests.
String defaultConfigPath({Map<String, String>? env, bool? isWindows}) {
  final e = env ?? Platform.environment;
  final win = isWindows ?? Platform.isWindows;
  final override = e['BEESKY_AGENT_CONFIG'];
  if (override != null && override.isNotEmpty) return override;
  final sep = Platform.pathSeparator;
  if (win) {
    final appdata = e['APPDATA'];
    if (appdata != null && appdata.isNotEmpty) {
      return '$appdata${sep}BeeSky${sep}agent-config.json';
    }
  }
  final home = e['HOME'] ?? e['USERPROFILE'] ?? '';
  return '$home${sep}.beesky${sep}agent-config.json';
}

/// Reads/writes the config file at [path]. An interface so widget
/// tests can substitute an in-memory store (mock mode).
abstract class AgentConfigStore {
  String get path;

  /// agent.log / agent-status.json live next to the config file
  /// (the core's status_file_path / log_file_path).
  String get statusPath;
  String get logPath;

  bool exists();

  /// Throws [FormatException] on unparseable content, mirroring
  /// the core's ValueError from `AgentConfig.load`.
  AgentConfig load();

  void save(AgentConfig cfg);

  /// Whether agent.log exists yet (the Xem log button's probe).
  bool logExists();

  /// The last cycle's status (`agent_app.read_status`): null when
  /// the agent never ran or the file is unparseable.
  AgentStatus? readStatus();

  /// agent-status.json's mtime — the Tk window polls exactly this
  /// to repaint only on change; null when the file is absent.
  DateTime? statusModified();
}

String _sibling(String configPath, String name) {
  final dir = File(configPath).parent.path;
  return '$dir${Platform.pathSeparator}$name';
}

class FileConfigStore implements AgentConfigStore {
  @override
  final String path;
  FileConfigStore(this.path);

  @override
  String get statusPath => _sibling(path, 'agent-status.json');
  @override
  String get logPath => _sibling(path, 'agent.log');

  @override
  bool exists() => File(path).existsSync();

  @override
  AgentConfig load() {
    final raw = File(path).readAsStringSync();
    try {
      return AgentConfig.decode(raw);
    } on FormatException catch (e) {
      throw FormatException('$path is not valid JSON: ${e.message}');
    }
  }

  @override
  void save(AgentConfig cfg) {
    final file = File(path);
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(cfg.encode());
  }

  @override
  bool logExists() => File(logPath).existsSync();

  @override
  AgentStatus? readStatus() {
    try {
      final data = jsonDecode(File(statusPath).readAsStringSync());
      if (data is Map<String, dynamic>) return AgentStatus.fromJson(data);
    } catch (_) {
      // Missing or broken — the core's read_status returns None
      // the same way; the card shows "Chưa có dữ liệu".
    }
    return null;
  }

  @override
  DateTime? statusModified() {
    try {
      return File(statusPath).statSync().modified;
    } catch (_) {
      return null;
    }
  }
}

/// One agent cycle's status, as written by the running agent into
/// agent-status.json (`agent_app.write_status`).
class AgentStatus {
  final String time;
  final bool ok;
  final int miners;
  final String? error;
  final String cloudUrl;
  final String site;

  const AgentStatus({
    required this.time,
    required this.ok,
    required this.miners,
    required this.error,
    required this.cloudUrl,
    required this.site,
  });

  factory AgentStatus.fromJson(Map<String, dynamic> data) => AgentStatus(
        time: (data['time'] as String?) ?? '?',
        ok: data['ok'] == true,
        miners: (data['miners'] as num?)?.toInt() ?? 0,
        error: data['error'] as String?,
        cloudUrl: (data['cloud_url'] as String?) ?? '',
        site: (data['site'] as String?) ?? '',
      );
}

/// The status card's derivation — a pure mirror of the Tk window's
/// `refresh_bg_status` (docs/agent-app-mapping.md §1.4).
class StatusView {
  /// 'dim' | 'ok' | 'bad' — the pill tones.
  final String tone;
  final String pillText;
  final String bodyText;
  const StatusView(this.tone, this.pillText, this.bodyText);
}

StatusView deriveStatusView(AgentStatus? status) {
  if (status == null) {
    return const StatusView('dim', 'Chưa có dữ liệu',
        'Agent chưa chạy vòng nào — trạng thái sẽ hiện ở đây sau vòng quét đầu tiên.');
  }
  if (status.ok) {
    return StatusView('ok', 'Đang chạy tốt',
        'Vòng gần nhất OK lúc ${status.time} — ${status.miners} máy · trại ${status.site} · cloud ${status.cloudUrl}');
  }
  return StatusView('bad', 'Lỗi gần nhất',
      'Lỗi lúc ${status.time}: ${status.error ?? 'không rõ nguyên nhân'}');
}

/// The core's `insecure_cloud_warning`, mirrored: plain http:// to
/// a non-local host sends the agent key unencrypted. Advisory only.
String? insecureCloudWarning(String cloudUrl) {
  final url = cloudUrl.trim();
  if (!url.toLowerCase().startsWith('http://')) return null;
  final host = Uri.tryParse(url)?.host.toLowerCase() ?? '';
  if (host == 'localhost' || host == '127.0.0.1' || host == '::1') {
    return null;
  }
  return 'Cloud URL dùng http:// không mã hoá — agent key sẽ đi '
      'qua mạng dạng rõ; nên dùng https:// cho cloud.';
}
