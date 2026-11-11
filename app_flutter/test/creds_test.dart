import 'dart:convert';
import 'dart:io';

import 'package:beesky_app/creds.dart';
import 'package:beesky_app/sidecar.dart';
import 'package:flutter_test/flutter_test.dart';

/// v0.23: saved credential sets — the on-disk schema is the CLI's
/// --creds-file schema (a bare JSON list), the store persists next
/// to the executable with a fallback location, and the sidecar argv
/// references the file by path only (no credential values in argv).
void main() {
  group('CredSet JSON (the --creds-file schema)', () {
    test('round-trips label/user/password/type/api_key', () {
      final set = CredSet(
        label: 'VNish trại A',
        user: 'root',
        secret: 'pw-1',
        type: 'vnish',
        apiKey: 'key-9',
      );
      final back = CredSet.fromJson(set.toJson());
      expect(back.label, 'VNish trại A');
      expect(back.user, 'root');
      expect(back.secret, 'pw-1');
      expect(back.type, 'vnish');
      expect(back.apiKey, 'key-9');
    });

    test('api_key is omitted from JSON while empty', () {
      final set = CredSet(label: 'Kho', user: 'root', secret: 'root');
      expect(set.toJson().containsKey('api_key'), isFalse);
    });

    test('missing/unknown type reads as "any" (back-compat)', () {
      expect(CredSet.fromJson(const {'user': 'root'}).type, 'any');
      expect(
        CredSet.fromJson(const {'user': 'root', 'type': 'bogus'}).type,
        'any',
      );
      expect(
        CredSet.fromJson(const {'user': 'root', 'type': 'stock'}).type,
        'stock',
      );
    });
  });

  group('CredStore', () {
    late Directory tmp;
    late CredStore store;

    setUp(() async {
      tmp = await Directory.systemTemp.createTemp('beesky_creds_test');
      store = CredStore(
        primaryDir: Directory('${tmp.path}/app'),
        fallbackDir: Directory('${tmp.path}/fallback'),
      );
      await store.primaryDir.create(recursive: true);
    });

    tearDown(() async {
      if (await tmp.exists()) await tmp.delete(recursive: true);
    });

    test('missing file loads empty, with no source', () async {
      final (creds, source) = await store.load();
      expect(creds, isEmpty);
      expect(source, isNull);
    });

    test('save/load round-trip keeps every field, types included',
        () async {
      final sets = [
        CredSet(
          label: 'VNish trại A',
          user: 'root',
          secret: 'vnish-pw',
          type: 'vnish',
          apiKey: 'key-1',
        ),
        CredSet(label: 'Kho S19 gốc', user: 'root', secret: 'root',
            type: 'stock'),
        CredSet(label: 'Dự phòng', user: 'admin', secret: 'x',
            type: 'any'),
      ];
      final written = await store.save(sets);
      expect(written.path, store.primaryFile.path);
      // The file content is the bare-list --creds-file schema.
      final raw = jsonDecode(await written.readAsString()) as List;
      expect(raw, hasLength(3));
      expect((raw[0] as Map)['type'], 'vnish');
      expect((raw[0] as Map)['api_key'], 'key-1');

      final (loaded, source) = await store.load();
      expect(source?.path, written.path);
      expect(loaded.map((c) => c.label),
          ['VNish trại A', 'Kho S19 gốc', 'Dự phòng']);
      expect(loaded.map((c) => c.type), ['vnish', 'stock', 'any']);
      expect(loaded[0].apiKey, 'key-1');
      expect(loaded[1].secret, 'root');
    });

    test('an unwritable primary dir falls back, and load finds it',
        () async {
      // A regular FILE as a path component of the primary dir:
      // writes under it raise FileSystemException, exercising the
      // fallback path.
      final blocker = File('${tmp.path}/blocker');
      await blocker.writeAsString('not a dir');
      final blocked = CredStore(
        primaryDir: Directory('${blocker.path}/sub'),
        fallbackDir: Directory('${tmp.path}/fallback'),
      );
      final written = await blocked.save([CredSet(label: 'A')]);
      expect(written.path, blocked.fallbackFile.path);
      final (loaded, _) = await blocked.load();
      expect(loaded.single.label, 'A');
    });
  });

  group('sidecar argv contract', () {
    test('scan args: --creds-file only when a file is given', () {
      expect(
        SidecarBridge.scanArgs('192.168.2.0/24'),
        ['scan', '192.168.2.0/24', '--json'],
      );
      expect(
        SidecarBridge.scanArgs('192.168.2.0/24',
            credsFile: '/app/beesky-creds.json'),
        [
          'scan',
          '192.168.2.0/24',
          '--json',
          '--creds-file',
          '/app/beesky-creds.json',
        ],
      );
    });

    test('tickets args mirror the same creds handling', () {
      expect(
        SidecarBridge.ticketsArgs('t', '/app/tickets'),
        ['scan', 't', '--tickets', '/app/tickets'],
      );
      expect(
        SidecarBridge.ticketsArgs('t', '/app/tickets',
            credsFile: '/app/beesky-creds.json'),
        [
          'scan',
          't',
          '--tickets',
          '/app/tickets',
          '--creds-file',
          '/app/beesky-creds.json',
        ],
      );
    });
  });
}
