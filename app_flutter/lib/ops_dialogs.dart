import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'ops.dart';
import 'theme.dart';

/// Operations dialogs (v0.26, + v0.29 tail forms): the confirm
/// step (HashCore's "Confirm operation"), the payload forms
/// (switch-pool; throttle / API key / preset / password /
/// diagnostic-report from docs/vnish-ops-mapping.md §3), and the
/// task-history dialog (HashCore's Operations dialog — mapping
/// §4.8). All state lives in the home page / OpsHistoryStore;
/// these widgets only render and report.

String fmtOpsTime(DateTime t) =>
    '${t.hour.toString().padLeft(2, '0')}:'
    '${t.minute.toString().padLeft(2, '0')}:'
    '${t.second.toString().padLeft(2, '0')} '
    '${t.day}/${t.month}/${t.year}';

Color opsStatusColor(OpsStatus status) => switch (status) {
      OpsStatus.success => BeeSkyColors.ok,
      OpsStatus.hasErrors => BeeSkyColors.warn,
      OpsStatus.error => BeeSkyColors.bad,
      OpsStatus.cancelled => BeeSkyColors.muted,
      OpsStatus.running => BeeSkyColors.accent,
    };

/// "Confirm operation" — shown before a device-mutating task
/// (reboot / switch_pool). Lists every target so the operator
/// confirms the exact device set, HashCore-style.
Future<bool> showOpsConfirmDialog(
  BuildContext context,
  OpsTaskType type,
  List<String> targets,
) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: Text('Xác nhận thao tác — ${type.label}'),
      content: SizedBox(
        width: 420,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${type.label} trên ${targets.length} máy đã chọn:',
              style: const TextStyle(color: BeeSkyColors.muted),
            ),
            const SizedBox(height: 10),
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 220),
              child: ListView(
                shrinkWrap: true,
                children: [
                  for (final ip in targets)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text(ip,
                          style: const TextStyle(
                              fontFamily: 'monospace', fontSize: 13)),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(false),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(ctx).pop(true),
          child: Text('Chạy ${type.label}'),
        ),
      ],
    ),
  );
  return result ?? false;
}

/// The switch-pool payload form: activate an already-configured
/// slot, or write a new pool into a slot (the two documented dashd
/// mechanisms, core/actions.py). Returns the job payload, or null
/// when cancelled. The password field's value goes into the job
/// FILE (never argv) and the file is deleted when the run ends.
Future<Map<String, dynamic>?> showSwitchPoolDialog(
  BuildContext context,
) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => const _SwitchPoolDialog(),
  );
}

class _SwitchPoolDialog extends StatefulWidget {
  const _SwitchPoolDialog();

  @override
  State<_SwitchPoolDialog> createState() => _SwitchPoolDialogState();
}

class _SwitchPoolDialogState extends State<_SwitchPoolDialog> {
  bool _writeNew = false;
  final _slotCtrl = TextEditingController(text: '0');
  final _urlCtrl = TextEditingController();
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _slotCtrl.dispose();
    _urlCtrl.dispose();
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    final slot = int.tryParse(_slotCtrl.text.trim());
    if (slot == null || slot < 0) {
      setState(() => _error = 'Slot phải là số nguyên ≥ 0.');
      return;
    }
    if (!_writeNew) {
      Navigator.of(context).pop({'pool_id': slot});
      return;
    }
    final url = _urlCtrl.text.trim();
    final user = _userCtrl.text.trim();
    if (url.isEmpty || user.isEmpty) {
      setState(() => _error = 'Pool mới cần cả URL và worker.');
      return;
    }
    Navigator.of(context).pop({
      'pool_id': slot,
      'url': url,
      'user': user,
      if (_passCtrl.text.isNotEmpty) 'password': _passCtrl.text,
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Đổi pool (VNish/dashd)'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Chỉ máy VNish/dashd đổi pool được — máy khác sẽ báo '
              'không hỗ trợ, không giả vờ thành công.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const SizedBox(width: 110, child: Text('Slot pool')),
                Expanded(
                  child: TextField(
                    controller: _slotCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      hintText: '0',
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            CheckboxListTile(
              value: _writeNew,
              onChanged: (v) => setState(() => _writeNew = v ?? false),
              title: const Text('Ghi pool mới vào slot này'),
              subtitle: const Text(
                'Đọc cấu hình hiện tại cần API key (theo api-doc '
                'của firmware).',
                style: TextStyle(fontSize: 12),
              ),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
            ),
            if (_writeNew) ...[
              TextField(
                controller: _urlCtrl,
                decoration: const InputDecoration(
                  labelText: 'URL (stratum+tcp://…)',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _userCtrl,
                decoration: const InputDecoration(
                  labelText: 'Worker',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _passCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Mật khẩu pool (tùy chọn)',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: BeeSkyColors.bad)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: _submit,
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The throttle form — HashCore's Throttle dialog ported
/// (vnish-ops-mapping §2.6): "Power level", the AVAILABLE RANGE
/// 20–100% (the api-doc's own ThrottleSettings bounds), the
/// RESET TO DEFAULT 100% affordance, and its how-it-works line.
/// Returns {'percent': N} or null when cancelled.
Future<Map<String, dynamic>?> showThrottleDialog(BuildContext context) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => const _ThrottleDialog(),
  );
}

class _ThrottleDialog extends StatefulWidget {
  const _ThrottleDialog();

  @override
  State<_ThrottleDialog> createState() => _ThrottleDialogState();
}

class _ThrottleDialogState extends State<_ThrottleDialog> {
  double _percent = 100;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Giảm công suất (VNish/dashd)'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Chỉ máy VNish/dashd nhận lệnh này — máy khác sẽ báo '
              'không hỗ trợ, không giả vờ thành công.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                const Text('Mức công suất'),
                const Spacer(),
                Text(
                  '${_percent.round()}%',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            Slider(
              value: _percent,
              min: 20,
              max: 100,
              divisions: 80,
              label: '${_percent.round()}%',
              onChanged: (v) => setState(() => _percent = v),
            ),
            Row(
              children: [
                const Text(
                  'Phạm vi cho phép: 20–100%',
                  style: TextStyle(
                      color: BeeSkyColors.muted, fontSize: 12),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => setState(() => _percent = 100),
                  child: const Text('Đặt lại mặc định: 100%'),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Cách hoạt động: giảm tần số mọi chip theo tỉ lệ — '
              'giảm điện năng tiêu thụ trong khi vẫn giữ nhiệt '
              'lượng tỏa ra.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context)
              .pop({'percent': _percent.round()}),
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The API-key configuration form — HashCore's edit_api_key
/// dialog (operation Add/Remove, key + description fields;
/// vnish-ops-mapping §2.10). The key must be exactly 32
/// characters (the api-doc's schema), checked here AND in the
/// core. Returns the job payload or null when cancelled.
Future<Map<String, dynamic>?> showApiKeyConfigDialog(
  BuildContext context,
) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => const _ApiKeyConfigDialog(),
  );
}

class _ApiKeyConfigDialog extends StatefulWidget {
  const _ApiKeyConfigDialog();

  @override
  State<_ApiKeyConfigDialog> createState() => _ApiKeyConfigDialogState();
}

class _ApiKeyConfigDialogState extends State<_ApiKeyConfigDialog> {
  String _operation = 'add';
  final _keyCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _keyCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    final key = _keyCtrl.text.trim();
    if (key.length != 32) {
      setState(() => _error =
          'API key phải đúng 32 ký tự (theo api-doc của firmware).');
      return;
    }
    Navigator.of(context).pop({
      'operation': _operation,
      'key': key,
      if (_operation == 'add' && _descCtrl.text.trim().isNotEmpty)
        'description': _descCtrl.text.trim(),
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Cấu hình API key (VNish/dashd)'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SizedBox(width: 110, child: Text('Thao tác')),
                Expanded(
                  child: DropdownButton<String>(
                    value: _operation,
                    isExpanded: true,
                    items: const [
                      DropdownMenuItem(
                          value: 'add', child: Text('Thêm API key')),
                      DropdownMenuItem(
                          value: 'remove', child: Text('Xóa API key')),
                    ],
                    onChanged: (v) =>
                        setState(() => _operation = v ?? 'add'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _keyCtrl,
              decoration: const InputDecoration(
                labelText: 'API key (32 ký tự)',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            if (_operation == 'add') ...[
              const SizedBox(height: 8),
              TextField(
                controller: _descCtrl,
                decoration: const InputDecoration(
                  labelText: 'Mô tả (tùy chọn)',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: BeeSkyColors.bad)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: _submit,
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The set-preset form: one profile name (the device's own
/// GET /autotune/presets universe names it; free text here — a
/// name the device does not know is refused by the device and
/// reported per device, like every other tail action).
Future<Map<String, dynamic>?> showSetPresetDialog(BuildContext context) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => const _SetPresetDialog(),
  );
}

class _SetPresetDialog extends StatefulWidget {
  const _SetPresetDialog();

  @override
  State<_SetPresetDialog> createState() => _SetPresetDialogState();
}

class _SetPresetDialogState extends State<_SetPresetDialog> {
  final _nameCtrl = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Cần tên preset.');
      return;
    }
    Navigator.of(context).pop({'preset': name});
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Đặt preset (VNish/dashd)'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ghi qua /settings (đọc cấu hình cần API key, theo '
              'api-doc). Tên preset do máy quyết định — tên sai '
              'sẽ bị máy từ chối và báo theo từng máy.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Tên preset (ví dụ: perf-110)',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: BeeSkyColors.bad)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: _submit,
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The device-password form: the NEW password, twice. The
/// current password never appears here — the core takes it from
/// the winning credential set (vnish-ops-mapping §2.11); a win
/// that cannot produce it (API key only) fails honestly per
/// device. The new password rides the job FILE, never argv.
Future<Map<String, dynamic>?> showChangePasswordDialog(
  BuildContext context,
) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => const _ChangePasswordDialog(),
  );
}

class _ChangePasswordDialog extends StatefulWidget {
  const _ChangePasswordDialog();

  @override
  State<_ChangePasswordDialog> createState() =>
      _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends State<_ChangePasswordDialog> {
  final _pwCtrl = TextEditingController();
  final _pw2Ctrl = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _pwCtrl.dispose();
    _pw2Ctrl.dispose();
    super.dispose();
  }

  void _submit() {
    if (_pwCtrl.text.isEmpty) {
      setState(() => _error = 'Mật khẩu mới không được trống.');
      return;
    }
    if (_pwCtrl.text != _pw2Ctrl.text) {
      setState(() => _error = 'Hai lần nhập chưa khớp nhau.');
      return;
    }
    Navigator.of(context).pop({'new_password': _pwCtrl.text});
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Đổi mật khẩu máy (VNish/dashd)'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Đổi mật khẩu đăng nhập web của máy. Sau khi đổi, '
              'hãy cập nhật bộ tài khoản đã lưu — bộ cũ sẽ không '
              'vào được nữa. Máy thắng bằng API key (không có mật '
              'khẩu hiện tại) sẽ báo lỗi rõ ràng.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _pwCtrl,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Mật khẩu mới',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _pw2Ctrl,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Nhập lại mật khẩu mới',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: BeeSkyColors.bad)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: _submit,
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The diagnostic-report form — HashCore's export shape
/// (reports directory + optional reason; vnish-ops-mapping
/// §2.12) over a BeeSky-VARIANT bundle: one JSON per device
/// (health record + inspect document) written by the core into
/// the chosen directory. The directory is pre-filled with the
/// app's export folder and stays editable (no file-picker
/// plugin in this zero-dependency app).
Future<Map<String, dynamic>?> showDiagnosticReportDialog(
  BuildContext context, {
  required String defaultDir,
}) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => _DiagnosticReportDialog(defaultDir: defaultDir),
  );
}

class _DiagnosticReportDialog extends StatefulWidget {
  final String defaultDir;
  const _DiagnosticReportDialog({required this.defaultDir});

  @override
  State<_DiagnosticReportDialog> createState() =>
      _DiagnosticReportDialogState();
}

class _DiagnosticReportDialogState
    extends State<_DiagnosticReportDialog> {
  late final _dirCtrl = TextEditingController(text: widget.defaultDir);
  final _reasonCtrl = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _dirCtrl.dispose();
    _reasonCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    final dir = _dirCtrl.text.trim();
    if (dir.isEmpty) {
      setState(() => _error = 'Cần thư mục lưu báo cáo.');
      return;
    }
    Navigator.of(context).pop({
      'report_dir': dir,
      if (_reasonCtrl.text.trim().isNotEmpty)
        'reason': _reasonCtrl.text.trim(),
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: const Text('Báo cáo chẩn đoán'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Mỗi máy một file JSON (bản ghi sức khỏe + dữ liệu '
              'inspect) ghi vào thư mục dưới đây.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _dirCtrl,
              decoration: const InputDecoration(
                labelText: 'Thư mục lưu báo cáo',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _reasonCtrl,
              decoration: const InputDecoration(
                labelText: 'Lý do (tùy chọn)',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: BeeSkyColors.bad)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: _submit,
          child: const Text('Tiếp tục'),
        ),
      ],
    );
  }
}

/// The Operations history dialog: every recorded task, newest
/// first — per-item info line, expandable per-device results, and
/// HashCore's item actions (isolate devices with errors, copy
/// task info, delete entry) plus the header clear-all. The dialog
/// owns a working copy of the list (deletions render immediately)
/// and reports every mutation through the callbacks; the home
/// page persists.
class OpsHistoryDialog extends StatefulWidget {
  final List<OpsTask> tasks;
  final void Function(OpsTask task) onDelete;
  final VoidCallback onClearAll;
  final void Function(List<String> ips) onIsolateErrors;

  const OpsHistoryDialog({
    super.key,
    required this.tasks,
    required this.onDelete,
    required this.onClearAll,
    required this.onIsolateErrors,
  });

  @override
  State<OpsHistoryDialog> createState() => _OpsHistoryDialogState();
}

class _OpsHistoryDialogState extends State<OpsHistoryDialog> {
  late List<OpsTask> tasks = [...widget.tasks];

  void _delete(OpsTask task) {
    setState(() => tasks = [for (final t in tasks) if (t.id != task.id) t]);
    widget.onDelete(task);
  }

  void _clearAll() {
    setState(() => tasks = const []);
    widget.onClearAll();
  }

  void _isolate(List<String> ips) {
    Navigator.of(context).pop();
    widget.onIsolateErrors(ips);
  }

  @override
  Widget build(BuildContext context) {
    final ordered = tasks.reversed.toList();
    return AlertDialog(
      backgroundColor: BeeSkyColors.panel2,
      title: Row(
        children: [
          const Icon(Icons.history, size: 20),
          const SizedBox(width: 8),
          const Text('Lịch sử tác vụ'),
          const Spacer(),
          Text(
            '${tasks.length} thao tác',
            style: const TextStyle(
                color: BeeSkyColors.muted,
                fontSize: 13,
                fontWeight: FontWeight.w400),
          ),
        ],
      ),
      content: SizedBox(
        width: 640,
        height: 480,
        child: tasks.isEmpty
            ? const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'Lịch sử tác vụ đang trống.\n'
                    'Chạy một lệnh từ thanh thao tác của danh sách '
                    'máy để thêm một mục vào đây.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: BeeSkyColors.muted),
                  ),
                ),
              )
            : ListView(
                children: [
                  for (final task in ordered)
                    _OpsHistoryItem(
                      task: task,
                      onDelete: () => _delete(task),
                      onIsolateErrors: _isolate,
                    ),
                ],
              ),
      ),
      actions: [
        if (tasks.isNotEmpty)
          TextButton(
            onPressed: () async {
              final sure = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: BeeSkyColors.panel2,
                  title: const Text('Chắc chắn?'),
                  content: const Text(
                      'Xóa toàn bộ lịch sử tác vụ? Việc này không '
                      'hoàn tác được.'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(false),
                      child: const Text('Hủy'),
                    ),
                    FilledButton(
                      onPressed: () => Navigator.of(ctx).pop(true),
                      child: const Text('Xóa hết'),
                    ),
                  ],
                ),
              );
              if (sure == true) _clearAll();
            },
            child: const Text('Xóa hết lịch sử'),
          ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Đóng'),
        ),
      ],
    );
  }
}

class _OpsHistoryItem extends StatelessWidget {
  final OpsTask task;
  final VoidCallback onDelete;
  final void Function(List<String> ips) onIsolateErrors;

  const _OpsHistoryItem({
    required this.task,
    required this.onDelete,
    required this.onIsolateErrors,
  });

  @override
  Widget build(BuildContext context) {
    // An entry still marked running when the dialog opens means
    // the app closed mid-run — HashCore's "Not completed".
    final interrupted =
        task.status == OpsStatus.running && task.finishedAt == null;
    final statusLabel =
        interrupted ? 'Chưa hoàn tất' : task.status.label;
    final d = task.duration;
    final durText = d == null
        ? ''
        : ' / Thời lượng: ${d.inMinutes >= 1 ? '${d.inMinutes} phút, ${d.inSeconds % 60} giây' : '${d.inSeconds} giây'}';
    return Card(
      color: BeeSkyColors.ghostFill,
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ExpansionTile(
        leading: Icon(task.type.icon, size: 20),
        title: Text(
          '${task.type.label} — $statusLabel',
          style: const TextStyle(fontSize: 13.5),
        ),
        subtitle: Text(
          '${fmtOpsTime(task.createdAt)} · '
          'Máy: ${task.total} / Đã xong: ${task.completed} / '
          'Lỗi: ${task.failCount}'
          '${task.cancelledCount > 0 ? ' / Đã hủy: ${task.cancelledCount}' : ''}'
          '$durText',
          style:
              const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ),
        trailing: Icon(
          task.status == OpsStatus.success
              ? Icons.check_circle_outline
              : task.status == OpsStatus.hasErrors ||
                      task.status == OpsStatus.error
                  ? Icons.error_outline
                  : Icons.schedule,
          color: opsStatusColor(
              interrupted ? OpsStatus.cancelled : task.status),
          size: 20,
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.infoText(),
                  style: const TextStyle(
                      color: BeeSkyColors.muted, fontSize: 12),
                ),
                const SizedBox(height: 8),
                if (task.results.isEmpty)
                  const Text(
                    'Không có chi tiết.',
                    style: TextStyle(
                        color: BeeSkyColors.muted, fontSize: 12),
                  ),
                for (final r in task.results)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          r.cancelled
                              ? Icons.block_outlined
                              : r.ok
                                  ? Icons.check_circle_outline
                                  : Icons.cancel_outlined,
                          size: 15,
                          color: r.cancelled
                              ? BeeSkyColors.muted
                              : r.ok
                                  ? BeeSkyColors.ok
                                  : BeeSkyColors.bad,
                        ),
                        const SizedBox(width: 8),
                        SizedBox(
                          width: 130,
                          child: Text(r.ip,
                              style: const TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: 12.5)),
                        ),
                        Expanded(
                          child: Text(r.message,
                              style: const TextStyle(fontSize: 12.5)),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  children: [
                    if (task.failCount > 0)
                      TextButton.icon(
                        onPressed: () => onIsolateErrors(task.results
                            .where((r) => !r.ok && !r.cancelled)
                            .map((r) => r.ip)
                            .toList()),
                        icon: const Icon(Icons.filter_alt_outlined,
                            size: 15),
                        label: const Text('Cô lập máy lỗi'),
                      ),
                    TextButton.icon(
                      onPressed: () async {
                        await Clipboard.setData(
                            ClipboardData(text: task.infoText()));
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Đã chép thông tin tác vụ')),
                          );
                        }
                      },
                      icon: const Icon(Icons.copy_outlined, size: 15),
                      label: const Text('Chép thông tin'),
                    ),
                    TextButton.icon(
                      onPressed: () async {
                        final sure = await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: BeeSkyColors.panel2,
                            title: const Text('Chắc chắn?'),
                            content: Text(
                                'Xóa tác vụ "${task.type.label}" khỏi '
                                'lịch sử?'),
                            actions: [
                              TextButton(
                                onPressed: () =>
                                    Navigator.of(ctx).pop(false),
                                child: const Text('Hủy'),
                              ),
                              FilledButton(
                                onPressed: () =>
                                    Navigator.of(ctx).pop(true),
                                child: const Text('Xóa'),
                              ),
                            ],
                          ),
                        );
                        if (sure == true) onDelete();
                      },
                      icon: const Icon(Icons.delete_outline, size: 15),
                      label: const Text('Xóa khỏi lịch sử'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
