import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'ops.dart';
import 'theme.dart';

/// Operations dialogs (v0.26): the confirm step (HashCore's
/// "Confirm operation"), the switch-pool payload form, and the
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
