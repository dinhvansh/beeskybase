import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'agent_config.dart';
import 'agent_process.dart';
import 'theme.dart';

class AgentUpdateInfo {
  final bool ok, available, previousFailed;
  final String current, latest, message;
  final String? previousMessage;
  const AgentUpdateInfo(
      {required this.ok,
      required this.available,
      this.current = agentAppVersion,
      this.latest = '',
      required this.message,
      this.previousMessage,
      this.previousFailed = false});
  factory AgentUpdateInfo.fromJson(Map<String, dynamic> json) {
    final previous = json['previous'];
    return AgentUpdateInfo(
        ok: json['ok'] == true,
        available: json['available'] == true,
        current: json['current'] as String? ?? agentAppVersion,
        latest: json['latest'] as String? ?? '',
        message: json['message'] as String? ?? 'Chưa kiểm tra được bản mới.',
        previousMessage: previous is Map &&
                ['failed', 'complete'].contains(previous['phase'])
            ? previous['message'] as String?
            : null,
        previousFailed: previous is Map && previous['phase'] == 'failed');
  }
}

abstract class AgentUpdater {
  bool get isMock;
  Future<AgentUpdateInfo> check(String config);
  Future<bool> prepare(String config, void Function(double?, String) progress);
  Future<void> openLogs(String config) async {
    if (isMock) return;
    final directory = Directory(
        '${File(config).parent.path}${Platform.pathSeparator}agent-updates');
    if (!await directory.exists())
      throw const FormatException('Chưa có nhật ký cập nhật trên máy này.');
    await Process.start('explorer.exe', [directory.path],
        mode: ProcessStartMode.detached);
  }
}

class ProcessAgentUpdater extends AgentUpdater {
  final String executable;
  ProcessAgentUpdater(this.executable);
  @override
  bool get isMock => false;
  @override
  Future<AgentUpdateInfo> check(String config) async {
    final result = await runAgentProcess(
        executable, ['update-check', '--config', config],
        timeout: const Duration(seconds: 45));
    return AgentUpdateInfo.fromJson(
        jsonDecode((result.stdout as String).trim()) as Map<String, dynamic>);
  }

  @override
  Future<bool> prepare(
      String config, void Function(double?, String) progress) async {
    final process = await Process.start(
        executable, ['update-prepare', '--config', config, '--ui-pid', '$pid']);
    Map<String, dynamic>? result;
    final errors = process.stderr.drain<void>();
    final output = process.stdout
        .transform(const Utf8Decoder(allowMalformed: true))
        .transform(const LineSplitter())
        .forEach((line) {
      try {
        final data = jsonDecode(line) as Map<String, dynamic>;
        if (data.containsKey('ok')) {
          result = data;
        } else {
          final number = data['progress'];
          progress(number is num ? number.toDouble().clamp(0, 100) / 100 : null,
              data['message'] as String? ?? 'Đang tải bản mới…');
        }
      } on FormatException {
        /* Engine diagnostics are not user-facing progress. */
      }
    });
    try {
      await process.stdin.close();
      await process.exitCode.timeout(const Duration(minutes: 8));
      await output;
      await errors;
      if (result?['ok'] == true && result?['ready'] == true) return true;
      throw FormatException(result?['message'] as String? ??
          'Chưa chuẩn bị được bản cập nhật. Thử lại sau.');
    } finally {
      process.kill();
      await process.exitCode;
      await Future.wait([output, errors]);
    }
  }
}

class MockAgentUpdater extends AgentUpdater {
  @override
  bool get isMock => true;
  AgentUpdateInfo info = const AgentUpdateInfo(
      ok: true, available: false, message: 'Agent đang dùng bản mới nhất.');
  @override
  Future<AgentUpdateInfo> check(String config) async => info;
  @override
  Future<bool> prepare(
          String config, void Function(double?, String) progress) async =>
      true;
}

class AgentUpdatePanel extends StatefulWidget {
  final AgentUpdater updater;
  final String config;
  final bool enabled, unsavedChanges;
  final ValueChanged<bool> onBusy;
  final ValueChanged<AgentUpdateInfo> onInfo;
  final VoidCallback? onReady;
  final void Function(String, bool, double?)? onFeedback;
  const AgentUpdatePanel(
      {super.key,
      required this.updater,
      required this.config,
      required this.enabled,
      this.unsavedChanges = false,
      required this.onBusy,
      required this.onInfo,
      this.onReady,
      this.onFeedback});
  @override
  State<AgentUpdatePanel> createState() => AgentUpdatePanelState();
}

class AgentUpdatePanelState extends State<AgentUpdatePanel> {
  bool _checking = false, _preparing = false;
  AgentUpdateInfo? _info;
  String _message = 'Tự kiểm tra bản mới khi mở Agent.';
  double? _progress;
  bool _error = false;
  Timer? _nextCheck;
  @override
  void initState() {
    super.initState();
    _nextCheck = Timer(const Duration(seconds: 1), check);
  }

  @override
  void dispose() {
    _nextCheck?.cancel();
    super.dispose();
  }

  Future<void> check() async {
    if (_checking || _preparing) return;
    _nextCheck?.cancel();
    setState(() {
      _checking = true;
      _error = false;
    });
    try {
      final info = await widget.updater.check(widget.config);
      if (!mounted) return;
      setState(() {
        _info = info;
        _message = info.message;
        _error = !info.ok;
      });
      widget.onInfo(info);
    } catch (_) {
      if (mounted)
        setState(() {
          _error = true;
          _message = 'Chưa kiểm tra được bản mới. Kiểm tra mạng rồi thử lại.';
        });
    } finally {
      if (mounted) {
        setState(() => _checking = false);
        _nextCheck = Timer(
            _error ? const Duration(minutes: 15) : const Duration(hours: 6),
            check);
      }
    }
  }

  Future<void> requestUpdate() async {
    if (!widget.enabled || _preparing || _checking || _info?.available != true)
      return;
    final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
                title: Text('Cập nhật Agent ${_info!.latest}?'),
                content: Text(
                    'Agent sẽ tải bản mới, tạm dừng quét để cài đặt rồi tự mở lại. Token và cấu hình đã lưu được giữ nguyên.'
                    '${widget.unsavedChanges ? '\n\nCác thay đổi chưa lưu trên màn hình sẽ không được áp dụng.' : ''}'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Để sau')),
                  FilledButton(
                      onPressed: () => Navigator.pop(context, true),
                      child: const Text('Cập nhật'))
                ]));
    if (confirmed != true || !mounted) return;
    widget.onBusy(true);
    setState(() {
      _preparing = true;
      _error = false;
      _message = 'Đang chuẩn bị bản cập nhật…';
      _progress = null;
    });
    widget.onFeedback?.call(_message, false, null);
    try {
      final ready =
          await widget.updater.prepare(widget.config, (value, message) {
        if (mounted)
          setState(() {
            _progress = value;
            _message = message;
          });
        if (mounted) widget.onFeedback?.call(message, false, value);
      });
      if (!mounted) return;
      if (!ready)
        throw const FormatException(
            'Chưa chuẩn bị được bản cập nhật. Thử lại sau.');
      setState(() => _message = 'Đã tải xong. Agent sẽ cập nhật và mở lại.');
      if (widget.onReady != null) {
        widget.onReady!();
      } else if (!widget.updater.isMock) {
        exit(0);
      }
    } on FormatException catch (error) {
      if (mounted)
        setState(() {
          _error = true;
          _message = error.message;
        });
    } catch (_) {
      if (mounted)
        setState(() {
          _error = true;
          _message =
              'Chưa tải được bản cập nhật. Agent vẫn được giữ nguyên; kiểm tra mạng rồi thử lại.';
        });
    } finally {
      if (mounted) {
        widget.onFeedback?.call(_message, _error, _progress);
        widget.onBusy(false);
        setState(() => _preparing = false);
      }
    }
  }

  Future<void> _openLogs() async {
    try {
      await widget.updater.openLogs(widget.config);
    } catch (_) {
      if (mounted)
        setState(() {
          _error = true;
          _message = 'Chưa mở được thư mục nhật ký cập nhật. Thử lại sau.';
        });
    }
  }

  @override
  Widget build(BuildContext context) =>
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Divider(height: 24),
        const Text('Phiên bản & cập nhật',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Semantics(
            liveRegion: true,
            child: Text(_checking ? 'Đang kiểm tra bản mới…' : _message,
                style: TextStyle(
                    fontSize: 12,
                    height: 1.6,
                    color: _error ? BeeSkyColors.bad : BeeSkyColors.muted))),
        if (_info?.previousMessage != null)
          Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('Lần cập nhật trước: ${_info!.previousMessage!}',
                  style: TextStyle(
                      fontSize: 12,
                      color: _info!.previousFailed
                          ? BeeSkyColors.bad
                          : BeeSkyColors.ok))),
        if (_preparing)
          Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: LinearProgressIndicator(value: _progress)),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          if (_info?.previousFailed == true)
            TextButton.icon(
                onPressed: _preparing ? null : _openLogs,
                icon: const Icon(Icons.folder_open_outlined, size: 17),
                label: const Text('Nhật ký cập nhật')),
          OutlinedButton.icon(
              onPressed:
                  widget.enabled && !_checking && !_preparing ? check : null,
              icon: const Icon(Icons.refresh, size: 17),
              label: const Text('Kiểm tra bản mới')),
          if (_info?.available == true)
            FilledButton.icon(
                onPressed: widget.enabled && !_checking && !_preparing
                    ? requestUpdate
                    : null,
                icon: const Icon(Icons.system_update_alt, size: 17),
                label: const Text('Cập nhật ngay')),
        ]),
      ]);
}
