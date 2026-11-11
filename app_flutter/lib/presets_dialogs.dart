import 'package:flutter/material.dart';

import 'grid.dart';
import 'models.dart';
import 'presets.dart';
import 'theme.dart';

/// Presets dialogs (v0.28) — the HashCore Toolkit's Presets
/// center ported per docs/presets-ipreport-mapping.md §1/§3:
/// ONE dialog, two tabs (Bộ lọc / Pools), managing both
/// preset kinds; the pool-preset editor (name, description,
/// 3 slot rows, the pattern help, a live worker Preview
/// against the first selected device); and the apply picker
/// the Operations bar opens. All state lives in the grid
/// config / home page; these widgets render working copies
/// and report mutations through callbacks.

/// The Presets center. Works on copies of both preset
/// lists; every mutation is reported through [onChanged]
/// with a config carrying the new lists (the home page
/// persists). Deletions ask first (HashCore's delete
/// prompts); duplicates append " (bản sao)".
class PresetsCenterDialog extends StatefulWidget {
  final GridConfig config;
  final void Function(GridConfig config) onChanged;

  /// The device the pool-preset editor previews against
  /// (the first selected miner — HashCore's first-device
  /// rule), or null when nothing is selected.
  final MinerRecord? previewRecord;

  const PresetsCenterDialog({
    super.key,
    required this.config,
    required this.onChanged,
    required this.previewRecord,
  });

  @override
  State<PresetsCenterDialog> createState() => _PresetsCenterDialogState();
}

class _PresetsCenterDialogState extends State<PresetsCenterDialog> {
  late List<FilterPreset> _filters = [
    for (final p in widget.config.filterPresets) p.copy(),
  ];
  late List<PoolPreset> _pools = [
    for (final p in widget.config.poolPresets) p.copy(),
  ];

  void _emit() {
    final cfg = GridConfig(
      columnOrder: widget.config.columnOrder,
      visibleColumns: widget.config.visibleColumns,
      viewType: widget.config.viewType,
      viewMode: widget.config.viewMode,
      overviewColor: widget.config.overviewColor,
      overviewSize: widget.config.overviewSize,
      sort: widget.config.sort,
      groupBy: widget.config.groupBy,
      filterPresets: _filters,
      poolPresets: _pools,
    );
    widget.onChanged(cfg);
  }

  Future<bool> _confirm(String title, String message) async {
    final sure = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: BeeSkyColors.panel2,
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Đồng ý'),
          ),
        ],
      ),
    );
    return sure ?? false;
  }

  Future<void> _editPoolPreset({PoolPreset? existing}) async {
    final result = await showPoolPresetEditorDialog(
      context,
      existing: existing,
      takenNames: [
        for (final p in _pools)
          if (existing == null || p.name != existing.name) p.name,
      ],
      previewRecord: widget.previewRecord,
    );
    if (result == null) return;
    setState(() {
      final i = _pools.indexWhere((p) => p.name == result.name);
      if (existing != null) {
        final j = _pools.indexWhere((p) => p.name == existing.name);
        if (j >= 0) _pools[j] = result;
      } else if (i >= 0) {
        _pools[i] = result; // same name replaces (asks via warning)
      } else {
        _pools.add(result);
      }
    });
    _emit();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Row(
        children: [
          Icon(Icons.bookmarks_outlined, size: 20),
          SizedBox(width: 8),
          Text('Trung tâm mẫu'),
        ],
      ),
      content: SizedBox(
        width: 620,
        height: 460,
        child: DefaultTabController(
          length: 2,
          child: Column(
            children: [
              const TabBar(
                tabs: [
                  Tab(text: 'Bộ lọc'),
                  Tab(text: 'Pools'),
                ],
              ),
              Expanded(
                child: TabBarView(
                  children: [
                    _filtersTab(),
                    _poolsTab(),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Đóng'),
        ),
      ],
    );
  }

  Widget _empty(String text) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: BeeSkyColors.muted),
          ),
        ),
      );

  Widget _filtersTab() {
    if (_filters.isEmpty) {
      return _empty(
        'Chưa có mẫu lọc nào.\n'
        'Tạo mẫu từ hộp thoại Bộ lọc của danh sách máy.',
      );
    }
    return ListView(
      children: [
        for (final p in _filters)
          ListTile(
            title: Text(p.name),
            subtitle: Text(
              '${p.filters.length} điều kiện'
              '${p.description.isNotEmpty ? ' • ${p.description}' : ''}',
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: const Icon(Icons.copy_outlined, size: 18),
                  tooltip: 'Nhân đôi',
                  onPressed: () {
                    setState(() => _filters.add(
                          FilterPreset(
                            name: '${p.name} (bản sao)',
                            description: p.description,
                            filters: p.filters.map((f) => f.copy()).toList(),
                          ),
                        ));
                    _emit();
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outline, size: 18),
                  tooltip: 'Xóa mẫu',
                  onPressed: () async {
                    if (!await _confirm(
                      'Xóa mẫu lọc?',
                      'Xóa mẫu lọc "${p.name}"?',
                    )) {
                      return;
                    }
                    setState(() =>
                        _filters.removeWhere((x) => x.name == p.name));
                    _emit();
                  },
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _poolsTab() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: Alignment.centerRight,
          child: FilledButton.icon(
            onPressed: () => _editPoolPreset(),
            icon: const Icon(Icons.add, size: 16),
            label: const Text('Mẫu pool mới'),
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: _pools.isEmpty
              ? _empty(
                  'Chưa có mẫu pool nào.\n'
                  'Tạo mẫu pool đầu tiên bằng nút phía trên.',
                )
              : ListView(
                  children: [
                    for (final p in _pools)
                      ListTile(
                        title: Text(p.name),
                        subtitle: Text(
                          '${p.activeSlots.length} pool • '
                          '${p.activeSlots.isEmpty ? '—' : p.activeSlots.first.url}'
                          '${p.description.isNotEmpty ? ' • ${p.description}' : ''}',
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit_outlined,
                                  size: 18),
                              tooltip: 'Sửa mẫu',
                              onPressed: () =>
                                  _editPoolPreset(existing: p),
                            ),
                            IconButton(
                              icon: const Icon(Icons.copy_outlined,
                                  size: 18),
                              tooltip: 'Nhân đôi',
                              onPressed: () {
                                setState(() => _pools.add(
                                      PoolPreset(
                                        name: '${p.name} (bản sao)',
                                        description: p.description,
                                        slots: p.slots
                                            .map((s) => s.copy())
                                            .toList(),
                                      ),
                                    ));
                                _emit();
                              },
                            ),
                            IconButton(
                              icon: const Icon(
                                  Icons.delete_outline, size: 18),
                              tooltip: 'Xóa mẫu',
                              onPressed: () async {
                                if (!await _confirm(
                                  'Xóa mẫu pool?',
                                  'Xóa mẫu pool "${p.name}"?',
                                )) {
                                  return;
                                }
                                setState(() => _pools.removeWhere(
                                    (x) => x.name == p.name));
                                _emit();
                              },
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

/// The pool-preset editor: name + optional description +
/// three slot rows (URL / Worker / Mật khẩu pool), the
/// pattern help (HashCore's "Show available patterns") and
/// a live Preview of every filled slot's worker expanded
/// against [previewRecord] (the first selected device).
/// Saving requires slot 1 filled (HashCore's preset-saving
/// rule); a name matching [takenNames] warns that saving
/// REPLACES that preset. Returns null on cancel.
Future<PoolPreset?> showPoolPresetEditorDialog(
  BuildContext context, {
  PoolPreset? existing,
  required List<String> takenNames,
  MinerRecord? previewRecord,
}) {
  return showDialog<PoolPreset>(
    context: context,
    builder: (_) => _PoolPresetEditorDialog(
      existing: existing,
      takenNames: takenNames,
      previewRecord: previewRecord,
    ),
  );
}

class _PoolPresetEditorDialog extends StatefulWidget {
  final PoolPreset? existing;
  final List<String> takenNames;
  final MinerRecord? previewRecord;
  const _PoolPresetEditorDialog({
    required this.existing,
    required this.takenNames,
    required this.previewRecord,
  });

  @override
  State<_PoolPresetEditorDialog> createState() =>
      _PoolPresetEditorDialogState();
}

class _SlotCtrls {
  final url = TextEditingController();
  final worker = TextEditingController();
  final password = TextEditingController();
  void dispose() {
    url.dispose();
    worker.dispose();
    password.dispose();
  }
}

class _PoolPresetEditorDialogState
    extends State<_PoolPresetEditorDialog> {
  late final _name =
      TextEditingController(text: widget.existing?.name ?? '');
  late final _description =
      TextEditingController(text: widget.existing?.description ?? '');
  late final List<_SlotCtrls> _slots = [
    for (var i = 0; i < 3; i++)
      _SlotCtrls()
        ..url.text = _slotAt(i)?.url ?? ''
        ..worker.text = _slotAt(i)?.worker ?? ''
        ..password.text = _slotAt(i)?.password ?? '',
  ];
  String? _error;

  PoolSlot? _slotAt(int i) {
    final slots = widget.existing?.slots ?? const [];
    return i < slots.length ? slots[i] : null;
  }

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    for (final s in _slots) {
      s.dispose();
    }
    super.dispose();
  }

  bool get _clash =>
      widget.takenNames.contains(_name.text.trim()) &&
      _name.text.trim() != (widget.existing?.name ?? '');

  /// The live preview line for slot [i]'s worker — expanded
  /// against the preview record, or the pattern failure
  /// verbatim (the same honesty the core runner applies).
  String? _preview(int i) {
    final worker = _slots[i].worker.text;
    final rec = widget.previewRecord;
    if (worker.isEmpty || rec == null) return null;
    try {
      final expanded = expandWorkerPattern(
        worker,
        PatternContext.ofRecord(rec, index: 0),
      );
      return 'Xem trước (${rec.ip}): $expanded';
    } on PatternException catch (e) {
      return 'Xem trước: ${e.message}';
    }
  }

  void _submit() {
    final name = _name.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Tên mẫu không được để trống.');
      return;
    }
    final slots = [
      for (final c in _slots)
        PoolSlot(
          url: c.url.text.trim(),
          worker: c.worker.text.trim(),
          password: c.password.text,
        ),
    ];
    final active = slots.where((s) => !s.isEmpty).toList();
    if (active.isEmpty || active.first.isEmpty) {
      setState(
        () => _error = 'Pool 1 phải có đủ URL và worker mới '
            'lưu được mẫu (quy tắc của bản gốc).',
      );
      return;
    }
    Navigator.of(context).pop(
      PoolPreset(
        name: name,
        description: _description.text.trim(),
        slots: active,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const pad = EdgeInsets.symmetric(horizontal: 10, vertical: 8);
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: Text(
        widget.existing == null
            ? 'Mẫu pool mới'
            : 'Sửa mẫu pool: ${widget.existing!.name}',
      ),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _name,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Tên mẫu',
                  contentPadding: pad,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _description,
                decoration: const InputDecoration(
                  labelText: 'Mô tả (tùy chọn)',
                  contentPadding: pad,
                ),
              ),
              if (_clash) ...[
                const SizedBox(height: 8),
                const Text(
                  'Đã có mẫu với tên này — Lưu sẽ thay thế mẫu đó.',
                  style: TextStyle(
                      color: BeeSkyColors.warn, fontSize: 12),
                ),
              ],
              for (var i = 0; i < 3; i++) ...[
                const SizedBox(height: 14),
                Text(
                  'Pool ${i + 1}${i == 0 ? ' (bắt buộc)' : ' (tùy chọn)'}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _slots[i].url,
                  decoration: const InputDecoration(
                    labelText: 'URL (stratum+tcp://…)',
                    contentPadding: pad,
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _slots[i].worker,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    labelText: 'Worker (hỗ trợ biến mẫu {…})',
                    contentPadding: pad,
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _slots[i].password,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Mật khẩu pool (tùy chọn)',
                    contentPadding: pad,
                  ),
                ),
                if (_preview(i) != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    _preview(i)!,
                    style: const TextStyle(
                      color: BeeSkyColors.muted,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ],
              const SizedBox(height: 14),
              ExpansionTile(
                title: const Text(
                  'Các biến mẫu cho Worker',
                  style: TextStyle(fontSize: 13),
                ),
                tilePadding: EdgeInsets.zero,
                childrenPadding: const EdgeInsets.only(bottom: 8),
                children: [
                  for (final (token, desc) in patternHelp)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 110,
                            child: Text(
                              token,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 12,
                                color: BeeSkyColors.accent,
                              ),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              desc,
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: const TextStyle(color: BeeSkyColors.bad),
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
        FilledButton(
          onPressed: _submit,
          child: const Text('Lưu mẫu'),
        ),
      ],
    );
  }
}

/// The apply picker: "Select pool preset to apply"
/// (HashCore's placeholder, verbatim concept) — a simple
/// list; tapping a preset returns it, cancel returns null.
Future<PoolPreset?> showPoolPresetPickerDialog(
  BuildContext context, {
  required List<PoolPreset> presets,
}) {
  return showDialog<PoolPreset>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Áp mẫu pool'),
      content: SizedBox(
        width: 440,
        child: ListView(
          shrinkWrap: true,
          children: [
            const Text(
              'Chọn mẫu pool để áp cho các máy đã chọn:',
              style: TextStyle(color: BeeSkyColors.muted),
            ),
            const SizedBox(height: 8),
            for (final p in presets)
              ListTile(
                title: Text(p.name),
                subtitle: Text(
                  '${p.activeSlots.length} pool • '
                  '${p.activeSlots.isEmpty ? '—' : p.activeSlots.first.url}',
                ),
                trailing: const Icon(Icons.chevron_right, size: 18),
                onTap: () => Navigator.of(ctx).pop(p),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(),
          child: const Text('Hủy'),
        ),
      ],
    ),
  );
}