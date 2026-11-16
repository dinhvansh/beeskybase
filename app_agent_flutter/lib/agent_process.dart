import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Drain both pipes while the process is running, and own its lifetime even on
/// timeout. Future.timeout alone does not stop a scan or task command.
Future<ProcessResult> runAgentProcess(String executable, List<String> args,
    {required Duration timeout, String? input}) async {
  final process = await Process.start(executable, args);
  final output =
      process.stdout.transform(const Utf8Decoder(allowMalformed: true)).join();
  final errors =
      process.stderr.transform(const Utf8Decoder(allowMalformed: true)).join();
  try {
    if (input != null) process.stdin.write(input);
    await process.stdin.close();
    final code = await process.exitCode.timeout(timeout);
    return ProcessResult(process.pid, code, await output, await errors);
  } finally {
    process.kill();
    await process.exitCode;
    await Future.wait([output, errors]);
  }
}
