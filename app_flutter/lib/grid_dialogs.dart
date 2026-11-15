import 'package:flutter/material.dart';

import 'grid.dart';
import 'theme.dart';

/// Dialogs for the data grid (v0.25): the columns configuration
/// ("Cột hiển thị" — HashCore's Columns / Columns order / Reset to
/// defaults) and the filter builder with its presets (HashCore's
/// Filter builder + "Save as preset"). Both work on COPIES and
/// commit on their save action, the house dialog pattern; null
/// means the user cancelled and nothing changed.

// --------------------------------------------------------------------
// Columns dialog
// --------------------------------------------------------------------

/// Edits a copy of [config]'s column order + Custom-mode
/// visibility; returns the updated config, or null on cancel.
Future<GridConfig?> showGridColumnsDialog(
  BuildContext context,
  GridConfig config,
) {
  return showDialog<GridConfig>(
    context: context,
    builder: (_) => _ColumnsDialog(config: config),
  );
}

class _ColumnsDialog extends StatefulWidget {
  final GridConfig config;
  const _ColumnsDialog({required this.config});

  @override
  State<_ColumnsDialog> createState() => _ColumnsDialogState();
}

class _ColumnsDialogState extends State<_ColumnsDialog> {
  late final List<String> _order = [...widget.config.columnOrder];
  late final Set<String> _visible = {...widget.config.visibleColumns};

  GridConfig _collect() {
    final cfg = widget.config;
    cfg.columnOrder = [..._order];
    cfg.visibleColumns = {..._visible};
    return cfg;
  }

  void _move(int index, int delta) {
    final j = index + delta;
    if (j < 0 || j >= _order.length) return;
    setState(() {
      final id = _order[index];
      _order[index] = _order[j];
      _order[j] = id;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel,
      title: const Text('Cột hiển thị'),
      content: SizedBox(
        width: 460,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Thứ tự và cột đang bật cho chế độ "Tùy chỉnh". '
              'Cột ghi "chưa có dữ liệu" là cột BeeSky chưa có '
              'nguồn dữ liệu — bật lên sẽ hiện "—".',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
            const SizedBox(height: 10),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _order.length,
                itemBuilder: (context, i) {
                  final def = gridColumnById(_order[i])!;
                  return Row(
                    children: [
                      Checkbox(
                        value: _visible.contains(def.id),
                        onChanged: (v) => setState(() {
                          if (v == true) {
                            _visible.add(def.id);
                          } else {
                            _visible.remove(def.id);
                          }
                        }),
                      ),
                      Expanded(
                        child: Text(
                          def.label,
                          style: const TextStyle(fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (def.dataGap)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: BeeSkyColors.entryFill,
                            borderRadius: BorderRadius.circular(radiusPill),
                          ),
                          child: const Text(
                            'CHƯA CÓ DỮ LIỆU',
                            style: TextStyle(
                              color: BeeSkyColors.muted,
                              fontSize: 9,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      IconButton(
                        icon: const Icon(Icons.arrow_upward, size: 17),
                        tooltip: 'Lên',
                        onPressed: i == 0 ? null : () => _move(i, -1),
                      ),
                      IconButton(
                        icon: const Icon(Icons.arrow_downward, size: 17),
                        tooltip: 'Xuống',
                        onPressed:
                            i == _order.length - 1 ? null : () => _move(i, 1),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => setState(() {
            _order
              ..clear()
              ..addAll(gridColumnUniverse.map((c) => c.id));
            _visible
              ..clear()
              ..addAll(gridDefaultVisible);
          }),
          child: const Text('Đặt lại mặc định'),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(_collect()),
          child: const Text('Lưu'),
        ),
      ],
    );
  }
}

// --------------------------------------------------------------------
// Filter dialog: builder rows + saved presets
// --------------------------------------------------------------------

/// The filter dialog's commit: the edited rows AND the (possibly
/// changed) preset list — presets live in the same grid config,
/// so both travel together.
class FilterDialogResult {
  final List<GridFilter> filters;
  final List<FilterPreset> presets;
  const FilterDialogResult(this.filters, this.presets);
}

/// Edits copies of the active [filters] and the saved [presets];
/// returns both on [Áp dụng], null on cancel.
Future<FilterDialogResult?> showGridFilterDialog(
  BuildContext context, {
  required List<GridFilter> filters,
  required List<FilterPreset> presets,
}) {
  return showDialog<FilterDialogResult>(
    context: context,
    builder: (_) => _FilterDialog(filters: filters, presets: presets),
  );
}

class _FilterRow {
  String field;
  FilterOp op;
  final TextEditingController value;
  final TextEditingController value2;
  _FilterRow(GridFilter f)
      : field = f.field,
        op = f.op,
        value = TextEditingController(text: f.value),
        value2 = TextEditingController(text: f.value2);

  GridFilter toFilter() =>
      GridFilter(field: field, op: op, value: value.text, value2: value2.text);

  void dispose() {
    value.dispose();
    value2.dispose();
  }
}

class _FilterDialog extends StatefulWidget {
  final List<GridFilter> filters;
  final List<FilterPreset> presets;
  const _FilterDialog({required this.filters, required this.presets});

  @override
  State<_FilterDialog> createState() => _FilterDialogState();
}

class _FilterDialogState extends State<_FilterDialog> {
  late final List<_FilterRow> _rows = [
    for (final f in widget.filters) _FilterRow(f.copy()),
  ];
  late final List<FilterPreset> _presets = [
    for (final p in widget.presets) p.copy(),
  ];
  final _presetName = TextEditingController();
  String? _error;

  @override
  void dispose() {
    for (final r in _rows) {
      r.dispose();
    }
    _presetName.dispose();
    super.dispose();
  }

  FilterFieldDef _defOf(_FilterRow row) =>
      filterFieldById(row.field) ?? gridFilterFields.first;

  void _addRow() {
    setState(() {
      final def = gridFilterFields[7]; // hashrate — the common case
      _rows.add(
        _FilterRow(
          GridFilter(field: def.id, op: filterOpsFor(def.kind).first),
        ),
      );
    });
  }

  void _savePreset() {
    final name = _presetName.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Đặt tên cho bộ lọc trước khi lưu.');
      return;
    }
    if (_rows.isEmpty) {
      setState(() => _error = 'Chưa có điều kiện nào để lưu.');
      return;
    }
    setState(() {
      _error = null;
      final preset = FilterPreset(
        name: name,
        filters: _rows.map((r) => r.toFilter()).toList(),
      );
      final i = _presets.indexWhere((p) => p.name == name);
      if (i >= 0) {
        _presets[i] = preset; // same name replaces (HashCore asks;
        // BeeSky states it — see docs/grid-mapping.md §6)
      } else {
        _presets.add(preset);
      }
      _presetName.clear();
    });
  }

  void _applyPreset(FilterPreset preset) {
    setState(() {
      for (final r in _rows) {
        r.dispose();
      }
      _rows
        ..clear()
        ..addAll(preset.filters.map((f) => _FilterRow(f.copy())));
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel,
      title: const Text('Bộ lọc'),
      content: SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Các điều kiện kết hợp theo VÀ (máy phải khớp mọi '
                'điều kiện).',
                style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
              const SizedBox(height: 10),
              if (_rows.isEmpty)
                const Text(
                  'Chưa có điều kiện nào.',
                  style: TextStyle(color: BeeSkyColors.muted, fontSize: 13),
                )
              else
                for (var i = 0; i < _rows.length; i++) _rowWidget(i),
              const SizedBox(height: 6),
              OutlinedButton.icon(
                onPressed: _addRow,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Thêm điều kiện'),
              ),
              const Divider(height: 26),
              const Text(
                'Bộ lọc đã lưu',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _presetName,
                      decoration: const InputDecoration(
                        hintText: 'Tên bộ lọc, ví dụ: Máy nóng',
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 9,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _savePreset,
                    child: const Text('Lưu bộ lọc'),
                  ),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: 6),
                Text(
                  _error!,
                  style: const TextStyle(
                    color: BeeSkyColors.bad,
                    fontSize: 12,
                  ),
                ),
              ],
              if (_presets.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text(
                    'Chưa có bộ lọc nào được lưu.',
                    style: TextStyle(
                      color: BeeSkyColors.muted,
                      fontSize: 12,
                    ),
                  ),
                )
              else
                for (final p in _presets)
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${p.name} (${p.filters.length} điều kiện)',
                          style: const TextStyle(fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      TextButton(
                        onPressed: () => _applyPreset(p),
                        child: const Text('Áp dụng'),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline, size: 18),
                        tooltip: 'Xóa bộ lọc',
                        onPressed: () => setState(() => _presets.remove(p)),
                      ),
                    ],
                  ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => setState(() {
            for (final r in _rows) {
              r.dispose();
            }
            _rows.clear();
          }),
          child: const Text('Xóa hết điều kiện'),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(
            FilterDialogResult(
              _rows.map((r) => r.toFilter()).toList(),
              _presets,
            ),
          ),
          child: const Text('Áp dụng'),
        ),
      ],
    );
  }

  Widget _rowWidget(int i) {
    final row = _rows[i];
    final def = _defOf(row);
    final ops = filterOpsFor(def.kind);
    if (!ops.contains(row.op)) row.op = ops.first;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 168,
            child: DropdownButton<String>(
              value: row.field,
              isExpanded: true,
              dropdownColor: BeeSkyColors.panel2,
              items: [
                for (final f in gridFilterFields)
                  DropdownMenuItem(
                    value: f.id,
                    child: Text(
                      f.label,
                      style: const TextStyle(fontSize: 12.5),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: (v) => setState(() {
                row.field = v!;
                row.op = filterOpsFor(_defOf(row).kind).first;
              }),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 128,
            child: DropdownButton<FilterOp>(
              value: row.op,
              isExpanded: true,
              dropdownColor: BeeSkyColors.panel2,
              items: [
                for (final op in ops)
                  DropdownMenuItem(
                    value: op,
                    child: Text(
                      op.label,
                      style: const TextStyle(fontSize: 12.5),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: (v) => setState(() => row.op = v!),
            ),
          ),
          const SizedBox(width: 8),
          if (def.kind == FilterFieldKind.bool)
            const Expanded(
              child: Text(
                '—',
                style: TextStyle(color: BeeSkyColors.muted),
              ),
            )
          else
            Expanded(
              child: TextField(
                controller: row.value,
                decoration: InputDecoration(
                  hintText: def.kind == FilterFieldKind.text &&
                          (row.op == FilterOp.anyOf || row.op == FilterOp.notIn)
                      ? 'cách nhau dấu phẩy'
                      : 'giá trị',
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                ),
              ),
            ),
          if (row.op == FilterOp.between) ...[
            const SizedBox(width: 6),
            const Text('đến', style: TextStyle(color: BeeSkyColors.muted)),
            const SizedBox(width: 6),
            SizedBox(
              width: 84,
              child: TextField(
                controller: row.value2,
                decoration: const InputDecoration(
                  hintText: 'đến',
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                ),
              ),
            ),
          ],
          IconButton(
            icon: const Icon(Icons.close, size: 18),
            tooltip: 'Xóa điều kiện',
            onPressed: () => setState(() {
              _rows[i].dispose();
              _rows.removeAt(i);
            }),
          ),
        ],
      ),
    );
  }
}
