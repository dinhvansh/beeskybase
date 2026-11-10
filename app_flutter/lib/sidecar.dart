import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'models.dart';

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
  Future<SysInfo> sysinfo();
  Future<ScanResult> scan(
    String target, {
    String user = '',
    String password = '',
  });

  /// Exports repair tickets; returns a human-readable destination.
  Future<String> exportTickets(
    String target, {
    String user = '',
    String password = '',
  });

  /// Starts the local web dashboard (`beesky serve`) and opens a browser.
  Future<void> openLocalWeb(String target);
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

  @override
  Future<ScanResult> scan(
    String target, {
    String user = '',
    String password = '',
  }) async {
    final args = <String>['scan', target, '--json'];
    // Credentials are only forwarded when non-empty (the CLI treats an
    // empty --user/--password as "not provided").
    if (user.isNotEmpty) args.addAll(['--user', user]);
    if (password.isNotEmpty) args.addAll(['--password', password]);
    final doc = await _runJson(args);
    return ScanResult.fromJson(doc);
  }

  @override
  Future<String> exportTickets(
    String target, {
    String user = '',
    String password = '',
  }) async {
    // There is no standalone "tickets" verb in the CLI: tickets are a
    // post-step of `scan` (--tickets DIR prints one .txt per problem
    // miner). Stage 1 therefore runs a scan pass with that flag next to
    // the sidecar exe — same behaviour as the Tk app's button.
    // TODO(stage-2): a `tickets` verb re-using the last scan's records
    // would avoid the second network pass.
    final exeFile = File(exePath);
    final baseDir = exePath.contains(Platform.pathSeparator)
        ? exeFile.parent.path
        : '.';
    final dir = Directory('$baseDir${Platform.pathSeparator}tickets');
    await dir.create(recursive: true);
    final args = <String>['scan', target, '--tickets', dir.path];
    if (user.isNotEmpty) args.addAll(['--user', user]);
    if (password.isNotEmpty) args.addAll(['--password', password]);
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

  @override
  Future<void> openLocalWeb(String target) async {
    // Mirrors the Tk app: `beesky serve <target> --port 8787` detached,
    // then the OS browser on http://localhost:8787.
    // TODO(stage-2): the url_launcher plugin would open the browser more
    // cleanly than the OS shell; kept dependency-free for stage 1.
    const port = 8787;
    await Process.start(exePath, [
      'serve',
      target,
      '--port',
      '$port',
    ], mode: ProcessStartMode.detached);
    final url = 'http://localhost:$port';
    if (Platform.isWindows) {
      await Process.start('cmd', [
        '/c',
        'start',
        '',
        url,
      ], mode: ProcessStartMode.detached);
    } else if (Platform.isMacOS) {
      await Process.start('open', [url], mode: ProcessStartMode.detached);
    } else {
      await Process.start('xdg-open', [url], mode: ProcessStartMode.detached);
    }
  }
}

/// Dev/demo bridge: canned data, no process. Enabled with the BEESKY_MOCK
/// environment variable or --dart-define=BEESKY_MOCK=1, and used directly
/// by the widget tests. The sample fleet intentionally includes the two
/// machines that exposed the v0.20 unit bug — an L9 at 14.54 MH/s and a
/// Z15 at 1101.00 ksol/s — plus one sick S19 and one unreachable unit.
class MockBridge implements BeeSkyBridge {
  @override
  bool get isMock => true;

  static const String _sampleJson = '''
{"records": [
  {"ip": "192.168.2.101", "model": "Antminer S19 Pro", "source": "vnish",
   "chains": [{"index": 0, "temp_c": 61.0, "chips_alive": 114, "chips_total": 114},
              {"index": 1, "temp_c": 65.0, "chips_alive": 114, "chips_total": 114},
              {"index": 2, "temp_c": 63.0, "chips_alive": 114, "chips_total": 114}],
   "fans_rpm": [4120, 4080, 4150, 4090], "chips_alive": 342, "chips_total": 342,
   "max_temp_c": 65.0, "problems": [], "status": "OK",
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
   "chains": [{"index": 0, "temp_c": 55.0, "chips_alive": 24, "chips_total": 24},
              {"index": 1, "temp_c": 58.0, "chips_alive": 24, "chips_total": 24},
              {"index": 2, "temp_c": 56.0, "chips_alive": 24, "chips_total": 24}],
   "fans_rpm": [3900, 3840], "chips_alive": 72, "chips_total": 72,
   "max_temp_c": 58.0, "problems": [], "status": "OK",
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
      const SysInfo(version: '0.21.0', defaultTarget: '192.168.2.0/24');

  @override
  Future<ScanResult> scan(
    String target, {
    String user = '',
    String password = '',
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    return ScanResult.fromJson(jsonDecode(_sampleJson) as Map<String, dynamic>);
  }

  @override
  Future<String> exportTickets(
    String target, {
    String user = '',
    String password = '',
  }) async => '(mock) không ghi file phiếu thật';

  @override
  Future<void> openLocalWeb(String target) async {}
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
