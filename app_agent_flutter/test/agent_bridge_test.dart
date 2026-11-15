import 'package:flutter_test/flutter_test.dart';

import 'package:beesky_agent_app/agent_bridge.dart';

/// The argv contracts with the core's `beesky-agent` verbs
/// (docs/agent-app-mapping.md §3). These lists are what actually
/// runs on a farm PC, so they are pinned exactly.
void main() {
  group('test verb argv (the overlay contract, D3)', () {
    test('full form -> config, positional target, overlay flags', () {
      expect(
        ProcessAgentBridge.testArgs(
          configPath: r'C:\Users\farm\AppData\Roaming\BeeSky\agent-config.json',
          target: '192.168.1.10-192.168.1.60',
          cloudUrl: 'https://cloud.example.com',
          key: 'secret-key',
          site: 'Xưởng 1',
          intervalRaw: '45',
        ),
        [
          'test',
          '--config',
          r'C:\Users\farm\AppData\Roaming\BeeSky\agent-config.json',
          '192.168.1.10-192.168.1.60',
          '--cloud',
          'https://cloud.example.com',
          '--key',
          'secret-key',
          '--site',
          'Xưởng 1',
          '--interval',
          '45',
        ],
      );
    });

    test('empty target omits the positional (nothing to override with)', () {
      final args = ProcessAgentBridge.testArgs(
        configPath: 'c.json',
        target: '',
        cloudUrl: 'https://cloud.example.com',
        key: 'k',
        site: 's',
        intervalRaw: '30',
      );
      expect(args, [
        'test',
        '--config',
        'c.json',
        '--cloud',
        'https://cloud.example.com',
        '--key',
        'k',
        '--site',
        's',
        '--interval',
        '30',
      ]);
    });

    test('protected key state omits --key (the core uses the stored key)',
        () {
      final args = ProcessAgentBridge.testArgs(
        configPath: 'c.json',
        target: 't',
        cloudUrl: 'u',
        key: null,
        site: 's',
        intervalRaw: '30',
      );
      expect(args.contains('--key'), isFalse);
    });

    test('a cleared key still passes --key "" (the Tk empty override)', () {
      final args = ProcessAgentBridge.testArgs(
        configPath: 'c.json',
        target: 't',
        cloudUrl: 'u',
        key: '',
        site: 's',
        intervalRaw: '30',
      );
      final i = args.indexOf('--key');
      expect(i, greaterThan(0));
      expect(args[i + 1], '');
    });
  });

  group('task verbs argv', () {
    test('install-task carries the config path (SYSTEM %APPDATA% fix)', () {
      expect(ProcessAgentBridge.installTaskArgs('/x/agent-config.json'),
          ['install-task', '--config', '/x/agent-config.json']);
    });

    test('remove-task is bare, like the Tk remove_task() call', () {
      expect(ProcessAgentBridge.removeTaskArgs(), ['remove-task']);
    });
  });
}
