import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:beesky_agent_app/agent_process.dart';

void main() {
  final python = Platform.isWindows ? 'python' : 'python3';
  test('a timed out scan process actually exits', () async {
    final directory =
        await Directory.systemTemp.createTemp('beesky-owned-process-');
    final pidFile = File('${directory.path}/pid');
    try {
      await expectLater(
          runAgentProcess(
              python,
              [
                '-c',
                'import os,sys,time;open(sys.argv[1],"w").write(str(os.getpid()));time.sleep(60)',
                pidFile.path
              ],
              timeout: const Duration(seconds: 2)),
          throwsA(isA<TimeoutException>()));
      final pid = int.parse(await pidFile.readAsString());
      expect(Process.killPid(pid), isFalse,
          reason: 'Timed-out engine must not be left running');
    } finally {
      await directory.delete(recursive: true);
    }
  });
  test('large output on both pipes drains and preserves Vietnamese', () async {
    final result = await runAgentProcess(
        python,
        [
          '-c',
          'import sys;sys.stdout.reconfigure(encoding="utf-8");sys.stderr.reconfigure(encoding="utf-8");print("Xưởng máy "+"x"*100000);print("Nhật ký "+"y"*100000,file=sys.stderr)'
        ],
        timeout: const Duration(seconds: 10));
    expect(result.exitCode, 0);
    expect(result.stdout, startsWith('Xưởng máy'));
    expect(result.stderr, startsWith('Nhật ký'));
  });
}
