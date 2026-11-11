import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:beesky_agent_app/agent_bridge.dart';
import 'package:beesky_agent_app/agent_config.dart';

void main() {
  group('AgentConfig parse (mirrors AgentConfig.from_dict)', () {
    test('tolerant: unknown keys ignored, scalars coerced', () {
      final cfg = AgentConfig.fromJson({
        'target': '192.168.1.0/24',
        'cloud_url': 'https://cloud.example.com',
        'key': 'k',
        'site': 'Xưởng 1',
        'interval': '45', // string coerced to float
        'workers': '16',
        'notify_config': 'not-a-dict', // dropped to null
        'auto_update': true,
        'something_new': {'x': 1}, // ignored
      });
      expect(cfg.interval, 45.0);
      expect(cfg.workers, 16);
      expect(cfg.notifyConfig, isNull);
      expect(cfg.autoUpdate, isTrue);
      expect(cfg.user, 'root'); // default kept
      expect(cfg.httpPort, 80);
    });

    test('zero / null numerics fall back to the CLI defaults', () {
      final cfg = AgentConfig.fromJson({'interval': 0, 'workers': null});
      expect(cfg.interval, 30.0);
      expect(cfg.workers, 64);
    });

    test('decode rejects a non-object document', () {
      expect(() => AgentConfig.decode('[1, 2]'), throwsFormatException);
      expect(() => AgentConfig.decode('{broken'), throwsFormatException);
    });
  });

  group('save / load round-trip through the mock store', () {
    test('form save keeps unedited fields and writes the core format', () {
      final store = MockConfigStore.demo();
      final loaded = store.load();
      expect(loaded.workers, 32); // the fixture's scan-side field
      // Simulate the page: disk config as base, five form fields on top.
      loaded.site = 'Xưởng 2';
      loaded.interval = 45;
      store.save(loaded);
      final raw = store.savedRaw!;
      expect(raw.endsWith('\n'), isTrue);
      final again = AgentConfig.decode(raw);
      expect(again.site, 'Xưởng 2');
      expect(again.interval, 45.0);
      expect(again.workers, 32); // carried through untouched
      expect(again.key, 'demo-agent-key');
      // Field order matches the core's dataclass order.
      final keys = (jsonDecode(raw) as Map<String, dynamic>).keys.toList();
      expect(keys.sublist(0, 7), [
        'target',
        'cloud_url',
        'key',
        'key_protected',
        'site',
        'interval',
        'notify_config',
      ]);
    });

    test('a typed key replaces a DPAPI blob (legacy plain form)', () {
      final store = MockConfigStore.protectedKey();
      final loaded = store.load();
      expect(loaded.hasProtectedKey, isTrue);
      loaded.key = 'new-key';
      loaded.keyProtected = '';
      store.save(loaded);
      final again = AgentConfig.decode(store.savedRaw!);
      expect(again.key, 'new-key');
      expect(again.keyProtected, '');
    });

    test('an untouched DPAPI blob survives a save verbatim', () {
      final store = MockConfigStore.protectedKey();
      final loaded = store.load();
      loaded.site = 'Trại Khác';
      store.save(loaded);
      final again = AgentConfig.decode(store.savedRaw!);
      expect(again.keyProtected, 'QUJDREVGRw==');
      expect(again.key, '');
      expect(again.site, 'Trại Khác');
    });
  });

  group('validation (mirrors missing_fields + the interval rules)', () {
    test('missing fields come in the core fix order', () {
      expect(AgentConfig().missingFields(),
          ['target', 'cloud_url', 'key', 'site']);
      final partial = AgentConfig(target: 'x', site: 'y');
      expect(partial.missingFields(), ['cloud_url', 'key']);
    });

    test('a DPAPI blob counts as a present key', () {
      final cfg = AgentConfig(
          target: 't', cloudUrl: 'u', site: 's', keyProtected: 'QUJD');
      expect(cfg.hasKey, isTrue);
      expect(cfg.missingFields(), isEmpty);
    });

    test('whitespace-only fields count as missing', () {
      final cfg = AgentConfig(target: '  ', cloudUrl: 'u', key: 'k', site: 's');
      expect(cfg.missingFields(), ['target']);
    });
  });

  group('status derivation (mirrors refresh_bg_status)', () {
    test('no status file -> dim placeholder', () {
      final view = deriveStatusView(null);
      expect(view.tone, 'dim');
      expect(view.pillText, 'Chưa có dữ liệu');
      expect(view.bodyText, contains('chưa chạy vòng nào'));
    });

    test('ok cycle -> green pill with counts', () {
      final view = deriveStatusView(const AgentStatus(
          time: '2026-11-11 07:45:00',
          ok: true,
          miners: 63,
          error: null,
          cloudUrl: 'https://cloud.example.com',
          site: 'Xưởng 1'));
      expect(view.tone, 'ok');
      expect(view.pillText, 'Đang chạy tốt');
      expect(
          view.bodyText,
          'Vòng gần nhất OK lúc 2026-11-11 07:45:00 — 63 máy · '
          'trại Xưởng 1 · cloud https://cloud.example.com');
    });

    test('failed cycle -> red pill with the error verbatim', () {
      final view = deriveStatusView(const AgentStatus(
          time: '2026-11-11 07:46:00',
          ok: false,
          miners: 0,
          error: 'cloud không nhận snapshot',
          cloudUrl: '',
          site: ''));
      expect(view.tone, 'bad');
      expect(view.pillText, 'Lỗi gần nhất');
      expect(view.bodyText,
          'Lỗi lúc 2026-11-11 07:46:00: cloud không nhận snapshot');
    });

    test('failed cycle without an error -> không rõ nguyên nhân', () {
      final view = deriveStatusView(const AgentStatus(
          time: 'T', ok: false, miners: 0, error: null, cloudUrl: '', site: ''));
      expect(view.bodyText, 'Lỗi lúc T: không rõ nguyên nhân');
    });
  });

  group('insecure cloud warning (mirrors insecure_cloud_warning)', () {
    test('http to a public host warns; https / local do not', () {
      expect(insecureCloudWarning('http://cloud.example.com'), isNotNull);
      expect(insecureCloudWarning('https://cloud.example.com'), isNull);
      expect(insecureCloudWarning('http://127.0.0.1:8788'), isNull);
      expect(insecureCloudWarning('http://localhost:8788'), isNull);
      expect(insecureCloudWarning(''), isNull);
    });
  });

  group('interval formatting (mirrors the Tk load)', () {
    test('integral renders bare, fractional renders raw', () {
      expect(formatInterval(30.0), '30');
      expect(formatInterval(45.5), '45.5');
    });
  });

  group('config path (mirrors default_config_path)', () {
    test('env override wins', () {
      expect(
          defaultConfigPath(
              env: {'BEESKY_AGENT_CONFIG': '/tmp/x.json'},
              isWindows: false),
          '/tmp/x.json');
    });

    test('windows uses APPDATA', () {
      final path = defaultConfigPath(
          env: {'APPDATA': r'C:\Users\a\AppData\Roaming'}, isWindows: true);
      expect(path, contains('BeeSky'));
      expect(path, endsWith('agent-config.json'));
    });

    test('posix falls back to ~/.beesky', () {
      final path =
          defaultConfigPath(env: {'HOME': '/home/a'}, isWindows: false);
      expect(path, '/home/a/.beesky/agent-config.json');
    });
  });
}
