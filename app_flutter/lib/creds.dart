import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import 'theme.dart';

/// Saved miner-login credential sets (v0.23) — the HashCore-style
/// multi-credential model the owner asked for: a farm runs several
/// machine lines with different web logins, so the app keeps MANY
/// sets and the scanner tries them per miner in family order.
///
/// On-disk schema is EXACTLY the CLI's --creds-file schema (a bare
/// JSON list), so the app just hands the file path to the sidecar —
/// passwords never travel on a command line:
///
///   [{"label": "...", "user": "...", "password": "...",
///     "type": "any" | "stock" | "vnish" | "whatsminer" | "avalon" |
///      "iceriver" | "jasminer" | "braiins" | "luxos"}, ...]
///
/// "type" is the machine-family tag: the core tries sets tagged for
/// the detected family first, then "any", then the rest (a wrong tag
/// never locks a machine out). Missing/unknown tags read as "any".
///
/// A "vnish" set may carry an "api_key" instead of a login — the
/// VNish API-key unlock method (HashCore keys methods per vendor
/// the same way): the core then authenticates with the x-api-key
/// header and never attempts /unlock for that set.
class CredSet {
  String label;
  String user;
  String secret;
  String type; // a credTypeLabels key ('any' = every family)
  String apiKey;

  CredSet({
    this.label = '',
    this.user = '',
    this.secret = '',
    this.type = 'any',
    this.apiKey = '',
  });

  factory CredSet.fromJson(Map<String, dynamic> json) => CredSet(
        label: (json['label'] ?? '') as String,
        user: (json['user'] ?? '') as String,
        secret: (json['password'] ?? '') as String,
        type: credTypeLabels.containsKey(json['type'])
            ? json['type'] as String
            : 'any',
        apiKey: (json['api_key'] ?? '') as String,
      );

  Map<String, dynamic> toJson() => {
        'label': label,
        'user': user,
        'password': secret,
        'type': type,
        if (apiKey.isNotEmpty) 'api_key': apiKey,
      };

  CredSet copy() => CredSet(
        label: label,
        user: user,
        secret: secret,
        type: type,
        apiKey: apiKey,
      );
}

/// Type tag -> the label the creds dialog's dropdown shows.
/// The family set is HashCore's vendor universe as ported in
/// docs/vendor-coverage-mapping.md §6 (v0.30): detection exists
/// for whatsminer + avalon; iceriver / jasminer / braiins / luxos
/// are tag-only families until their contracts are evidenced.
const credTypeLabels = <String, String>{
  'any': 'Mọi loại máy',
  'stock': 'Antminer gốc',
  'vnish': 'VNish',
  'whatsminer': 'Whatsminer (MicroBT)',
  'avalon': 'Avalon (Canaan)',
  'iceriver': 'IceRiver',
  'jasminer': 'Jasminer (SunLune)',
  'braiins': 'Braiins OS',
  'luxos': 'LuxOS',
};

/// Persistence for the creds file.
///
/// Location (deterministic, documented in the app README): the file
/// `beesky-creds.json` NEXT TO the app executable — the shipped
/// bundle folder, beside beesky.exe. When that folder is not
/// writable (Program Files installs), saving falls back to
/// `%APPDATA%\BeeSky\beesky-creds.json` (or the system temp dir's
/// BeeSky folder elsewhere). Loading reads the primary file when it
/// exists, else the fallback, else starts empty.
class CredStore {
  final Directory primaryDir;
  final Directory fallbackDir;

  const CredStore({required this.primaryDir, required this.fallbackDir});

  factory CredStore.appDefault() {
    final exeDir = File(Platform.resolvedExecutable).parent;
    final appData = Platform.environment['APPDATA'];
    final fallback = (appData != null && appData.isNotEmpty)
        ? Directory('$appData${Platform.pathSeparator}BeeSky')
        : Directory(
            '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
    return CredStore(primaryDir: exeDir, fallbackDir: fallback);
  }

  static const fileName = 'beesky-creds.json';

  File get primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  /// (sets, source) — source is the file the sets were read from,
  /// or null when no file exists yet. A corrupt file reads as empty
  /// (the CLI validates loudly when IT is handed a bad file; the
  /// app must not brick on a settings file it can simply rewrite).
  Future<(List<CredSet>, File?)> load() async {
    // Sync IO internally (the async signature stays for callers):
    // the file is ~1 KB read once at startup, and sync calls
    // cannot be stranded half-done by an interrupted async chain.
    for (final file in [primaryFile, fallbackFile]) {
      try {
        if (!file.existsSync()) continue;
        final decoded = jsonDecode(file.readAsStringSync());
        if (decoded is List) {
          return (
            decoded
                .whereType<Map<String, dynamic>>()
                .map(CredSet.fromJson)
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
    return (<CredSet>[], null);
  }

  /// Writes the sets; returns the file actually written (the
  /// fallback when the bundle folder refuses the write).
  Future<File> save(List<CredSet> creds) async {
    // Sync writes, same reason as load(): a click saves ~1 KB, and
    // the file is either fully written or not there at all.
    final text = const JsonEncoder.withIndent('  ')
        .convert(creds.map((c) => c.toJson()).toList());
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

/// The editable list of credential-set rows — shared by the global
/// creds dialog below AND the network-group editor (v0.24: a group
/// carries its own sets in the same schema). One row per set:
/// label, user, password obscured, machine-type dropdown, delete,
/// plus an add button. The parent reads the result via
/// [CredSetsEditorState.collect] (fully-blank rows are dropped).
class CredSetsEditor extends StatefulWidget {
  final List<CredSet> initial;
  const CredSetsEditor({super.key, required this.initial});

  @override
  CredSetsEditorState createState() => CredSetsEditorState();
}

class _Row {
  final CredSet data;
  final TextEditingController label;
  final TextEditingController user;
  final TextEditingController secret;
  final TextEditingController apiKey;
  _Row(CredSet src)
      : data = src.copy(),
        label = TextEditingController(text: src.label),
        user = TextEditingController(text: src.user),
        secret = TextEditingController(text: src.secret),
        apiKey = TextEditingController(text: src.apiKey);

  void dispose() {
    label.dispose();
    user.dispose();
    secret.dispose();
    apiKey.dispose();
  }
}

class CredSetsEditorState extends State<CredSetsEditor> {
  late final List<_Row> _rows = [for (final c in widget.initial) _Row(c)];

  @override
  void dispose() {
    for (final r in _rows) {
      r.dispose();
    }
    super.dispose();
  }

  void _addRow() => setState(() => _rows.add(_Row(CredSet())));

  void _removeRow(int i) => setState(() {
        _rows[i].dispose();
        _rows.removeAt(i);
      });

  /// The edited sets; fully-blank rows are dropped (the save rule
  /// both dialogs share).
  List<CredSet> collect() => <CredSet>[
        for (final r in _rows)
          if (r.label.text.trim().isNotEmpty ||
              r.user.text.trim().isNotEmpty ||
              r.secret.text.isNotEmpty ||
              r.apiKey.text.trim().isNotEmpty)
            CredSet(
              label: r.label.text.trim(),
              user: r.user.text.trim(),
              secret: r.secret.text,
              type: r.data.type,
              apiKey: r.apiKey.text.trim(),
            ),
      ];

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < _rows.length; i++) _row(i),
        OutlinedButton.icon(
          onPressed: _addRow,
          icon: const Icon(Icons.add, size: 16),
          label: const Text('Thêm bộ'),
        ),
      ],
    );
  }

  Widget _row(int i) {
    const fieldPad = EdgeInsets.symmetric(horizontal: 10, vertical: 8);
    final r = _rows[i];
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: BeeSkyColors.ghostFill,
        border: Border.all(color: BeeSkyColors.glassBorder),
        borderRadius: BorderRadius.circular(radiusWidget),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextField(
                  controller: r.label,
                  decoration: InputDecoration(
                    hintText: 'Tên bộ (vd: VNish trại A)',
                    contentPadding: fieldPad,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 2,
                child: DropdownButtonFormField<String>(
                  initialValue: r.data.type,
                  // Fit the bounded flex width (the longest label,
                  // "Antminer gốc", plus icon would otherwise
                  // overflow the field).
                  isExpanded: true,
                  decoration: InputDecoration(contentPadding: fieldPad),
                  items: [
                    for (final e in credTypeLabels.entries)
                      DropdownMenuItem(value: e.key, child: Text(e.value)),
                  ],
                  onChanged: (v) =>
                      setState(() => r.data.type = v ?? 'any'),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline, size: 19),
                tooltip: 'Xóa bộ này',
                onPressed: () => _removeRow(i),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: r.user,
                  decoration: InputDecoration(
                    hintText: 'User',
                    contentPadding: fieldPad,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: r.secret,
                  obscureText: true,
                  decoration: InputDecoration(
                    hintText: 'Mật khẩu',
                    contentPadding: fieldPad,
                  ),
                ),
              ),
            ],
          ),
          // The API-key method exists only for VNish sets (the core
          // sends it as the x-api-key header instead of a login).
          if (r.data.type == 'vnish') ...[
            const SizedBox(height: 8),
            TextField(
              controller: r.apiKey,
              obscureText: true,
              decoration: InputDecoration(
                hintText: 'API key (không bắt buộc)',
                contentPadding: fieldPad,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// The credentials editor dialog: the shared [CredSetsEditor] in a
/// dialog with Save/Cancel. Returns the edited list on Save, null
/// on cancel.
Future<List<CredSet>?> showCredsDialog(
  BuildContext context,
  List<CredSet> initial,
) {
  return showDialog<List<CredSet>>(
    context: context,
    builder: (_) => _CredsDialog(initial: initial),
  );
}

class _CredsDialog extends StatefulWidget {
  final List<CredSet> initial;
  const _CredsDialog({required this.initial});

  @override
  State<_CredsDialog> createState() => _CredsDialogState();
}

class _CredsDialogState extends State<_CredsDialog> {
  final _editorKey = GlobalKey<CredSetsEditorState>();

  void _save() =>
      Navigator.of(context).pop(_editorKey.currentState?.collect());

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel,
      title: const Text('Tài khoản máy đào'),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Mỗi bộ là một tài khoản web của một dòng máy. Quét sẽ '
                'thử bộ gắn đúng loại máy trước, rồi "Mọi loại máy", '
                'rồi các bộ còn lại.',
                style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              CredSetsEditor(key: _editorKey, initial: widget.initial),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(onPressed: _save, child: const Text('Lưu')),
      ],
    );
  }
}
