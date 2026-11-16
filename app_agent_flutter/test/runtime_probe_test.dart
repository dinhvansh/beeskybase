import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:beesky_agent_app/agent_bridge.dart';

void main() {
  test(
      'runtime probe supports extensionless config and distinguishes unknown from stopped',
      () async {
    final directory = await Directory.systemTemp.createTemp('beesky-probe-');
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    var invalid = false;
    final token = List.filled(64, 'a')
        .join(); // local control fixture, never a Cloud token
    server.listen((request) {
      request.response.statusCode = invalid ? 403 : 200;
      request.response.write(
          jsonEncode({'pid': 123, 'instance': token, 'startedAt': 1000}));
      request.response.close();
    });
    final config = '${directory.path}/agent-config';
    final runtime = File('$config.runtime.json');
    await runtime.writeAsString(
        jsonEncode({'port': server.port, 'pid': 123, 'token': token}));
    final bridge = ProcessAgentBridge(agentExe: 'unused');
    try {
      expect(await bridge.refreshRunning(config), isTrue);
      expect(bridge.runtimeUncertain, isFalse);
      invalid = true;
      await bridge.refreshRunning(config);
      expect(bridge.runtimeUncertain, isTrue);
      invalid = false;
      expect(await bridge.refreshRunning(config), isTrue);
      expect(bridge.runtimeUncertain, isFalse);
      await server.close(force: true);
      await bridge.refreshRunning(config);
      expect(bridge.running && !bridge.runtimeUncertain, isFalse,
          reason: 'a closed control channel must never be confirmed healthy');
      await runtime.delete();
      expect(await bridge.refreshRunning(config), isFalse);
      expect(bridge.runtimeUncertain, isFalse);
    } finally {
      await server.close(force: true);
      expect(
          directory.absolute.path
              .startsWith(Directory.systemTemp.absolute.path),
          isTrue);
      await directory.delete(recursive: true);
    }
  });
}
