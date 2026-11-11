import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/material.dart';

import 'creds.dart';
import 'theme.dart';

/// Network groups (v0.24) — the HashCore Toolkit's home-screen
/// concept, ported per docs/network-groups-mapping.md: a group is a
/// NAMED scan target with its own credential sets (the per-group
/// layer over the global v0.23 sets), an autoscan setting, and a
/// persisted last-scan summary.
///
/// On-disk schema is EXACTLY the core's store document
/// (beesky/core/groups.py), so the app and the CLI share one file:
///
///   {"version": 1, "groups": [
///     {"id": "…", "name": "…", "targets": "192.168.2.0/24",
///      "creds": [ …the --creds-file entry schema… ],
///      "autoscan": {"enabled": false, "interval_min": 30},
///      "last_scan": {"at": "…", "scanned": N, "found": N,
///                    "ok": N, "check": N, "error": N} | null} ]}
///
/// Group scans run through the sidecar as `scan --group <name>` —
/// the CORE resolves targets and merges group-then-global creds,
/// and persists last_scan into this same file.
class GroupLastScan {
  final String at; // ISO-8601, as the core wrote it
  final int scanned;
  final int found;
  final int ok;
  final int check;
  final int error;

  const GroupLastScan({
    required this.at,
    required this.scanned,
    required this.found,
    required this.ok,
    required this.check,
    required this.error,
  });

  factory GroupLastScan.fromJson(Map<String, dynamic> json) =>
      GroupLastScan(
        at: (json['at'] ?? '') as String,
        scanned: ((json['scanned'] as num?) ?? 0).toInt(),
        found: ((json['found'] as num?) ?? 0).toInt(),
        ok: ((json['ok'] as num?) ?? 0).toInt(),
        check: ((json['check'] as num?) ?? 0).toInt(),
        error: ((json['error'] as num?) ?? 0).toInt(),
      );

  Map<String, dynamic> toJson() => {
        'at': at,
        'scanned': scanned,
        'found': found,
        'ok': ok,
        'check': check,
        'error': error,
      };

  DateTime? get atTime => DateTime.tryParse(at);

  /// "Quét 09:41 11/11: 63 máy • OK 12 • Kiểm tra 51 • Lỗi 0" —
  /// the card's one-line summary of the last pass.
  String get summaryText {
    final t = atTime;
    final when = t == null
        ? at
        : '${t.hour.toString().padLeft(2, '0')}:'
            '${t.minute.toString().padLeft(2, '0')} '
            '${t.day.toString().padLeft(2, '0')}/'
            '${t.month.toString().padLeft(2, '0')}';
    return 'Quét $when: $found máy • OK $ok • '
        'Kiểm tra $check • Lỗi $error';
  }
}

class NetGroup {
  String id;
  String name;
  String targets;
  List<CredSet> creds;
  bool autoscanEnabled;
  int autoscanIntervalMin;
  GroupLastScan? lastScan;

  NetGroup({
    required this.id,
    required this.name,
    required this.targets,
    List<CredSet>? creds,
    this.autoscanEnabled = false,
    this.autoscanIntervalMin = 30,
    this.lastScan,
  }) : creds = creds ?? [];

  /// HashCore marks a group that has never been scanned with a
  /// "new" tag; BeeSky mirrors it (last_scan == null → MỚI).
  bool get isNew => lastScan == null;

  String get autoscanText => autoscanEnabled
      ? 'Tự quét: mỗi $autoscanIntervalMin phút'
      : 'Tự quét: tắt';

  factory NetGroup.fromJson(Map<String, dynamic> json) => NetGroup(
        id: (json['id'] ?? '') as String,
        name: (json['name'] ?? '') as String,
        targets: (json['targets'] ?? '') as String,
        creds: ((json['creds'] as List<dynamic>?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(CredSet.fromJson)
            .toList(),
        autoscanEnabled:
            ((json['autoscan'] as Map<String, dynamic>?)?['enabled']
                    as bool?) ??
                false,
        autoscanIntervalMin:
            (((json['autoscan'] as Map<String, dynamic>?)?['interval_min']
                        as num?) ??
                    30)
                .toInt(),
        lastScan: json['last_scan'] is Map<String, dynamic>
            ? GroupLastScan.fromJson(
                json['last_scan'] as Map<String, dynamic>)
            : null,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'targets': targets,
        'creds': creds.map((c) => c.toJson()).toList(),
        'autoscan': {
          'enabled': autoscanEnabled,
          'interval_min': autoscanIntervalMin,
        },
        'last_scan': lastScan?.toJson(),
      };

  NetGroup copy() => NetGroup(
        id: id,
        name: name,
        targets: targets,
        creds: creds.map((c) => c.copy()).toList(),
        autoscanEnabled: autoscanEnabled,
        autoscanIntervalMin: autoscanIntervalMin,
        lastScan: lastScan,
      );
}

String newGroupId() {
  final rnd = Random();
  return List.generate(
    12,
    (_) => rnd.nextInt(16).toRadixString(16),
  ).join();
}

/// The union of two target specs (v0.28 group merge): items
/// comma-joined, de-duplicated by item text, keep-order first.
String unionTargetSpecs(String a, String b) {
  final seen = <String>{};
  final out = <String>[];
  for (final part in [...a.split(','), ...b.split(',')]) {
    final item = part.trim();
    if (item.isNotEmpty && seen.add(item)) out.add(item);
  }
  return out.join(', ');
}

/// Merge group [other] INTO [keep] (v0.28 — HashCore's "Merge
/// network groups"; its internal semantics are UNKNOWN, so
/// these are BeeSky's, stated in docs/presets-ipreport-
/// mapping.md §6): keep's id/name/autoscan survive; targets
/// are the union; creds are keep's sets then other's sets not
/// already present (identity = label + user + type + apiKey);
/// lastScan is the NEWER of the two (the freshest summary of
/// the merged ranges), the existing one when only one side
/// was ever scanned, null only when neither was.
NetGroup mergeGroups(NetGroup keep, NetGroup other) {
  String credKey(CredSet c) =>
      '${c.label}|${c.user}|${c.type}|${c.apiKey}';
  final have = keep.creds.map(credKey).toSet();
  final creds = [
    ...keep.creds.map((c) => c.copy()),
    for (final c in other.creds)
      if (have.add(credKey(c))) c.copy(),
  ];
  GroupLastScan? lastScan;
  final a = keep.lastScan, b = other.lastScan;
  if (a != null && b != null) {
    final at = a.atTime, bt = b.atTime;
    lastScan = (at != null && bt != null && bt.isAfter(at)) ? b : a;
  } else {
    lastScan = a ?? b;
  }
  return NetGroup(
    id: keep.id,
    name: keep.name,
    targets: unionTargetSpecs(keep.targets, other.targets),
    creds: creds,
    autoscanEnabled: keep.autoscanEnabled,
    autoscanIntervalMin: keep.autoscanIntervalMin,
    lastScan: lastScan,
  );
}

/// Is an app-side autoscan pass due for [group]? (Pure, so the
/// timer wiring stays a one-liner and the rule is unit-testable.)
/// [lastRun] is when this app last scanned the group (or its
/// persisted last-scan time when the app has not run it yet).
bool autoscanDue(NetGroup group, DateTime? lastRun, DateTime now) {
  if (!group.autoscanEnabled || lastRun == null) return false;
  return now.difference(lastRun) >=
      Duration(minutes: group.autoscanIntervalMin);
}

/// Persistence for the groups file — the CredStore strategy
/// mirrored: `beesky-groups.json` NEXT TO the app executable, with
/// `%APPDATA%\BeeSky\` (or a system-temp BeeSky folder elsewhere)
/// as the fallback when the bundle folder refuses the write.
class GroupStore {
  final Directory primaryDir;
  final Directory fallbackDir;

  const GroupStore({required this.primaryDir, required this.fallbackDir});

  factory GroupStore.appDefault() {
    final exeDir = File(Platform.resolvedExecutable).parent;
    final appData = Platform.environment['APPDATA'];
    final fallback = (appData != null && appData.isNotEmpty)
        ? Directory('$appData${Platform.pathSeparator}BeeSky')
        : Directory(
            '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
    return GroupStore(primaryDir: exeDir, fallbackDir: fallback);
  }

  static const fileName = 'beesky-groups.json';

  File get primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  /// (groups, source) — source is the file the groups were read
  /// from, or null when no file exists yet. A corrupt file reads
  /// as empty (the CLI validates loudly when IT reads the store;
  /// the app must not brick on a settings file it can rewrite).
  Future<(List<NetGroup>, File?)> load() async {
    for (final file in [primaryFile, fallbackFile]) {
      try {
        if (!file.existsSync()) continue;
        final decoded = jsonDecode(file.readAsStringSync());
        final List<dynamic>? raw = decoded is List
            ? decoded
            : (decoded is Map<String, dynamic>
                ? decoded['groups'] as List<dynamic>?
                : null);
        if (raw != null) {
          return (
            raw
                .whereType<Map<String, dynamic>>()
                .map(NetGroup.fromJson)
                .toList(),
            file,
          );
        }
      } on FileSystemException {
        continue;
      } on FormatException {
        continue;
      }
    }
    return (<NetGroup>[], null);
  }

  /// Writes the versioned document; returns the file actually
  /// written (the fallback when the bundle folder refuses).
  Future<File> save(List<NetGroup> groups) async {
    final text = const JsonEncoder.withIndent('  ').convert({
      'version': 1,
      'groups': groups.map((g) => g.toJson()).toList(),
    });
    try {
      primaryFile.writeAsStringSync(text);
      return primaryFile;
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      fallbackFile.writeAsStringSync(text);
      return fallbackFile;
    }
  }
}

/// Demo groups for the MOCK shell only: the owner's farm shape —
/// the main hall already scanned once (counts matching the mock
/// fleet: 4 found, 1 OK, 2 CHECK, 1 ERROR), the second hall never
/// scanned (the MỚI tag shows). In-memory; persisted only if the
/// user edits and saves them.
List<NetGroup> demoGroups() => [
      NetGroup(
        id: 'demo-trang-chinh',
        name: 'Trại chính',
        targets: '192.168.2.0/24',
        creds: [
          CredSet(
            label: 'VNish trại A',
            user: 'root',
            secret: 'vnish-pw',
            type: 'vnish',
          ),
        ],
        autoscanEnabled: true,
        autoscanIntervalMin: 30,
        lastScan: const GroupLastScan(
          at: '2026-11-11T08:15:00+07:00',
          scanned: 254,
          found: 4,
          ok: 1,
          check: 2,
          error: 1,
        ),
      ),
      NetGroup(
        id: 'demo-kho-phu',
        name: 'Kho phụ',
        targets: '192.168.3.0/24',
      ),
    ];

/// The group editor dialog: name, targets, the autoscan toggle +
/// interval, and the group's own credential sets (the shared
/// [CredSetsEditor] — an empty list means "use the global sets").
/// Returns (edited group, scanAfter) on Save — scanAfter is the
/// v0.28 "Lưu & quét" submit (save, then enter + scan the group
/// immediately; a BeeSky UX addition, mapping §6) — or null on
/// cancel. Id and last_scan are preserved when editing. Empty
/// name/targets are refused with an inline error — the core
/// would reject them anyway.
Future<(NetGroup, bool)?> showGroupEditorDialog(
  BuildContext context, {
  NetGroup? existing,
}) {
  return showDialog<(NetGroup, bool)>(
    context: context,
    builder: (_) => _GroupEditorDialog(existing: existing),
  );
}

class _GroupEditorDialog extends StatefulWidget {
  final NetGroup? existing;
  const _GroupEditorDialog({required this.existing});

  @override
  State<_GroupEditorDialog> createState() => _GroupEditorDialogState();
}

class _GroupEditorDialogState extends State<_GroupEditorDialog> {
  late final TextEditingController _name =
      TextEditingController(text: widget.existing?.name ?? '');
  late final TextEditingController _targets =
      TextEditingController(text: widget.existing?.targets ?? '');
  late final TextEditingController _interval = TextEditingController(
    text: '${widget.existing?.autoscanIntervalMin ?? 30}',
  );
  late bool _autoscan = widget.existing?.autoscanEnabled ?? false;
  final _editorKey = GlobalKey<CredSetsEditorState>();
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _targets.dispose();
    _interval.dispose();
    super.dispose();
  }

  void _save({required bool scanAfter}) {
    final name = _name.text.trim();
    final targets = _targets.text.trim();
    if (name.isEmpty || targets.isEmpty) {
      setState(
        () => _error = 'Tên nhóm và dải quét không được để trống.',
      );
      return;
    }
    final interval = int.tryParse(_interval.text.trim());
    Navigator.of(context).pop((
      NetGroup(
        id: widget.existing?.id ?? newGroupId(),
        name: name,
        targets: targets,
        creds: _editorKey.currentState?.collect() ?? [],
        autoscanEnabled: _autoscan,
        autoscanIntervalMin:
            (interval == null || interval < 1) ? 30 : interval,
        lastScan: widget.existing?.lastScan,
      ),
      scanAfter,
    ));
  }

  @override
  Widget build(BuildContext context) {
    const fieldPad = EdgeInsets.symmetric(horizontal: 12, vertical: 10);
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel,
      title: Text(
        widget.existing == null ? 'Thêm nhóm mạng' : 'Sửa nhóm mạng',
      ),
      content: SizedBox(
        width: 600,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _name,
                decoration: const InputDecoration(
                  labelText: 'Tên nhóm',
                  hintText: 'vd: Trại chính',
                  contentPadding: fieldPad,
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _targets,
                decoration: const InputDecoration(
                  labelText: 'Dải quét',
                  hintText: '192.168.2.0/24, 192.168.3.10-192.168.3.60',
                  contentPadding: fieldPad,
                ),
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Switch(
                    value: _autoscan,
                    onChanged: (v) => setState(() => _autoscan = v),
                  ),
                  const Text('Tự quét khi app đang mở'),
                  const SizedBox(width: 12),
                  SizedBox(
                    width: 76,
                    child: TextField(
                      controller: _interval,
                      keyboardType: TextInputType.number,
                      enabled: _autoscan,
                      decoration: const InputDecoration(
                        labelText: 'Mỗi (phút)',
                        contentPadding: fieldPad,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Text(
                'Tài khoản riêng của nhóm (để trống = dùng tài khoản '
                'chung). Quét nhóm thử bộ của nhóm trước, rồi mới tới '
                'bộ chung.',
                style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
              const SizedBox(height: 8),
              CredSetsEditor(
                key: _editorKey,
                initial: widget.existing?.creds ?? const [],
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: const TextStyle(
                    color: BeeSkyColors.bad,
                    fontSize: 12,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        TextButton(
          onPressed: () => _save(scanAfter: false),
          child: const Text('Lưu'),
        ),
        FilledButton(
          onPressed: () => _save(scanAfter: true),
          child: const Text('Lưu & quét'),
        ),
      ],
    );
  }
}
