import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'models.dart';
import 'ops.dart';

/// The bridge between the Flutter shell and the BeeSky Python engine.
///
/// The Python core is the ONLY engine (scanner / agent / cloud stay
/// untouched): this app drives the `beesky` CLI executable as a sidecar
/// and consumes its JSON bridge (v0.21.0):
///   beesky sysinfo --json           -> {"version", "default_target"}
///   beesky scan <target> --json …   -> {"records", "scanned", ...}
///
/// The interface exists so widget tests can inject [MockBridge] and never
/// touch a real process.
abstract class BeeSkyBridge {
  bool get isMock;

  /// Resolved sidecar executable path, or null for the mock bridge.
  /// The sidebar's status dot uses it to tell "sidecar found" apart
  /// from "beesky.exe missing next to the app".
  String? get exePath;
  Future<SysInfo> sysinfo();

  /// One scan pass. [credsFile] is the app's saved credential-sets
  /// file (the --creds-file schema) or null when no sets are saved —
  /// passwords never travel on the command line (v0.23).
  Future<ScanResult> scan(String target, {String? credsFile});

  /// One scan of a saved network group (v0.24): the CORE resolves
  /// the group's targets, merges the group's own credential sets
  /// ahead of the global [credsFile] ones, and persists the group's
  /// last_scan into [groupsFile] (the core's default store location
  /// applies when null).
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
  });

  /// Exports repair tickets; returns a human-readable destination.
  Future<String> exportTickets(String target, {String? credsFile});

  /// Starts ONE Operations task (v0.26): [job] is the core runner's
  /// job document (type / targets / payload / group / creds_file —
  /// VALUES travel inside the job FILE, never on argv; credential
  /// sets are referenced by path). Returns the run handle: event
  /// stream + summary future + Stop.
  Future<OpsRun> startOps(Map<String, dynamic> job);
}

/// Opens [url] in the OS default browser — used for a miner's own
/// web admin on row double-click (BTC Tools-style). Windows goes
/// through `cmd /c start`, macOS through `open`, Linux `xdg-open`.
Future<void> openUrlInBrowser(String url) async {
  if (Platform.isWindows) {
    await Process.start('cmd', ['/c', 'start', '', url],
        mode: ProcessStartMode.detached);
  } else if (Platform.isMacOS) {
    await Process.start('open', [url], mode: ProcessStartMode.detached);
  } else {
    await Process.start('xdg-open', [url], mode: ProcessStartMode.detached);
  }
}

class SidecarException implements Exception {
  final String message;
  SidecarException(this.message);
  @override
  String toString() => message;
}

class SidecarBridge implements BeeSkyBridge {
  final String exePath;
  SidecarBridge({String? exePath}) : exePath = exePath ?? resolveBeeSkyExe();

  @override
  bool get isMock => false;

  /// Sidecar resolution order:
  /// 1. explicit constructor override (tests / tooling),
  /// 2. BEESKY_EXE environment variable,
  /// 3. --dart-define=BEESKY_EXE=…,
  /// 4. beesky.exe sitting next to this app's executable (the shipped
  ///    bundle layout — see .github/workflows/build-flutter.yml),
  /// 5. plain `beesky` from PATH (dev machines with the package installed).
  static String resolveBeeSkyExe() {
    final env = Platform.environment['BEESKY_EXE'];
    if (env != null && env.isNotEmpty) return env;
    const define = String.fromEnvironment('BEESKY_EXE');
    if (define.isNotEmpty) return define;
    final dir = File(Platform.resolvedExecutable).parent.path;
    final sibling = File('$dir${Platform.pathSeparator}beesky.exe');
    if (sibling.existsSync()) return sibling.path;
    return 'beesky';
  }

  Future<Map<String, dynamic>> _runJson(
    List<String> args, {
    Duration timeout = const Duration(minutes: 10),
  }) async {
    final ProcessResult result;
    try {
      result = await Process.run(
        exePath,
        args,
        stdoutEncoding: utf8,
      ).timeout(timeout);
    } on ProcessException catch (e) {
      throw SidecarException('Không chạy được beesky ($exePath): ${e.message}');
    } on TimeoutException {
      throw SidecarException('beesky chạy quá lâu, đã hủy: ${args.join(' ')}');
    }
    if (result.exitCode != 0) {
      final err = ('${result.stderr}').trim();
      throw SidecarException(
        err.isNotEmpty ? err : 'beesky thoát với mã ${result.exitCode}',
      );
    }
    try {
      // Bridge mode guarantees stdout is exactly ONE JSON document.
      return jsonDecode('${result.stdout}') as Map<String, dynamic>;
    } on FormatException {
      throw SidecarException('Phản hồi từ beesky không phải JSON hợp lệ.');
    }
  }

  @override
  Future<SysInfo> sysinfo() async {
    final doc = await _runJson([
      'sysinfo',
      '--json',
    ], timeout: const Duration(seconds: 20));
    return SysInfo.fromJson(doc);
  }

  /// Argument list for a bridge scan — factored out so tests can pin
  /// the contract: the creds file is referenced by PATH only; no
  /// credential value ever appears in argv (v0.23).
  static List<String> scanArgs(String target, {String? credsFile}) {
    final args = <String>['scan', target, '--json'];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    return args;
  }

  /// Argument list for the tickets pass (a scan with --tickets).
  static List<String> ticketsArgs(
    String target,
    String dirPath, {
    String? credsFile,
  }) {
    final args = <String>['scan', target, '--tickets', dirPath];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    return args;
  }

  /// Argument list for a group scan — factored out for tests like
  /// [scanArgs]: `scan --group <name>` with NO positional target
  /// (the core takes it from the group), plus the file paths the
  /// core needs (values never travel, only paths — v0.24).
  static List<String> scanGroupArgs(
    String name, {
    String? credsFile,
    String? groupsFile,
  }) {
    final args = <String>['scan', '--group', name, '--json'];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    if (groupsFile != null) args.addAll(['--groups-file', groupsFile]);
    return args;
  }

  /// Argument list for an ops run — the job travels as a FILE
  /// (its path is the only ops argument; no secret value ever
  /// appears in argv, the v0.23 rule applied to tasks).
  static List<String> opsArgs(String jobPath) => ['ops', '--job', jobPath];

  @override
  Future<OpsRun> startOps(Map<String, dynamic> job) async {
    final exeFile = File(exePath);
    final baseDir =
        exePath.contains(Platform.pathSeparator) ? exeFile.parent.path : '.';
    final files = OpsFiles(
      primaryDir: Directory(baseDir),
      fallbackDir: OpsFiles.appDefault().fallbackDir,
    );
    var jobFile = files.jobFile;
    try {
      jobFile.writeAsStringSync(jsonEncode(job));
    } on FileSystemException {
      // Bundle dir refused the write (Program Files): the job
      // file lands in the fallback dir, like every other store.
      files.fallbackDir.createSync(recursive: true);
      jobFile = File(
        '${files.fallbackDir.path}${Platform.pathSeparator}'
        '${OpsFiles.jobFileName}',
      );
      jobFile.writeAsStringSync(jsonEncode(job));
    }
    final Process process;
    try {
      process = await Process.start(exePath, opsArgs(jobFile.path));
    } on ProcessException catch (e) {
      throw SidecarException('Không chạy được beesky ($exePath): ${e.message}');
    }
    return _SidecarOpsRun(process, job, jobFile);
  }

  @override
  Future<ScanResult> scan(String target, {String? credsFile}) async {
    final doc = await _runJson(scanArgs(target, credsFile: credsFile));
    return ScanResult.fromJson(doc);
  }

  @override
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
  }) async {
    final doc = await _runJson(
      scanGroupArgs(name, credsFile: credsFile, groupsFile: groupsFile),
    );
    return ScanResult.fromJson(doc);
  }

  @override
  Future<String> exportTickets(String target, {String? credsFile}) async {
    // There is no standalone "tickets" verb in the CLI: tickets are a
    // post-step of `scan` (--tickets DIR prints one .txt per problem
    // miner). Stage 1 therefore runs a scan pass with that flag next to
    // the sidecar exe — same behaviour as the Tk app's button.
    // TODO(stage-2): a `tickets` verb re-using the last scan's records
    // would avoid the second network pass.
    final exeFile = File(exePath);
    final baseDir =
        exePath.contains(Platform.pathSeparator) ? exeFile.parent.path : '.';
    final dir = Directory('$baseDir${Platform.pathSeparator}tickets');
    await dir.create(recursive: true);
    final args = ticketsArgs(target, dir.path, credsFile: credsFile);
    final result = await Process.run(exePath, args, stdoutEncoding: utf8);
    if (result.exitCode != 0) {
      final err = ('${result.stderr}').trim();
      throw SidecarException(
        err.isNotEmpty
            ? err
            : 'Xuất phiếu sửa thất bại (mã ${result.exitCode})',
      );
    }
    final count = dir
        .listSync()
        .whereType<File>()
        .where((f) => f.path.toLowerCase().endsWith('.txt'))
        .length;
    return '${dir.path} ($count phiếu)';
  }

}

/// One live `beesky ops` sidecar run: NDJSON lines in, [OpsEvent]s
/// out (the summary LINE is consumed into the summary future, not
/// forwarded as an event). When the process dies without a summary
/// — the Windows Stop kills it outright — the summary is
/// SYNTHESISED from the received results so every device is still
/// accounted (mapping §4.7). The job file (which can carry a pool
/// password) is deleted when the run ends.
class _SidecarOpsRun implements OpsRun {
  final Process _process;
  final File _jobFile;
  final int _total;
  final Stopwatch _clock = Stopwatch()..start();
  final StreamController<OpsEvent> _controller = StreamController<OpsEvent>();
  final Completer<OpsSummary> _summary = Completer<OpsSummary>();
  OpsSummary? _coreSummary;
  bool _stopped = false;
  int _results = 0;
  int _ok = 0;

  _SidecarOpsRun(this._process, Map<String, dynamic> job, this._jobFile)
      : _total = ((job['targets'] as List<dynamic>?) ?? const []).length {
    _process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen(_onLine, onError: (_) {});
    // Drain stderr so a chatty failure can't fill the pipe buffer.
    _process.stderr.listen((_) {}, onError: (_) {});
    _process.exitCode.then(_onExit);
  }

  void _onLine(String line) {
    final trimmed = line.trim();
    if (trimmed.isEmpty) return;
    final Map<String, dynamic> doc;
    try {
      doc = jsonDecode(trimmed) as Map<String, dynamic>;
    } on FormatException {
      return; // bridge contract is NDJSON; a stray line is ignored
    }
    if (doc['event'] == 'summary') {
      _coreSummary = OpsSummary.fromJson(doc);
      return;
    }
    final event = OpsEvent.fromJson(doc);
    if (event.kind == 'result') {
      _results++;
      if (event.ok == true) _ok++;
    }
    if (!_controller.isClosed) _controller.add(event);
  }

  void _onExit(int exitCode) {
    _clock.stop();
    try {
      _jobFile.deleteSync();
    } on FileSystemException {
      // Already gone / never landed — nothing to clean.
    }
    final summary = _coreSummary ??
        OpsSummary(
          total: _total,
          completed: _results,
          ok: _ok,
          failed: _results - _ok,
          cancelled: _total - _results,
          status: _stopped
              ? OpsStatus.cancelled
              : (exitCode != 0 && _results == 0)
                  ? OpsStatus.error
                  : (_results - _ok == 0
                      ? OpsStatus.success
                      : (_ok == 0 ? OpsStatus.error : OpsStatus.hasErrors)),
          elapsedS: _clock.elapsedMilliseconds / 1000.0,
        );
    if (!_summary.isCompleted) _summary.complete(summary);
    _controller.close();
  }

  @override
  Stream<OpsEvent> get events => _controller.stream;

  @override
  Future<OpsSummary> get summary => _summary.future;

  @override
  Future<void> stop() async {
    _stopped = true;
    _process.kill();
  }
}

/// Dev/demo bridge: canned data, no process. Enabled with the BEESKY_MOCK
/// environment variable or --dart-define=BEESKY_MOCK=1, and used directly
/// by the widget tests. The sample fleet intentionally includes the two
/// machines that exposed the v0.20 unit bug — an L9 at 14.54 MH/s and a
/// Z15 at 1101.00 ksol/s — plus one sick S19 and one unreachable unit.
/// The Z15's middle board runs at 88 °C (over the core's 85 °C limit,
/// reported exactly as the core reports it: OVER_TEMP + CHECK) so the
/// red per-board temp state is exercised everywhere temps are shown.
class MockBridge implements BeeSkyBridge {
  @override
  bool get isMock => true;

  @override
  String? get exePath => null;

  static const String _sampleJson = '''
{"records": [
  {"ip": "192.168.2.101", "model": "Antminer S19 Pro", "source": "vnish",
   "chains": [{"index": 0, "temp_c": 61.0, "chips_alive": 114, "chips_total": 114},
              {"index": 1, "temp_c": 65.0, "chips_alive": 114, "chips_total": 114},
              {"index": 2, "temp_c": 63.0, "chips_alive": 114, "chips_total": 114}],
   "fans_rpm": [4120, 4080, 4150, 4090], "chips_alive": 342, "chips_total": 342,
   "max_temp_c": 65.0, "problems": [], "status": "OK",
   "cred_label": "VNish trại A",
   "rate_value": 110.5, "rate_unit": "TH/s", "ths": 110.5},
  {"ip": "192.168.2.102", "model": "Antminer L9", "source": "cgminer",
   "chains": [{"index": 0, "temp_c": 57.0, "chips_alive": 123, "chips_total": 123},
              {"index": 1, "temp_c": 59.0, "chips_alive": 84, "chips_total": 123},
              {"index": 2, "temp_c": 58.0, "chips_alive": 123, "chips_total": 123}],
   "fans_rpm": [4560, 4440], "chips_alive": 330, "chips_total": 369,
   "max_temp_c": 59.0,
   "problems": [{"code": "MISSING_CHIPS", "severity": "warn",
                 "detail": "board 1: 84/123 chip"}],
   "status": "CHECK", "rate_value": 14.54, "rate_unit": "MH/s", "ths": null},
  {"ip": "192.168.2.103", "model": "Antminer Z15", "source": "cgminer",
   "chains": [{"index": 0, "temp_c": 71.0, "chips_alive": 24, "chips_total": 24},
              {"index": 1, "temp_c": 88.0, "chips_alive": 24, "chips_total": 24},
              {"index": 2, "temp_c": 73.0, "chips_alive": 24, "chips_total": 24}],
   "fans_rpm": [3900, 3840], "chips_alive": 72, "chips_total": 72,
   "max_temp_c": 88.0,
   "problems": [{"code": "OVER_TEMP", "severity": "warn",
                 "detail": "chain 1: 88 C >= 85 C limit"}],
   "status": "CHECK",
   "rate_value": 1101.0, "rate_unit": "ksol/s", "ths": null},
  {"ip": "192.168.2.104", "model": "—", "source": "cgminer",
   "chains": [], "fans_rpm": [], "chips_alive": 0, "chips_total": 0,
   "max_temp_c": null,
   "problems": [{"code": "FETCH_ERROR", "severity": "error",
                 "detail": "không kết nối được (cổng 4028/80)"}],
   "status": "CHECK", "rate_value": null, "rate_unit": null, "ths": null}
 ],
 "scanned": 254, "found": 4, "elapsed_s": 3.42}
''';

  @override
  Future<SysInfo> sysinfo() async =>
      const SysInfo(version: '0.26.0', defaultTarget: '192.168.2.0/24');

  @override
  Future<ScanResult> scan(String target, {String? credsFile}) async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    return ScanResult.fromJson(jsonDecode(_sampleJson) as Map<String, dynamic>);
  }

  @override
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
  }) =>
      scan(name);

  @override
  Future<String> exportTickets(String target, {String? credsFile}) async =>
      '(mock) không ghi file phiếu thật';

  @override
  Future<OpsRun> startOps(Map<String, dynamic> job) async =>
      _MockOpsRun(job);
}

/// The mock ops path: simulates the core runner's lifecycle against
/// the sample fleet — per-device progress events, the unreachable
/// unit failing honestly, switch_pool failing on non-VNish sources
/// exactly like the real executors, and Stop accounting the
/// unstarted remainder as cancelled.
class _MockOpsRun implements OpsRun {
  final Map<String, dynamic> _job;
  final StreamController<OpsEvent> _controller = StreamController<OpsEvent>();
  final Completer<OpsSummary> _summary = Completer<OpsSummary>();
  Timer? _timer;
  bool _stopped = false;
  int _done = 0;
  int _ok = 0;

  _MockOpsRun(this._job) {
    final targets = ((_job['targets'] as List<dynamic>?) ?? const [])
        .map((e) => '$e')
        .toList();
    _controller.onListen = () {
      _controller.add(OpsEvent(kind: 'start', total: targets.length));
      var idx = 0;
      _timer = Timer.periodic(const Duration(milliseconds: 60), (timer) {
        if (idx >= targets.length) {
          _finish(cancelled: 0);
          return;
        }
        final ip = targets[idx++];
        final (ok, message, record) = _mockResult(ip);
        _done++;
        if (ok) _ok++;
        _controller.add(OpsEvent(
          kind: 'result',
          done: _done,
          total: targets.length,
          ip: ip,
          ok: ok,
          message: message,
          record: record,
        ));
        if (idx >= targets.length) _finish(cancelled: 0);
      });
    };
  }

  (bool, String, MinerRecord?) _mockResult(String ip) {
    final fleet = ScanResult.fromJson(
      jsonDecode(MockBridge._sampleJson) as Map<String, dynamic>,
    ).records;
    MinerRecord? rec;
    for (final r in fleet) {
      if (r.ip == ip) rec = r;
    }
    final type = _job['type'];
    if (rec == null) {
      return (
        false,
        'miner is not answering and its source could not be probed '
            '— action not executed (mock)',
        null,
      );
    }
    if (type == 'rescan') {
      return rec.hasFetchError
          ? (false, 'rescan: không kết nối được (mock)', rec)
          : (true, 'rescanned (${rec.source}) (mock)', rec);
    }
    if (rec.hasFetchError) {
      return (false, 'không kết nối được (mock)', null);
    }
    if (type == 'switch_pool' && rec.source != 'vnish') {
      return (
        false,
        'switch_pool is not supported for this source yet (mock)',
        null,
      );
    }
    return (
      true,
      type == 'switch_pool'
          ? 'dashd switched the active pool (mock)'
          : 'đã khởi động lại (mock)',
      null,
    );
  }

  void _finish({required int cancelled}) {
    _timer?.cancel();
    _timer = null;
    final targets = ((_job['targets'] as List<dynamic>?) ?? const []).length;
    final failed = _done - _ok;
    if (!_summary.isCompleted) {
      _summary.complete(OpsSummary(
        total: targets,
        completed: _done,
        ok: _ok,
        failed: failed,
        cancelled: cancelled,
        status: _stopped
            ? OpsStatus.cancelled
            : (failed == 0
                ? OpsStatus.success
                : (_ok == 0 ? OpsStatus.error : OpsStatus.hasErrors)),
        elapsedS: 0,
      ));
    }
    _controller.close();
  }

  @override
  Stream<OpsEvent> get events => _controller.stream;

  @override
  Future<OpsSummary> get summary => _summary.future;

  @override
  Future<void> stop() async {
    if (_summary.isCompleted) return;
    _stopped = true;
    final targets = ((_job['targets'] as List<dynamic>?) ?? const []).length;
    _finish(cancelled: targets - _done);
  }
}

/// Bridge selection for the real app: mock when BEESKY_MOCK is set in the
/// environment or via --dart-define, the sidecar otherwise.
BeeSkyBridge createBridge() {
  final env = Platform.environment['BEESKY_MOCK'];
  const define = String.fromEnvironment('BEESKY_MOCK');
  if ((env != null && env.isNotEmpty && env != '0') || define.isNotEmpty) {
    return MockBridge();
  }
  return SidecarBridge();
}
