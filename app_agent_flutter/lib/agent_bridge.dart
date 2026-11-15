import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'agent_config.dart';

/// The bridge between the Flutter agent app and the BeeSky Python
/// core. The core is the ONLY engine — this app never reimplements
/// agent behaviour; it drives the shipped `beesky-agent.exe` verbs
/// the Tk window's in-process calls map onto
/// (docs/agent-app-mapping.md §3, divergences D3/D4):
///
///   Chạy thử        -> beesky-agent test --config <path> [target]
///                      --cloud .. --key .. --site .. --interval ..
///   Bật/Tắt tự khởi động -> beesky-agent install-task --config <path>
///                      / beesky-agent remove-task
///   task state      -> schtasks /Query /TN "BeeSky Agent" (the
///                      exact probe agent_app.task_installed runs)
///   first-run target-> beesky sysinfo --json (when beesky.exe is
///                      resolvable; absent on agent-only installs)
///
/// The interface exists so widget tests can inject [MockAgentBridge]
/// and never touch a real process.
class TestOutcome {
  final bool ok;

  /// The status-line text, composed exactly as the Tk window
  /// composes it: `OK [HH:MM:SS]: <verdict>` / `FAIL …`.
  final String display;
  const TestOutcome(this.ok, this.display);
}

class TaskOutcome {
  final bool ok;
  final String message;
  const TaskOutcome(this.ok, this.message);
}

abstract class AgentBridge {
  bool get isMock;

  /// Resolved beesky-agent executable (for display/diagnostics).
  String get agentExePath;

  /// The core's own-subnet pre-fill for a first run, or null when
  /// no `beesky` sidecar is resolvable (agent-only install, D5).
  Future<String?> sysinfoDefaultTarget();

  Future<bool> taskInstalled();

  Future<TaskOutcome> installTask(String configPath);

  Future<TaskOutcome> removeTask();

  /// One test cycle through the core's `test` verb. [key] is null
  /// exactly when the stored key must be used (protected/untouched
  /// — D3); otherwise the form's key travels via the core's own
  /// `--key` overlay flag.
  Future<TestOutcome> testRun({
    required String configPath,
    required String target,
    required String cloudUrl,
    required String? key,
    required String site,
    required String intervalRaw,
  });

  /// Opens [path] with the OS default handler (the Tk window's
  /// `Xem log`). Returns an error message, or null on success.
  Future<String?> openFile(String path);
}

class ProcessAgentBridge implements AgentBridge {
  final String _agentExe;
  final String? _beeskyExe;

  ProcessAgentBridge({String? agentExe, String? beeskyExe})
      : _agentExe = agentExe ?? resolveAgentExe(),
        _beeskyExe = beeskyExe ?? resolveBeeskyExe();

  @override
  bool get isMock => false;

  @override
  String get agentExePath => _agentExe;

  static String _exeName(String base) =>
      Platform.isWindows ? '$base.exe' : base;

  /// Directories searched for a sibling exe, in order: the app's
  /// own folder, then its parent (the unified installer's
  /// `{app}\agent\` layout — D6 in the mapping).
  static List<String> candidateDirs() {
    final exeDir = File(Platform.resolvedExecutable).parent;
    return [exeDir.path, exeDir.parent.path];
  }

  static String? _findSibling(String fileName) {
    for (final dir in candidateDirs()) {
      final candidate = File('$dir${Platform.pathSeparator}$fileName');
      if (candidate.existsSync()) return candidate.path;
    }
    return null;
  }

  /// Resolution order (mirrors the main app's sidecar): explicit
  /// override → BEESKY_AGENT_EXE env → --dart-define → sibling
  /// exe (own dir, then parent) → bare name on PATH.
  static String resolveAgentExe() {
    final env = Platform.environment['BEESKY_AGENT_EXE'];
    if (env != null && env.isNotEmpty) return env;
    const define = String.fromEnvironment('BEESKY_AGENT_EXE');
    if (define.isNotEmpty) return define;
    return _findSibling(_exeName('beesky-agent')) ?? _exeName('beesky-agent');
  }

  static String? resolveBeeskyExe() {
    final env = Platform.environment['BEESKY_EXE'];
    if (env != null && env.isNotEmpty) return env;
    const define = String.fromEnvironment('BEESKY_EXE');
    if (define.isNotEmpty) return define;
    return _findSibling(_exeName('beesky')) ?? _exeName('beesky');
  }

  @override
  Future<String?> sysinfoDefaultTarget() async {
    final exe = _beeskyExe;
    if (exe == null) return null;
    try {
      final result = await Process.run(exe, ['sysinfo', '--json'])
          .timeout(const Duration(seconds: 20));
      if (result.exitCode != 0) return null;
      final data = jsonDecode(result.stdout as String);
      if (data is Map<String, dynamic>) {
        final target = data['default_target'];
        if (target is String && target.isNotEmpty) return target;
      }
    } catch (_) {
      // No sidecar (agent-only install) — blank target (D5).
    }
    return null;
  }

  @override
  Future<bool> taskInstalled() async {
    // The core gates on Windows before probing (agent_app._is_windows).
    if (!Platform.isWindows) return false;
    try {
      final result = await Process.run(
          'schtasks', ['/Query', '/TN', 'BeeSky Agent']);
      return result.exitCode == 0;
    } catch (_) {
      return false;
    }
  }

  /// The `test` verb's argv — the overlay flags are the core's own
  /// form-equivalent of the Tk window's in-memory config (D3).
  static List<String> testArgs({
    required String configPath,
    required String target,
    required String cloudUrl,
    required String? key,
    required String site,
    required String intervalRaw,
  }) =>
      <String>[
        'test',
        '--config',
        configPath,
        if (target.isNotEmpty) target,
        '--cloud',
        cloudUrl,
        if (key != null) ...['--key', key],
        '--site',
        site,
        '--interval',
        intervalRaw,
      ];

  @override
  Future<TestOutcome> testRun({
    required String configPath,
    required String target,
    required String cloudUrl,
    required String? key,
    required String site,
    required String intervalRaw,
  }) async {
    final args = testArgs(
      configPath: configPath,
      target: target,
      cloudUrl: cloudUrl,
      key: key,
      site: site,
      intervalRaw: intervalRaw,
    );
    try {
      final result = await Process.run(_agentExe, args)
          .timeout(const Duration(minutes: 10));
      final stdout = (result.stdout as String).trim();
      for (final line in stdout.split('\n')) {
        final trimmed = line.trim();
        if (trimmed.startsWith('TEST OK') || trimmed.startsWith('TEST FAIL')) {
          // The Tk window composes "OK [..]: verdict" itself; the
          // CLI prints the same text with a "TEST " prefix — strip
          // it so the status line reads identically.
          return TestOutcome(
              trimmed.startsWith('TEST OK'), trimmed.substring(5));
        }
      }
      final stderr = (result.stderr as String).trim();
      final detail = stderr.isNotEmpty
          ? stderr
          : (stdout.isNotEmpty ? stdout : 'exit ${result.exitCode}');
      return TestOutcome(false, detail);
    } catch (e) {
      return TestOutcome(false, '$e');
    }
  }

  static List<String> installTaskArgs(String configPath) =>
      ['install-task', '--config', configPath];

  static List<String> removeTaskArgs() => ['remove-task'];

  Future<TaskOutcome> _runTaskVerb(List<String> args) async {
    try {
      final result = await Process.run(_agentExe, args)
          .timeout(const Duration(minutes: 2));
      final stdout = (result.stdout as String).trim();
      final stderr = (result.stderr as String).trim();
      final message = stdout.isNotEmpty ? stdout : stderr;
      return TaskOutcome(result.exitCode == 0, message);
    } catch (e) {
      return TaskOutcome(false, '$e');
    }
  }

  @override
  Future<TaskOutcome> installTask(String configPath) =>
      _runTaskVerb(installTaskArgs(configPath));

  @override
  Future<TaskOutcome> removeTask() => _runTaskVerb(removeTaskArgs());

  @override
  Future<String?> openFile(String path) async {
    try {
      if (Platform.isWindows) {
        await Process.start('cmd', ['/c', 'start', '', path],
            mode: ProcessStartMode.detached);
      } else if (Platform.isMacOS) {
        await Process.start('open', [path], mode: ProcessStartMode.detached);
      } else {
        await Process.start('xdg-open', [path],
            mode: ProcessStartMode.detached);
      }
      return null;
    } catch (e) {
      return '$e';
    }
  }
}

/// Mock mode (BEESKY_MOCK, like the main app): fixture config +
/// status, canned verb outcomes, every call recorded for tests.
class MockAgentBridge implements AgentBridge {
  bool taskInstalledState = false;
  int testCalls = 0;
  Map<String, Object?>? lastTestCall;
  String? lastOpenedFile;

  @override
  bool get isMock => true;

  @override
  String get agentExePath => 'mock/beesky-agent';

  @override
  Future<String?> sysinfoDefaultTarget() async => '192.168.1.0/24';

  @override
  Future<bool> taskInstalled() async => taskInstalledState;

  @override
  Future<TaskOutcome> installTask(String configPath) async {
    taskInstalledState = true;
    return TaskOutcome(true,
        "Đã tạo Scheduled Task 'BeeSky Agent' (SYSTEM, chạy ngầm, tự khởi động lại khi lỗi): \"beesky-agentw.exe\" run --config \"$configPath\"");
  }

  @override
  Future<TaskOutcome> removeTask() async {
    taskInstalledState = false;
    return const TaskOutcome(true, "Đã gỡ Scheduled Task 'BeeSky Agent'.");
  }

  @override
  Future<TestOutcome> testRun({
    required String configPath,
    required String target,
    required String cloudUrl,
    required String? key,
    required String site,
    required String intervalRaw,
  }) async {
    testCalls++;
    lastTestCall = {
      'configPath': configPath,
      'target': target,
      'cloudUrl': cloudUrl,
      'key': key,
      'site': site,
      'intervalRaw': intervalRaw,
    };
    final now = DateTime.now();
    String two(int v) => v.toString().padLeft(2, '0');
    final stamp = '${two(now.hour)}:${two(now.minute)}:${two(now.second)}';
    return TestOutcome(true,
        "OK [$stamp]: đã đẩy snapshot 2 máy lên $cloudUrl (site '$site')");
  }

  @override
  Future<String?> openFile(String path) async {
    lastOpenedFile = path;
    return null;
  }
}

/// In-memory config store for mock mode and widget tests: seeded
/// from a fixture document, saves kept in memory.
class MockConfigStore implements AgentConfigStore {
  String? _content;
  AgentStatus? statusFixture;
  DateTime? statusMtime;

  MockConfigStore({String? fixtureJson, this.statusFixture, this.statusMtime})
      : _content = fixtureJson;

  /// The demo farm fixture (illustrative values, the same style as
  /// the main app's mock fleet): a configured agent with one
  /// scan-side field (workers) the form must carry through a save.
  factory MockConfigStore.demo() => MockConfigStore(
        fixtureJson: '{\n'
            '  "target": "192.168.1.10-192.168.1.60",\n'
            '  "cloud_url": "https://cloud.beeskybase.com",\n'
            '  "key": "demo-agent-key",\n'
            '  "key_protected": "",\n'
            '  "site": "Trại Demo",\n'
            '  "interval": 30.0,\n'
            '  "notify_config": null,\n'
            '  "auto_update": false,\n'
            '  "workers": 32\n'
            '}\n',
        statusFixture: const AgentStatus(
          time: '2026-11-11 07:45:00',
          ok: true,
          miners: 2,
          error: null,
          cloudUrl: 'https://cloud.beeskybase.com',
          site: 'Trại Demo',
        ),
        statusMtime: DateTime(2026, 11, 11, 7, 45),
      );

  /// A config whose key only exists as a DPAPI blob (D2's state).
  factory MockConfigStore.protectedKey() => MockConfigStore(
        fixtureJson: '{\n'
            '  "target": "192.168.2.0/24",\n'
            '  "cloud_url": "https://cloud.beeskybase.com",\n'
            '  "key": "",\n'
            '  "key_protected": "QUJDREVGRw==",\n'
            '  "site": "Trại Demo",\n'
            '  "interval": 45.0\n'
            '}\n',
      );

  @override
  String get path => 'mock/agent-config.json';
  @override
  String get statusPath => 'mock/agent-status.json';
  @override
  String get logPath => 'mock/agent.log';

  @override
  bool exists() => _content != null;

  @override
  AgentConfig load() {
    final raw = _content;
    if (raw == null) throw const FormatException('no fixture config');
    return AgentConfig.decode(raw);
  }

  @override
  void save(AgentConfig cfg) {
    _content = cfg.encode();
  }

  @override
  bool logExists() => statusFixture != null;

  /// The saved document, for round-trip assertions.
  String? get savedRaw => _content;

  @override
  AgentStatus? readStatus() => statusFixture;

  @override
  DateTime? statusModified() => statusMtime;
}

/// Bridge + store selection, mirroring the main app's
/// `createBridge()`: BEESKY_MOCK env / dart-define → fixtures,
/// otherwise the real sidecar + the core's default config path.
(AgentBridge, AgentConfigStore) createAgentRuntime() {
  final env = Platform.environment['BEESKY_MOCK'];
  const define = String.fromEnvironment('BEESKY_MOCK');
  if ((env != null && env.isNotEmpty && env != '0') || define.isNotEmpty) {
    return (MockAgentBridge(), MockConfigStore.demo());
  }
  return (ProcessAgentBridge(), FileConfigStore(defaultConfigPath()));
}
