import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'detail.dart';
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
/// THE message for a missing scan engine (v0.32, Workstream B —
/// docs/views-mapping.md). The owner's first real-Windows run
/// (2026-11-12) extracted the portable zip standalone, so no
/// beesky.exe sat beside the app and every bridge call failed
/// with the raw OS text "The system cannot find the file
/// specified". From v0.32 the zip bundles the exe, and when the
/// file is STILL absent (partial copy, quarantine) every surface
/// — scan, tickets, sysinfo, ops, inspect — says exactly this,
/// never a raw ProcessException.
const String missingSidecarMessage =
    'Không tìm thấy beesky.exe cạnh app — hãy giải nén app vào '
    'cùng thư mục với beesky.exe (hoặc cài bằng BeeSkySetup), và '
    'kiểm tra Windows Defender > Protection history nếu file bị '
    'cách ly.';

abstract class BeeSkyBridge {
  bool get isMock;

  /// Resolved sidecar executable path, or null for the mock bridge.
  /// The sidebar's status dot uses it to tell "sidecar found" apart
  /// from "beesky.exe missing next to the app".
  String? get exePath;

  /// True when the resolved sidecar is a concrete path that does
  /// not exist on disk — the v0.32 missing-engine state (a bare
  /// PATH name can never prove itself missing, so it stays false).
  bool get sidecarMissing;

  /// The folder repair tickets are exported to / listed from:
  /// `<sidecar dir>/tickets`, the export's own staging dir.
  String get ticketsDirPath;

  /// The file the IP-Report listener persists reports to:
  /// `<sidecar dir>/beesky-ipreports.json` (the core's
  /// `ipreport listen --out` store, v0.34).
  String get ipreportsFilePath;

  Future<SysInfo> sysinfo();

  /// One scan pass. [credsFile] is the app's saved credential-sets
  /// file (the --creds-file schema) or null when no sets are saved —
  /// passwords never travel on the command line (v0.23).
  /// [eventsState] (v0.32) is the core EventEngine's persisted
  /// state file for THIS target; the result then carries the
  /// events this pass diffed out (docs/views-mapping.md §4).
  /// [timeout]/[workers] (v0.34) are the Timeouts/Advanced
  /// settings, passed as `scan --timeout/--workers`.
  Future<ScanResult> scan(
    String target, {
    String? credsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  });

  /// One scan of a saved network group (v0.24): the CORE resolves
  /// the group's targets, merges the group's own credential sets
  /// ahead of the global [credsFile] ones, and persists the group's
  /// last_scan into [groupsFile] (the core's default store location
  /// applies when null).
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  });

  /// Exports repair tickets; returns a human-readable destination.
  Future<String> exportTickets(String target, {String? credsFile});

  /// Lists the exported repair tickets in [dir] through the
  /// core's read-only `tickets` verb (v0.32); newest first.
  Future<List<TicketInfo>> listTickets(String dir);

  /// Starts ONE Operations task (v0.26): [job] is the core runner's
  /// job document (type / targets / payload / group / creds_file —
  /// VALUES travel inside the job FILE, never on argv; credential
  /// sets are referenced by path). Returns the run handle: event
  /// stream + summary future + Stop.
  Future<OpsRun> startOps(Map<String, dynamic> job);

  /// Deep-fetch ONE device (v0.27): pools / fans / per-board
  /// detail for the detail tabs, through the core's
  /// `inspect --json` — the scan record does not carry them.
  /// Credential resolution is the scan's own: [credsFile]'s sets,
  /// led by [group]'s when a group scope is active (the core
  /// resolves; only paths and the group NAME travel on argv).
  /// [timeout] (v0.34) is the request timeout setting.
  Future<InspectResult> inspect(
    String ip, {
    String? credsFile,
    String? group,
    String? groupsFile,
    double? timeout,
  });

  /// Starts the IP-Report listener (v0.34): `beesky ipreport
  /// listen --json --out <ipreportsFilePath>`, streamed NDJSON —
  /// the panel's live feed, modelled on the ops run. The run
  /// persists reports to the store file itself (core-side).
  Future<IpReportRun> startIpReport();

  /// Lists the persisted IP reports through the core's read-only
  /// `ipreport list` verb (v0.34); newest first. Empty when the
  /// store file does not exist yet.
  Future<List<IpReport>> listIpReports();
}

/// One live `beesky ipreport listen` sidecar run: NDJSON lines in,
/// [IpReport]s out. Stopping kills the process; the store file
/// keeps what arrived.
abstract class IpReportRun {
  Stream<IpReport> get reports;
  Future<void> stop();
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

  @override
  bool get sidecarMissing =>
      exePath.contains(Platform.pathSeparator) &&
      !File(exePath).existsSync();

  /// Throws the ONE missing-engine message when the sidecar is a
  /// concrete path that isn't there — called before every spawn so
  /// no surface can leak the raw OS "file not found" text (v0.32).
  void _requireSidecar() {
    if (sidecarMissing) throw SidecarException(missingSidecarMessage);
  }

  @override
  String get ticketsDirPath =>
      '${_exeBaseDir(exePath)}${Platform.pathSeparator}tickets';

  /// The directory the sidecar exe lives in (or '.' when the exe
  /// is a bare PATH name) — the base every app-managed file that
  /// must sit WITH the engine uses (tickets dir, ops job file).
  static String _exeBaseDir(String exePath) =>
      exePath.contains(Platform.pathSeparator)
          ? File(exePath).parent.path
          : '.';

  /// Sidecar resolution order:
  /// 1. explicit constructor override (tests / tooling),
  /// 2. BEESKY_EXE environment variable,
  /// 3. --dart-define=BEESKY_EXE=…,
  /// 4. beesky.exe sitting next to this app's executable (the shipped
  ///    bundle layout — see .github/workflows/build-flutter.yml).
  /// 5. fallback: on Windows the EXPLICIT sibling path from step 4
  ///    even when the file is absent (v0.32): both shipped layouts
  ///    (installer, self-contained zip) place beesky.exe there, so
  ///    a missing file becomes the knowable [sidecarMissing] state
  ///    with one clear message — the pre-v0.32 bare `beesky` name
  ///    instead failed every call with the raw OS "The system
  ///    cannot find the file specified" (owner's 2026-11-12 test).
  ///    POSIX keeps the bare `beesky` from PATH (dev machines with
  ///    the package installed).
  static String resolveBeeSkyExe() {
    final env = Platform.environment['BEESKY_EXE'];
    if (env != null && env.isNotEmpty) return env;
    const define = String.fromEnvironment('BEESKY_EXE');
    if (define.isNotEmpty) return define;
    final dir = File(Platform.resolvedExecutable).parent.path;
    final sibling = File('$dir${Platform.pathSeparator}beesky.exe');
    if (sibling.existsSync()) return sibling.path;
    return Platform.isWindows ? sibling.path : 'beesky';
  }

  Future<Map<String, dynamic>> _runJson(
    List<String> args, {
    Duration timeout = const Duration(minutes: 10),
  }) async {
    _requireSidecar();
    final ProcessResult result;
    try {
      result = await Process.run(
        exePath,
        args,
        stdoutEncoding: utf8,
      ).timeout(timeout);
    } on ProcessException catch (e) {
      // The exe vanished between the check and the spawn (or a
      // PATH-resolved name stopped resolving): same one message.
      if (sidecarMissing) throw SidecarException(missingSidecarMessage);
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
  /// credential value ever appears in argv (v0.23). [eventsState]
  /// (v0.32) is a PATH too — the EventEngine state file whose
  /// diff lands in the payload's "events".
  static List<String> scanArgs(
    String target, {
    String? credsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  }) {
    final args = <String>['scan', target, '--json'];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    if (eventsState != null) args.addAll(['--events-state', eventsState]);
    if (timeout != null) args.addAll(['--timeout', '$timeout']);
    if (workers != null) args.addAll(['--workers', '$workers']);
    return args;
  }

  /// Argument list for the read-only tickets listing (v0.32):
  /// `beesky tickets --dir DIR --json` — one JSON document out.
  static List<String> listTicketsArgs(String dir) =>
      ['tickets', '--dir', dir, '--json'];

  /// Argument list for the tickets pass (a scan with --tickets).
  static List<String> ticketsArgs(
    String target,
    String dirPath, {
    String? credsFile,
    double? timeout,
    int? workers,
  }) {
    final args = <String>['scan', target, '--tickets', dirPath];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    if (timeout != null) args.addAll(['--timeout', '$timeout']);
    if (workers != null) args.addAll(['--workers', '$workers']);
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
    String? eventsState,
    double? timeout,
    int? workers,
  }) {
    final args = <String>['scan', '--group', name, '--json'];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    if (groupsFile != null) args.addAll(['--groups-file', groupsFile]);
    if (eventsState != null) args.addAll(['--events-state', eventsState]);
    if (timeout != null) args.addAll(['--timeout', '$timeout']);
    if (workers != null) args.addAll(['--workers', '$workers']);
    return args;
  }

  /// Argument list for the IP-Report listener (v0.34):
  /// `beesky ipreport listen --out FILE` — NDJSON to stdout, the
  /// store file beside the exe so reports survive restarts.
  static List<String> ipReportArgs(String outPath) =>
      ['ipreport', 'listen', '--out', outPath];

  /// Argument list for the read-only IP-Report listing (v0.34).
  static List<String> listIpReportsArgs(String filePath) =>
      ['ipreport', 'list', '--file', filePath, '--json'];

  /// Argument list for an ops run — the job travels as a FILE
  /// (its path is the only ops argument; no secret value ever
  /// appears in argv, the v0.23 rule applied to tasks).
  static List<String> opsArgs(String jobPath) => ['ops', '--job', jobPath];

  /// Argument list for an inspect run — factored out for tests
  /// like [scanArgs]: the device IP plus file PATHS only (the
  /// group is referenced by name; its sets resolve core-side).
  static List<String> inspectArgs(
    String ip, {
    String? credsFile,
    String? group,
    String? groupsFile,
    double? timeout,
  }) {
    final args = <String>['inspect', ip, '--json'];
    if (credsFile != null) args.addAll(['--creds-file', credsFile]);
    if (group != null) args.addAll(['--group', group]);
    if (groupsFile != null) args.addAll(['--groups-file', groupsFile]);
    if (timeout != null) args.addAll(['--timeout', '$timeout']);
    return args;
  }

  @override
  Future<InspectResult> inspect(
    String ip, {
    String? credsFile,
    String? group,
    String? groupsFile,
    double? timeout,
  }) async {
    final doc = await _runJson(
      inspectArgs(ip,
          credsFile: credsFile,
          group: group,
          groupsFile: groupsFile,
          timeout: timeout),
      timeout: const Duration(seconds: 60),
    );
    return InspectResult.fromJson(doc);
  }

  @override
  String get ipreportsFilePath =>
      '${_exeBaseDir(exePath)}${Platform.pathSeparator}'
      'beesky-ipreports.json';

  @override
  Future<IpReportRun> startIpReport() async {
    _requireSidecar();
    final Process process;
    try {
      process =
          await Process.start(exePath, ipReportArgs(ipreportsFilePath));
    } on ProcessException catch (e) {
      if (sidecarMissing) throw SidecarException(missingSidecarMessage);
      throw SidecarException('Không chạy được beesky ($exePath): ${e.message}');
    }
    return _SidecarIpReportRun(process);
  }

  @override
  Future<List<IpReport>> listIpReports() async {
    if (sidecarMissing) return const [];
    final file = File(ipreportsFilePath);
    if (!file.existsSync()) return const [];
    final doc = await _runJson(listIpReportsArgs(ipreportsFilePath),
        timeout: const Duration(seconds: 30));
    return ((doc['reports'] as List<dynamic>?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(IpReport.fromJson)
        .toList();
  }

  @override
  Future<OpsRun> startOps(Map<String, dynamic> job) async {
    _requireSidecar();
    final baseDir = _exeBaseDir(exePath);
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
      if (sidecarMissing) throw SidecarException(missingSidecarMessage);
      throw SidecarException('Không chạy được beesky ($exePath): ${e.message}');
    }
    return _SidecarOpsRun(process, job, jobFile);
  }

  @override
  Future<ScanResult> scan(
    String target, {
    String? credsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  }) async {
    final doc = await _runJson(
      scanArgs(target,
          credsFile: credsFile,
          eventsState: eventsState,
          timeout: timeout,
          workers: workers),
    );
    return ScanResult.fromJson(doc);
  }

  @override
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  }) async {
    final doc = await _runJson(
      scanGroupArgs(
        name,
        credsFile: credsFile,
        groupsFile: groupsFile,
        eventsState: eventsState,
        timeout: timeout,
        workers: workers,
      ),
    );
    return ScanResult.fromJson(doc);
  }

  @override
  Future<List<TicketInfo>> listTickets(String dir) async {
    final doc = await _runJson(
      listTicketsArgs(dir),
      timeout: const Duration(seconds: 30),
    );
    return ((doc['tickets'] as List<dynamic>?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(TicketInfo.fromJson)
        .toList();
  }

  @override
  Future<String> exportTickets(String target, {String? credsFile}) async {
    // Tickets are a post-step of `scan` (--tickets DIR prints one
    // .txt per problem miner), so the export runs a scan pass with
    // that flag next to the sidecar exe — same behaviour as the
    // Tk app's button. (The v0.32 `tickets` verb only LISTS what
    // exports wrote; it never scans.)
    _requireSidecar();
    final dir = Directory(ticketsDirPath);
    await dir.create(recursive: true);
    final args = ticketsArgs(target, dir.path, credsFile: credsFile);
    final ProcessResult result;
    try {
      result = await Process.run(exePath, args, stdoutEncoding: utf8);
    } on ProcessException catch (e) {
      // Pre-v0.32 this escaped UNWRAPPED — the owner's screenshot
      // showed the raw "ProcessException: … Command: beesky scan …"
      // text. It now lands in the same SidecarException channel
      // as every other bridge failure.
      if (sidecarMissing) throw SidecarException(missingSidecarMessage);
      throw SidecarException('Không chạy được beesky ($exePath): ${e.message}');
    }
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

/// One live `beesky ipreport listen` sidecar run (v0.34): NDJSON
/// lines in, [IpReport]s out — the ops run's streaming shape,
/// without a summary (the listener runs until stopped). The first
/// line is the {"listening": [...]} announcement, skipped like a
/// stray line; every {"report": {...}} line becomes a report.
class _SidecarIpReportRun implements IpReportRun {
  final Process _process;
  final StreamController<IpReport> _controller =
      StreamController<IpReport>();

  _SidecarIpReportRun(this._process) {
    _process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen(_onLine, onError: (_) {});
    // Drain stderr so a chatty failure can't fill the pipe buffer.
    _process.stderr.listen((_) {}, onError: (_) {});
    _process.exitCode.then((_) {
      if (!_controller.isClosed) _controller.close();
    });
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
    final report = doc['report'];
    if (report is Map<String, dynamic>) {
      if (!_controller.isClosed) {
        _controller.add(IpReport.fromJson(report));
      }
    }
  }

  @override
  Stream<IpReport> get reports => _controller.stream;

  @override
  Future<void> stop() async {
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

  @override
  bool get sidecarMissing => false;

  @override
  String get ticketsDirPath => '(mock) tickets';

  @override
  String get ipreportsFilePath => '(mock) ipreports';

  /// Canned IP reports for the mock panel (v0.34): one Antminer
  /// report with a payload IP+MAC, one Whatsminer report that only
  /// the sender address identifies.
  static final List<IpReport> _sampleReports = [
    IpReport(
      receivedAt:
          DateTime.now().millisecondsSinceEpoch / 1000.0 - 120,
      sender: '192.168.2.101',
      text: '192.168.2.101,AA:BB:CC:DD:EE:01',
      ip: '192.168.2.101',
      mac: 'AA:BB:CC:DD:EE:01',
      family: 'antminer',
    ),
    IpReport(
      receivedAt:
          DateTime.now().millisecondsSinceEpoch / 1000.0 - 45,
      sender: '192.168.2.105',
      text: '',
      ip: null,
      mac: null,
      family: 'whatsminer',
    ),
  ];

  @override
  Future<IpReportRun> startIpReport() async => _MockIpReportRun();

  @override
  Future<List<IpReport>> listIpReports() async =>
      List<IpReport>.unmodifiable(_sampleReports);

  static const String _sampleJson = '''
{"records": [
  {"ip": "192.168.2.101", "model": "Antminer S19 Pro", "source": "vnish",
   "chains": [{"index": 0, "temp_c": 61.0, "chips_alive": 114, "chips_total": 114},
              {"index": 1, "temp_c": 65.0, "chips_alive": 114, "chips_total": 114},
              {"index": 2, "temp_c": 63.0, "chips_alive": 114, "chips_total": 114}],
   "fans_rpm": [4120, 4080, 4150, 4090], "chips_alive": 342, "chips_total": 342,
   "max_temp_c": 65.0, "problems": [], "status": "OK",
   "cred_label": "VNish trại A",
   "pools": [{"url": "stratum+tcp://pool.example.com:3333",
              "worker": "mockworker.001", "status": "alive"},
             {"url": "stratum+tcp://backup.example.com:3333",
              "worker": "mockworker.002", "status": "alive"}],
   "rate_value": 110.5, "rate_unit": "TH/s", "ths": 110.5},
  {"ip": "192.168.2.102", "model": "Antminer L9", "source": "cgminer",
   "chains": [{"index": 0, "temp_c": 57.0, "chips_alive": 123, "chips_total": 123},
              {"index": 1, "temp_c": 59.0, "chips_alive": 84, "chips_total": 123},
              {"index": 2, "temp_c": 58.0, "chips_alive": 123, "chips_total": 123}],
   "fans_rpm": [4560, 4440], "chips_alive": 330, "chips_total": 369,
   "max_temp_c": 59.0,
   "problems": [{"code": "MISSING_CHIPS", "severity": "warn",
                 "detail": "board 1: 84/123 chip"}],
   "pools": [{"url": "stratum+tcp://pool.example.com:3333",
              "worker": "mockworker.001", "status": "Alive"}],
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
   "status": "CHECK", "rate_value": null, "rate_unit": null, "ths": null},
  {"ip": "192.168.2.105", "model": "WhatsMiner M30S", "source": "whatsminer",
   "chains": [{"index": 0, "temp_c": 62.0, "chips_alive": 0, "chips_total": 0},
              {"index": 1, "temp_c": 87.0, "chips_alive": 0, "chips_total": 0},
              {"index": 2, "temp_c": 65.0, "chips_alive": 0, "chips_total": 0}],
   "fans_rpm": [4560, 4620], "chips_alive": 0, "chips_total": 0,
   "max_temp_c": 87.0,
   "problems": [{"code": "OVER_TEMP", "severity": "warn",
                 "detail": "chain 2: 87 C >= 85 C limit"}],
   "pools": [{"url": "stratum+tcp://btc.pool.example:3333",
              "worker": "wmworker.001", "status": "Alive"}],
   "status": "CHECK", "rate_value": 111.8, "rate_unit": "TH/s", "ths": 111.8}
 ],
 "scanned": 254, "found": 5, "elapsed_s": 3.42}
''';

  @override
  Future<SysInfo> sysinfo() async =>
      const SysInfo(version: '0.38.0', defaultTarget: '192.168.2.0/24');

  /// The sample fleet's event story (v0.32): the Z15 crossed the
  /// temp limit and the L9 lost chips since the previous pass —
  /// exactly the diffs the real engine would emit. Returned only
  /// when the caller passes an events-state file, like the core.
  static List<FleetEvent> _sampleEvents() {
    final now = DateTime.now();
    String stamp(DateTime t) =>
        '${t.year.toString().padLeft(4, '0')}-${t.month.toString().padLeft(2, '0')}-${t.day.toString().padLeft(2, '0')} '
        '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}:${t.second.toString().padLeft(2, '0')}';
    return [
      FleetEvent(
        ts: now.millisecondsSinceEpoch / 1000.0,
        time: stamp(now),
        ip: '192.168.2.103',
        model: 'Antminer Z15',
        source: 'cgminer',
        type: 'OVER_TEMP',
        severity: 'warning',
        detail: 'max temp 88 C >= 85 C limit (mock)',
      ),
      FleetEvent(
        ts: now.millisecondsSinceEpoch / 1000.0 - 60,
        time: stamp(now.subtract(const Duration(minutes: 1))),
        ip: '192.168.2.102',
        model: 'Antminer L9',
        source: 'cgminer',
        type: 'CHIPS_LOST',
        severity: 'major',
        detail: 'alive chips 369 -> 330 (mock)',
      ),
    ];
  }

  @override
  Future<ScanResult> scan(
    String target, {
    String? credsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    final base =
        ScanResult.fromJson(jsonDecode(_sampleJson) as Map<String, dynamic>);
    if (eventsState == null) return base;
    return ScanResult(
      records: base.records,
      scanned: base.scanned,
      found: base.found,
      elapsedS: base.elapsedS,
      events: _sampleEvents(),
    );
  }

  @override
  Future<ScanResult> scanGroup(
    String name, {
    String? credsFile,
    String? groupsFile,
    String? eventsState,
    double? timeout,
    int? workers,
  }) =>
      scan(name, eventsState: eventsState);

  @override
  Future<String> exportTickets(String target, {String? credsFile}) async =>
      '(mock) không ghi file phiếu thật';

  @override
  Future<List<TicketInfo>> listTickets(String dir) async => const [
        TicketInfo(
          file: 'ticket-192_168_2_103.txt',
          ip: '192.168.2.103',
          modified: '2026-11-11T20:14:03',
          model: 'Antminer Z15',
          problems: ['Board 1: nhiệt độ cao 88°C (ngưỡng 85°C)'],
          text: 'PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO — BeeSky\n'
              'IP: 192.168.2.103\nModel: Antminer Z15\n(mock)',
        ),
        TicketInfo(
          file: 'ticket-192_168_2_102.txt',
          ip: '192.168.2.102',
          modified: '2026-11-11T20:14:03',
          model: 'Antminer L9',
          problems: ['Board 1: thiếu 39 chip (vị trí chết: 85, 86, …)'],
          text: 'PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO — BeeSky\n'
              'IP: 192.168.2.102\nModel: Antminer L9\n(mock)',
        ),
      ];

  @override
  Future<OpsRun> startOps(Map<String, dynamic> job) async =>
      _MockOpsRun(job);

  /// Inspect fixtures mirroring the sample fleet's families:
  /// the S19 (vnish) gets the grade split + fan mode, the L9/Z15
  /// (cgminer) get acs boards (NO grade buckets — the DATA-GAP
  /// is part of the fixture), and the unreachable unit is an
  /// honest error document, exactly like the real core's.
  @override
  Future<InspectResult> inspect(
    String ip, {
    String? credsFile,
    String? group,
    String? groupsFile,
    double? timeout,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 250));
    final doc = _inspectFixtures[ip] ??
        <String, dynamic>{
          'ip': ip,
          'source': null,
          'error': 'no miner answered on the RPC or web ports (mock)',
        };
    return InspectResult.fromJson(doc);
  }

  static Map<String, dynamic> _vnishBoard(
    int index,
    int stable,
    int slow,
    int critical,
    List<int> dead,
    double chipTemp,
    double pcbTemp,
  ) =>
      {
        'index': index,
        'chips_total': stable + slow + critical,
        'stable': stable,
        'slow': slow,
        'critical': critical,
        'dead_positions': dead,
        'chip_temp_c': chipTemp,
        'pcb_temp_c': pcbTemp,
        'chips': null,
      };

  static Map<String, dynamic> _acsBoard(
    int index,
    int total,
    int ok,
    List<int> dead,
    double temp,
  ) =>
      {
        'index': index,
        'acs': List<String>.generate(
          total,
          (i) => dead.contains(i + 1) ? 'x' : 'o',
        ).join(),
        'chips_total': total,
        'chips_ok': ok,
        'dead_positions': dead,
        'other_chars': {if (dead.isNotEmpty) 'x': dead.length},
        'temp_c': temp,
      };

  static final Map<String, Map<String, dynamic>> _inspectFixtures = {
    '192.168.2.101': {
      'ip': '192.168.2.101',
      'source': 'vnish',
      'model': 'Antminer S19 Pro',
      'cred_label': 'VNish trại A',
      'boards': {
        'supported': true,
        'boards': [
          _vnishBoard(1, 114, 0, 0, const [], 61, 49),
          _vnishBoard(2, 114, 0, 0, const [], 65, 52),
          _vnishBoard(3, 114, 0, 0, const [], 63, 51),
        ],
      },
      'pools': {
        'supported': true,
        'pools': [
          {
            'id': 0,
            'url': 'stratum+tcp://pool.example.com:3333',
            'user': 'mockworker.001',
            'status': 'working',
            'accepted': 2048,
            'rejected': 12,
            'stale': 1,
            'ping': 42,
          },
        ],
      },
      'fans': {
        'supported': true,
        'mode': 'auto',
        'mode_param': null,
        'duty_pct': 62,
        'fans': [
          {'id': 1, 'rpm': 4120, 'status': 'ok', 'max_rpm': 6000},
          {'id': 2, 'rpm': 4080, 'status': 'ok', 'max_rpm': 6000},
          {'id': 3, 'rpm': 4150, 'status': 'ok', 'max_rpm': 6000},
          {'id': 4, 'rpm': 4090, 'status': 'ok', 'max_rpm': 6000},
        ],
      },
    },
    '192.168.2.102': {
      'ip': '192.168.2.102',
      'source': 'cgminer',
      'model': 'Antminer L9',
      'cred_label': null,
      'boards': {
        'supported': true,
        'boards': [
          _acsBoard(1, 123, 123, const [], 57),
          _acsBoard(
            2,
            123,
            84,
            [for (var i = 85; i <= 123; i++) i],
            59,
          ),
          _acsBoard(3, 123, 123, const [], 58),
        ],
      },
      'pools': {
        'supported': true,
        'pools': [
          {
            'id': 0,
            'url': 'stratum+tcp://pool.example.com:3333',
            'user': 'mockworker.001',
            'status': 'Alive',
            'accepted': 2048,
            'rejected': 12,
          },
        ],
      },
      'fans': {
        'supported': true,
        'mode': null,
        'fans': [
          {'id': 1, 'rpm': 4560},
          {'id': 2, 'rpm': 4440},
        ],
      },
    },
    '192.168.2.103': {
      'ip': '192.168.2.103',
      'source': 'cgminer',
      'model': 'Antminer Z15',
      'cred_label': null,
      'boards': {
        'supported': true,
        'boards': [
          _acsBoard(1, 24, 24, const [], 71),
          _acsBoard(2, 24, 24, const [], 88),
          _acsBoard(3, 24, 24, const [], 73),
        ],
      },
      'pools': {
        'supported': true,
        'pools': [
          {
            'id': 0,
            'url': 'stratum+tcp://pool.example.com:3333',
            'user': 'mockworker.001',
            'status': 'Alive',
            'accepted': 1024,
            'rejected': 3,
          },
        ],
      },
      'fans': {
        'supported': true,
        'mode': null,
        'fans': [
          {'id': 1, 'rpm': 3900},
          {'id': 2, 'rpm': 3840},
        ],
      },
    },
    '192.168.2.104': {
      'ip': '192.168.2.104',
      'source': null,
      'error': 'không kết nối được (cổng 4028/80) (mock)',
    },
    // Whatsminer (v0.30): boards carry temps with chip counts
    // 0/0 — per-chip data is not in the evidenced socket contract
    // (docs/vendor-coverage-mapping.md G-W2), exactly like the
    // real core's inspect document.
    '192.168.2.105': {
      'ip': '192.168.2.105',
      'source': 'whatsminer',
      'model': 'WhatsMiner M30S',
      'cred_label': null,
      'boards': {
        'supported': true,
        'boards': [
          {
            'index': 1,
            'chips_total': 0,
            'chips_ok': 0,
            'dead_positions': <int>[],
            'other_chars': <String, int>{},
            'temp_c': 62.0,
          },
          {
            'index': 2,
            'chips_total': 0,
            'chips_ok': 0,
            'dead_positions': <int>[],
            'other_chars': <String, int>{},
            'temp_c': 87.0,
          },
          {
            'index': 3,
            'chips_total': 0,
            'chips_ok': 0,
            'dead_positions': <int>[],
            'other_chars': <String, int>{},
            'temp_c': 65.0,
          },
        ],
      },
      'pools': {
        'supported': true,
        'pools': [
          {
            'id': 0,
            'url': 'stratum+tcp://btc.pool.example:3333',
            'user': 'wmworker.001',
            'status': 'Alive',
            'accepted': 123456,
            'rejected': 123,
          },
        ],
      },
      'fans': {
        'supported': true,
        'mode': null,
        'fans': [
          {'id': 1, 'rpm': 4560},
          {'id': 2, 'rpm': 4620},
        ],
      },
    },
  };
}

/// The mock ops path: simulates the core runner's lifecycle against
/// the sample fleet — per-device progress events, the unreachable
/// unit failing honestly, switch_pool failing on non-VNish sources
/// exactly like the real executors, and Stop accounting the
/// unstarted remainder as cancelled.
/// Mock IP-Report run (v0.34): emits the canned reports once,
/// shortly after start, then stays quiet until stopped.
class _MockIpReportRun implements IpReportRun {
  final StreamController<IpReport> _controller =
      StreamController<IpReport>();

  _MockIpReportRun() {
    Future<void>.delayed(const Duration(milliseconds: 150), () {
      if (_controller.isClosed) return;
      for (final r in MockBridge._sampleReports) {
        _controller.add(r);
      }
    });
  }

  @override
  Stream<IpReport> get reports => _controller.stream;

  @override
  Future<void> stop() async {
    await _controller.close();
  }
}

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
    // The v0.29 VNish tail is dashd-only in the core, so the mock
    // fails it honestly on other families too (vnish-ops-mapping).
    const dashdOnly = {
      'pause_mining',
      'resume_mining',
      'restart_mining',
      'find_miner',
      'throttle',
      'reset_autotune_all',
      'reset_autotune_current',
      'configure_api_key',
      'set_preset',
      'change_password',
    };
    if (dashdOnly.contains(type) && rec.source != 'vnish') {
      return (
        false,
        '$type is not supported for this source yet (mock)',
        null,
      );
    }
    if (type == 'diagnostic_report') {
      // The BeeSky-variant bundle: any answering family produces
      // one in the real core (record + inspect), so the mock does
      // too — the message names the file it would have written.
      return (
        true,
        'diagnostic report saved: $ip-diagnostic.json (mock)',
        null,
      );
    }
    final payload = _job['payload'] as Map<String, dynamic>?;
    final tailMessages = <String, String>{
      'pause_mining': 'dashd accepted mining pause (mock)',
      'resume_mining': 'dashd accepted mining resume (mock)',
      'restart_mining': 'dashd accepted mining restart (mock)',
      'find_miner': 'dashd locate-miner is ON (mock)',
      'throttle':
          'dashd throttle set to ${payload?['percent'] ?? 100}% (mock)',
      'reset_autotune_all': 'dashd reset ALL autotune profiles (mock)',
      'reset_autotune_current':
          "dashd reset the current autotune profile 'perf-110' (mock)",
      'configure_api_key': 'dashd saved the API key — '
          "device reports 'inserted' (mock)",
      'set_preset':
          "dashd preset set to '${payload?['preset'] ?? ''}' (mock)",
      'change_password': 'dashd accepted the password change (mock)',
    };
    if (tailMessages.containsKey(type)) {
      return (true, tailMessages[type]!, null);
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
