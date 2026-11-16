import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';

import 'agent_bridge.dart';
import 'agent_config.dart';
import 'theme.dart';
import 'agent_updates.dart';

const String _protectedKeyHint =
    'Token đã được bảo vệ trên máy này — để trống để giữ nguyên, nhập mới để thay.';

String _stamp() {
  final now = DateTime.now();
  String two(int v) => v.toString().padLeft(2, '0');
  return '${two(now.hour)}:${two(now.minute)}:${two(now.second)}';
}

/// Standalone Agent setup and monitoring. The bridge owns process control;
/// the store preserves the Python engine's configuration format.
class AgentConfigPage extends StatefulWidget {
  final AgentBridge bridge;
  final AgentConfigStore store;
  final bool embedded;
  final AgentUpdater? updater;
  const AgentConfigPage({
    super.key,
    required this.bridge,
    required this.store,
    this.embedded = false,
    this.updater,
  });

  @override
  State<AgentConfigPage> createState() => _AgentConfigPageState();
}

class _AgentConfigPageState extends State<AgentConfigPage> {
  final _cloudCtrl = TextEditingController();
  final _keyCtrl = TextEditingController();
  final _siteCtrl = TextEditingController();
  final _targetCtrl = TextEditingController();
  final _intervalCtrl = TextEditingController(text: '30');

  bool _showKey = false;
  String? _connectionError;
  bool _refreshing = false, _changingRun = false;
  bool _changingAutostart = false;
  bool _updating = false;
  late final AgentUpdater _updater;
  final _updateKey = GlobalKey<AgentUpdatePanelState>();
  AgentUpdateInfo? _updateInfo;
  String? _updateMessage;
  bool _updateError = false;
  double? _updateProgress;
  String? _targetError, _intervalError;
  AgentStatus? _lastStatus;
  double _savedInterval = 30;
  bool get _busy =>
      _filling ||
      _checking ||
      _testing ||
      _changingRun ||
      _changingAutostart ||
      _updating;
  bool get _editable => !_busy && !bridge.running && !bridge.runtimeUncertain;
  bool _keyProtected = false;
  bool _testing = false;
  bool _checking = false, _filling = true;
  AgentConnection? _connection;
  String _statusLine = '';
  String _testPillTone = 'dim';
  String _testPillText = 'Chưa chạy thử';
  StatusView _statusView = deriveStatusView(null);
  bool _autostartAvailable = true;
  bool _autostartInstalled = false;
  String _autostartHint = '';
  Timer? _timer;

  AgentBridge get bridge => widget.bridge;
  AgentConfigStore get store => widget.store;

  @override
  void initState() {
    super.initState();
    _updater = widget.updater ??
        (bridge.isMock
            ? MockAgentUpdater()
            : ProcessAgentUpdater(bridge.agentExePath));
    _statusLine = 'Dán token từ Mine để kết nối xưởng.';
    _cloudCtrl.addListener(_connectionChanged);
    _keyCtrl.addListener(_connectionChanged);
    _init();
    // The Tk window polls the status file's mtime every 100 ms;
    // 2 s here (divergence D7 — status changes once per cycle).
    _timer = Timer.periodic(const Duration(seconds: 2), (_) async {
      await _refreshRuntime();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in [
      _cloudCtrl,
      _keyCtrl,
      _siteCtrl,
      _targetCtrl,
      _intervalCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _init() async {
    try {
      if (!store.exists()) {
        _cloudCtrl.text = 'https://mine.beeskybase.com';
        // First run: pre-fill the scan target with this machine's
        // own subnet, via the sidecar's sysinfo (D5).
        final target = await bridge.sysinfoDefaultTarget();
        if (!mounted) return;
        if (target != null && _targetCtrl.text.isEmpty) {
          setState(() => _targetCtrl.text = target);
        }
      } else {
        try {
          final cfg = store.load();
          _fillFields(cfg);
          _statusLine = 'Đã nạp cấu hình. Bắt đầu Agent để giám sát liên tục.';
        } catch (_) {
          _statusLine =
              'Không đọc được cấu hình đã lưu. Kiểm tra quyền truy cập rồi nhập lại token.';
          _connectionError = _statusLine;
        }
        if (mounted) setState(() {});
      }
      await bridge.refreshRunning(store.path);
      if (!mounted) return;
      _refreshStatusCard();
      if (bridge.running)
        _statusLine =
            'Agent đang chạy ngầm. Dừng Agent trước khi sửa cấu hình.';
      await _refreshAutostart();
    } catch (_) {
      if (mounted)
        setState(() => _statusLine =
            'Chưa nạp được trạng thái Agent. Kiểm tra cài đặt rồi mở lại.');
    } finally {
      if (mounted) setState(() => _filling = false);
    }
  }

  void _fillFields(AgentConfig cfg) {
    _cloudCtrl.text = cfg.cloudUrl == 'https://cloud.beeskybase.com'
        ? 'https://mine.beeskybase.com'
        : cfg.cloudUrl;
    _keyCtrl.text = cfg.key;
    _siteCtrl.text = cfg.site;
    _targetCtrl.text = cfg.target;
    _intervalCtrl.text = formatInterval(cfg.interval);
    _keyProtected = cfg.hasProtectedKey;
    _savedInterval = cfg.interval;
  }

  // -- config <-> fields (the Tk current_config) --------------------

  /// The disk config as base + the five form fields on top.
  /// Returns (config, null) or (null, error) — the error texts are
  /// the Tk ValueError texts verbatim.
  (AgentConfig?, String?) _currentConfig() {
    var base = AgentConfig();
    if (store.exists()) {
      try {
        base = store.load();
      } catch (_) {
        base = AgentConfig();
      }
    }
    base.target = _targetCtrl.text.trim();
    base.cloudUrl = _cloudCtrl.text.trim();
    base.site = _siteCtrl.text.trim();
    final typed = _keyCtrl.text.trim();
    if (typed.isNotEmpty) {
      base.key = typed;
      base.keyProtected = '';
    } else if (!base.hasProtectedKey) {
      // Field cleared (or never set): the form's empty key wins,
      // exactly like the Tk override. A stored DPAPI blob with an
      // untouched field is the branch above and survives (D2).
      base.key = '';
      base.keyProtected = '';
    }
    final raw = _intervalCtrl.text.trim();
    final parsed = double.tryParse(raw);
    if (parsed == null || !parsed.isFinite) {
      return (null, "chu kỳ quét '$raw' không phải số giây hợp lệ");
    }
    if (parsed <= 0) {
      return (null, 'chu kỳ quét phải lớn hơn 0 giây');
    }
    base.interval = parsed;
    return (base, null);
  }

  void _connectionChanged() {
    if (_filling || !mounted) return;
    setState(() {
      _connection = null;
      _connectionError = null;
      _siteCtrl.clear();
    });
  }

  Future<bool> _checkConnection() async {
    if (_checking) return false;
    final url = Uri.tryParse(_cloudCtrl.text.trim());
    final key = _keyCtrl.text.trim();
    if (url == null ||
        !url.hasAuthority ||
        !['https', 'http'].contains(url.scheme) ||
        url.userInfo.isNotEmpty ||
        url.hasQuery ||
        url.hasFragment) {
      setState(() => _connectionError = _statusLine =
          'Nhập địa chỉ Mine hợp lệ, ví dụ https://mine.beeskybase.com.');
      return false;
    }
    if (key.isEmpty && !_keyProtected) {
      setState(() => _connectionError =
          _statusLine = 'Dán token được tạo trong mục Agent trên Mine.');
      return false;
    }
    final cloud = _cloudCtrl.text, token = _keyCtrl.text;
    setState(() {
      _checking = true;
      _connectionError = null;
      _statusLine = 'Đang kiểm tra token với Mine…';
    });
    try {
      final connection = await bridge
          .connectionInfo(
            configPath: store.path,
            cloudUrl: _cloudCtrl.text.trim(),
            key: key.isEmpty && _keyProtected ? null : key,
          )
          .timeout(const Duration(seconds: 25));
      if (!mounted) return false;
      if (cloud != _cloudCtrl.text || token != _keyCtrl.text) {
        setState(() => _connectionError =
            'Token hoặc địa chỉ đã thay đổi. Bấm kiểm tra lại.');
        return false;
      }
      setState(() {
        _connection = connection;
        _siteCtrl.text = connection.siteName;
        _statusLine =
            'Đã xác nhận: ${connection.agentName} · ${connection.siteName} · ${connection.organizationName}';
      });
      return true;
    } on FormatException catch (e) {
      if (mounted)
        setState(() {
          _connection = null;
          _siteCtrl.clear();
          _connectionError = _statusLine = e.message.toString();
        });
      return false;
    } on TimeoutException {
      if (mounted)
        setState(() => _connectionError = _statusLine =
            'Cloud chưa phản hồi sau 25 giây. Kiểm tra mạng rồi thử lại.');
      return false;
    } catch (_) {
      if (mounted)
        setState(
          () => _connectionError = _statusLine =
              'Không kiểm tra được token. Kiểm tra kết nối rồi thử lại.',
        );
      return false;
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  Future<void> _toggleAgent() async {
    if (_busy) return;
    if (bridge.runtimeUncertain) {
      await _refreshRuntime();
      return;
    }
    setState(() => _changingRun = true);
    try {
      await bridge.refreshRunning(store.path);
      TaskOutcome outcome;
      if (bridge.runtimeUncertain) {
        if (mounted)
          setState(() {
            _refreshStatusCard();
            _statusLine =
                'Chưa xác nhận được tiến trình. Làm mới trạng thái trước khi thay đổi Agent.';
          });
        return;
      }
      if (bridge.running) {
        outcome = await bridge.stopAgent();
      } else {
        if (!_validateScan() ||
            !await _checkConnection() ||
            !mounted ||
            !_saveConfig()) return;
        outcome = await bridge.startAgent(store.path);
      }
      if (mounted) setState(() => _statusLine = outcome.message);
      await bridge.refreshRunning(store.path);
      if (mounted)
        setState(() {
          _refreshStatusCard();
        });
    } catch (_) {
      if (mounted)
        setState(() => _statusLine =
            'Không thay đổi được trạng thái Agent. Làm mới rồi thử lại.');
    } finally {
      if (mounted) setState(() => _changingRun = false);
    }
  }

  bool _saveConfig() {
    if (bridge.running || bridge.runtimeUncertain) {
      setState(() => _statusLine = 'Dừng Agent trước khi thay đổi cấu hình.');
      return false;
    }
    if (!_validateScan()) return false;
    final (cfg, error) = _currentConfig();
    if (error != null) {
      setState(() => _statusLine = 'Chưa lưu được: $error');
      return false;
    }
    final missing = cfg!.missingFields();
    if (missing.isNotEmpty) {
      const labels = {
        'target': 'dải IP',
        'cloud_url': 'địa chỉ Mine',
        'key': 'token',
        'site': 'xưởng đã xác nhận'
      };
      setState(
        () => _statusLine =
            'Chưa lưu được — còn thiếu: ${missing.map((name) => labels[name] ?? name).join(', ')}',
      );
      return false;
    }
    try {
      store.save(cfg);
    } catch (e) {
      setState(() => _statusLine = 'Chưa lưu được: $e');
      return false;
    }
    setState(() {
      _keyProtected = cfg.hasProtectedKey;
      _savedInterval = cfg.interval;
      _statusLine =
          'Đã lưu cấu hình (${_stamp()}). Bấm Bắt đầu Agent để chạy ngầm.';
    });
    return true;
  }

  // -- test cycle -----------------------------------------------------

  Future<void> _startTest() async {
    if (_busy || bridge.running || bridge.runtimeUncertain || !_validateScan())
      return;
    setState(() => _testing = true);
    try {
      if (!await _checkConnection() || !mounted) return;
      final (cfg, error) = _currentConfig();
      if (error != null) {
        setState(() {
          _statusLine = 'Chạy thử thất bại: $error';
          _testPillTone = 'bad';
          _testPillText = 'Chạy thử: FAIL';
        });
        return;
      }
      setState(() {
        _testing = true;
        _statusLine = 'Đang chạy thử — quét và đẩy lên cloud …';
        _testPillTone = 'warn';
        _testPillText = 'Đang chạy thử…';
      });
      final outcome = await bridge.testRun(
        configPath: store.path,
        target: cfg!.target,
        cloudUrl: cfg.cloudUrl,
        // A stored DPAPI key is used by the core itself (D3): no
        // --key flag. Any other state passes the form's key through
        // the core's own overlay flag.
        key: cfg.hasProtectedKey ? null : cfg.key,
        site: cfg.site,
        intervalRaw: _intervalCtrl.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _testing = false;
        _statusLine = outcome.display;
        _testPillTone = outcome.ok ? 'ok' : 'bad';
        _testPillText = outcome.ok ? 'Chạy thử: OK' : 'Chạy thử: FAIL';
        _refreshStatusCard();
      });
    } catch (_) {
      if (mounted)
        setState(() {
          _statusLine =
              'Chạy thử chưa hoàn tất. Kiểm tra mạng và nhật ký rồi thử lại.';
          _testPillTone = 'bad';
          _testPillText = 'Chạy thử: FAIL';
        });
    } finally {
      if (mounted) setState(() => _testing = false);
    }
  }

  // -- background status ----------------------------------------------

  void _refreshStatusCard() {
    _lastStatus = store.readStatus();
    _statusView = deriveStatusView(_lastStatus,
        running: bridge.running,
        now: DateTime.now(),
        startedAt: bridge.startedAt,
        interval: _savedInterval);
    if (bridge.runtimeUncertain)
      _statusView = const StatusView('warn', 'Chưa xác nhận trạng thái',
          'Tiến trình chưa phản hồi. Bấm Làm mới để kiểm tra; cấu hình đang được giữ nguyên.');
  }

  bool get _unsavedChanges {
    if (!store.exists()) return _keyCtrl.text.isNotEmpty;
    try {
      final cfg = store.load();
      final cloud = cfg.cloudUrl == 'https://cloud.beeskybase.com'
          ? 'https://mine.beeskybase.com'
          : cfg.cloudUrl;
      return _cloudCtrl.text.trim() != cloud ||
          _targetCtrl.text.trim() != cfg.target ||
          _intervalCtrl.text.trim() != formatInterval(cfg.interval) ||
          _keyCtrl.text.trim() != cfg.key;
    } catch (_) {
      return true;
    }
  }

  Future<void> _refreshRuntime() async {
    if (_refreshing || _changingRun || _filling) return;
    _refreshing = true;
    try {
      await bridge.refreshRunning(store.path);
      if (mounted) setState(_refreshStatusCard);
    } catch (_) {
      if (mounted)
        setState(() => _statusLine =
            'Chưa đọc được trạng thái Agent. Bấm Làm mới để thử lại.');
    } finally {
      _refreshing = false;
    }
  }

  bool _validateScan() {
    final interval = double.tryParse(_intervalCtrl.text.trim());
    setState(() {
      _targetError = validateScanTarget(_targetCtrl.text);
      _intervalError = interval == null || !interval.isFinite || interval <= 0
          ? 'Nhập số giây lớn hơn 0.'
          : null;
      if (_targetError != null || _intervalError != null) {
        _statusLine = _targetError ?? _intervalError!;
      }
    });
    return _targetError == null && _intervalError == null;
  }

  Future<void> _openLog() async {
    if (!store.logExists()) {
      setState(
        () => _statusLine =
            'Chưa có file log tại ${store.logPath} — agent chưa chạy.',
      );
      return;
    }
    final error = await bridge.openFile(store.logPath);
    if (error != null && mounted) {
      setState(() => _statusLine = 'Không mở được log: $error');
    }
  }

  // -- auto-start -------------------------------------------------------

  Future<void> _refreshAutostart() async {
    // Mock mode stands in for a Windows farm PC in tests/demos.
    _autostartAvailable = Platform.isWindows || bridge.isMock;
    if (!_autostartAvailable) {
      _autostartHint = '(Scheduled Task chỉ có trên Windows)';
      return;
    }
    _autostartHint = '';
    _autostartInstalled = await bridge.taskInstalled();
  }

  Future<void> _toggleAutostart() async {
    if (_busy) return;
    setState(() => _changingAutostart = true);
    try {
      final installed = await bridge.taskInstalled();
      if (!installed &&
          !bridge.running &&
          (!_validateScan() ||
              !await _checkConnection() ||
              !mounted ||
              !_saveConfig())) return;
      final outcome = installed
          ? await bridge.removeTask()
          : await bridge.installTask(store.path);
      await _refreshAutostart();
      if (mounted)
        setState(() => _statusLine = outcome.ok
            ? installed
                ? 'Đã tắt tự khởi động cùng Windows.'
                : 'Đã bật tự khởi động khi đăng nhập Windows.'
            : outcome.message);
    } catch (_) {
      if (mounted)
        setState(() => _statusLine =
            'Chưa đổi được tự khởi động. Kiểm tra quyền Windows rồi thử lại.');
    } finally {
      if (mounted) setState(() => _changingAutostart = false);
    }
  }

  // -- widgets ------------------------------------------------------------

  Color _toneColor(String tone) {
    switch (tone) {
      case 'ok':
        return BeeSkyColors.ok;
      case 'bad':
        return BeeSkyColors.bad;
      case 'warn':
        return BeeSkyColors.warn;
      default:
        return BeeSkyColors.muted;
    }
  }

  Widget _pill(String tone, String text) {
    final color = _toneColor(tone);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: BeeSkyColors.ghostFill,
        borderRadius: BorderRadius.circular(radiusPill),
        border: Border.all(color: BeeSkyColors.glassBorder),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 7),
          Text(text, style: TextStyle(color: color, fontSize: 12.5)),
        ],
      ),
    );
  }

  Widget _fieldLabel(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 5),
        child: Text(
          text,
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 13),
        ),
      );

  Widget _metric(String label, String value, IconData icon) => Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: BeeSkyColors.bg, borderRadius: BorderRadius.circular(6)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(icon, size: 16, color: BeeSkyColors.muted),
          const SizedBox(width: 6),
          Expanded(
              child: Text(label,
                  style:
                      const TextStyle(fontSize: 12, color: BeeSkyColors.muted)))
        ]),
        const SizedBox(height: 6),
        Text(value, style: numStyle(fontSize: 21, weight: FontWeight.w600)),
      ]));

  Widget _detail(String label, String value) => Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label,
            style: const TextStyle(fontSize: 12, color: BeeSkyColors.muted)),
        const SizedBox(height: 2),
        Text(value,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      ]));

  Widget _labeledField(String label, Widget field, {String? hint}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _fieldLabel(label),
          Semantics(label: label, child: field),
          if (hint != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                hint,
                style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }

  Widget _card(String title, List<Widget> children) {
    final icon = switch (title) {
      'Kết nối cloud' => Icons.link_rounded,
      'Quét tại xưởng' => Icons.radar_rounded,
      'Trạng thái chạy ngầm' => Icons.monitor_heart_outlined,
      _ => Icons.settings_outlined,
    };
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 19, color: BeeSkyColors.muted),
              const SizedBox(width: 8),
              Expanded(
                  child: Text(title,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w700))),
            ]),
            const SizedBox(height: 14),
            ...children,
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cloudWarning = insecureCloudWarning(_cloudCtrl.text);
    final tokenField = Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _fieldLabel('Token Agent:'),
          TextField(
            controller: _keyCtrl,
            readOnly: !_editable,
            autocorrect: false,
            enableSuggestions: false,
            obscureText: !_showKey,
            decoration: InputDecoration(
              hintText: 'Dán token từ Mine',
              suffixIcon: IconButton(
                tooltip: _showKey ? 'Ẩn token' : 'Hiện token',
                icon: Icon(
                  _showKey
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  size: 18,
                ),
                onPressed:
                    _busy ? null : () => setState(() => _showKey = !_showKey),
              ),
            ),
          ),
          if (_keyProtected)
            const Padding(
              padding: EdgeInsets.only(top: 4),
              child: Text(
                _protectedKeyHint,
                style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
              ),
            ),
        ],
      ),
    );
    final siteField = _labeledField(
      'Xưởng được cấp quyền:',
      TextField(
        controller: _siteCtrl,
        readOnly: true,
        decoration: const InputDecoration(
          prefixIcon: Icon(Icons.factory_outlined, size: 18),
          hintText: 'Tự nhận sau khi kiểm tra token',
        ),
      ),
      hint: _connection == null
          ? 'Xưởng được quyết định bởi token trên Mine.'
          : '${_connection!.organizationName} · ${_connection!.agentName}',
    );
    final connection = _card('Kết nối cloud', [
      _labeledField(
        'Cloud URL:',
        TextField(
            controller: _cloudCtrl,
            readOnly: !_editable,
            decoration: const InputDecoration(
                prefixIcon: Icon(Icons.language, size: 18))),
        hint: cloudWarning,
      ),
      LayoutBuilder(builder: (context, size) {
        if (size.maxWidth < 540)
          return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [tokenField, siteField]);
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: tokenField),
          const SizedBox(width: 16),
          Expanded(child: siteField)
        ]);
      }),
      Align(
        alignment: Alignment.centerLeft,
        child: OutlinedButton.icon(
          onPressed: _busy || bridge.running ? null : _checkConnection,
          icon: _checking
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.verified_user_outlined, size: 18),
          label: Text(_checking ? 'Đang kiểm tra…' : 'Kiểm tra token'),
        ),
      ),
      const SizedBox(height: 10),
      Semantics(
          key: const ValueKey('agent-connection-feedback'),
          liveRegion: true,
          child: Text(
              _checking
                  ? 'Đang kiểm tra token với Mine…'
                  : _connectionError ??
                      (_connection == null
                          ? bridge.running && !bridge.runtimeUncertain
                              ? 'Agent đang dùng token đã lưu.'
                              : 'Chưa kiểm tra token.'
                          : 'Đã kết nối: ${_connection!.siteName} · ${_connection!.organizationName}'),
              style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: _connectionError != null
                      ? BeeSkyColors.bad
                      : _connection != null
                          ? BeeSkyColors.ok
                          : BeeSkyColors.muted))),
    ]);
    final scan = _card('Quét tại xưởng', [
      _labeledField(
        'Dải IP quét:',
        TextField(
            controller: _targetCtrl,
            readOnly: !_editable,
            onChanged: (_) {
              if (_targetError != null) setState(() => _targetError = null);
            },
            decoration: InputDecoration(
                prefixIcon: const Icon(Icons.lan_outlined, size: 18),
                errorText: _targetError,
                errorMaxLines: 2)),
        hint: 'IPv4 / CIDR / dải IP. Nhiều dải cách nhau bằng dấu phẩy.',
      ),
      _labeledField(
        'Chu kỳ quét (giây):',
        TextField(
            controller: _intervalCtrl,
            readOnly: !_editable,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            onChanged: (_) {
              if (_intervalError != null) setState(() => _intervalError = null);
            },
            decoration: InputDecoration(
                prefixIcon: const Icon(Icons.timer_outlined, size: 18),
                suffixText: 'giây',
                errorText: _intervalError)),
      ),
    ]);
    final status = _card('Trạng thái chạy ngầm', [
      Semantics(
          liveRegion: true,
          child: _pill(_statusView.tone, _statusView.pillText)),
      const SizedBox(height: 14),
      Text(_statusView.bodyText,
          style: const TextStyle(
              color: BeeSkyColors.muted, fontSize: 13, height: 1.6)),
      const Padding(
          padding: EdgeInsets.symmetric(vertical: 12),
          child: Divider(height: 1)),
      Row(children: [
        Expanded(
            child: _metric(
                'Máy phản hồi',
                _lastStatus == null ? '—' : '${_lastStatus!.miners}',
                Icons.memory_outlined)),
        const SizedBox(width: 12),
        Expanded(
            child: _metric('Chu kỳ đã lưu',
                '${formatInterval(_savedInterval)} giây', Icons.update)),
      ]),
      const SizedBox(height: 14),
      _detail('Vòng quét gần nhất', _lastStatus?.time ?? 'Chưa có vòng quét'),
      _detail(
          'Gửi lên Mine',
          _lastStatus == null
              ? 'Chưa có dữ liệu'
              : _lastStatus!.ok
                  ? 'Thành công ở vòng gần nhất'
                  : 'Chưa thành công · sẽ thử lại'),
      if (_testing || _testPillTone != 'dim')
        Padding(
            padding: const EdgeInsets.only(top: 8),
            child: _pill(_testPillTone, _testPillText)),
      const SizedBox(height: 12),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          OutlinedButton.icon(
            onPressed: _busy ? null : _refreshRuntime,
            icon: const Icon(Icons.refresh, size: 17),
            label: const Text('Làm mới'),
          ),
          OutlinedButton.icon(
              onPressed: _openLog,
              icon: const Icon(Icons.article_outlined, size: 17),
              label: const Text('Xem log')),
        ],
      ),
    ]);
    final startup = _card('Khởi động & cấu hình', [
      MergeSemantics(
          child: InkWell(
        canRequestFocus: false,
        excludeFromSemantics: true,
        borderRadius: BorderRadius.circular(6),
        onTap: _busy || !_autostartAvailable || bridge.runtimeUncertain
            ? null
            : _toggleAutostart,
        child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    const Text('Tự khởi động cùng Windows',
                        style: TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 2),
                    Text(
                        _changingAutostart
                            ? 'Đang cập nhật…'
                            : _autostartInstalled
                                ? 'Đã bật · chạy khi đăng nhập'
                                : 'Chưa bật',
                        style: const TextStyle(
                            fontSize: 12, color: BeeSkyColors.muted)),
                  ])),
              const SizedBox(width: 12),
              BeeSkySwitch(
                  value: _autostartInstalled,
                  onChanged:
                      _busy || !_autostartAvailable || bridge.runtimeUncertain
                          ? null
                          : (_) => _toggleAutostart()),
            ])),
      )),
      const SizedBox(height: 8),
      const Text(
          'Đóng cửa sổ, Agent vẫn tiếp tục chạy. Dùng Dừng Agent khi muốn ngừng quét.',
          style:
              TextStyle(color: BeeSkyColors.muted, fontSize: 12, height: 1.6)),
      if (_autostartHint.isNotEmpty) Text(_autostartHint),
      AgentUpdatePanel(
          key: _updateKey,
          updater: _updater,
          config: store.path,
          enabled: !_busy && !bridge.runtimeUncertain,
          unsavedChanges: _unsavedChanges,
          onBusy: (value) {
            if (mounted) setState(() => _updating = value);
          },
          onInfo: (info) {
            if (mounted) setState(() => _updateInfo = info);
          },
          onFeedback: (message, error, progress) {
            if (mounted)
              setState(() {
                _updateMessage = message;
                _updateError = error;
                _updateProgress = progress;
              });
          }),
      ExpansionTile(
          tilePadding: EdgeInsets.zero,
          childrenPadding: const EdgeInsets.only(bottom: 8),
          title:
              const Text('Thông tin chẩn đoán', style: TextStyle(fontSize: 12)),
          children: [
            SelectableText(
                'Cấu hình: ${store.path}\nNhật ký: ${store.logPath}\nBộ chạy: ${bridge.agentExePath}',
                style: const TextStyle(
                    fontSize: 12, color: BeeSkyColors.muted, height: 1.7))
          ]),
    ]);
    return Scaffold(
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 20),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1120),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (!widget.embedded)
                        Row(
                          children: [
                            Image.asset(
                              'assets/beesky-logo.png',
                              width: 40,
                              height: 40,
                            ),
                            const SizedBox(width: 10),
                            const Expanded(
                                child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'BeeSky Agent',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                Text(
                                  'Kết nối xưởng với Mine',
                                  style: TextStyle(color: BeeSkyColors.muted),
                                ),
                              ],
                            )),
                            const SizedBox(width: 12),
                            _pill('dim', 'v$agentAppVersion'),
                          ],
                        ),
                      if (_updateInfo?.available == true)
                        Padding(
                            padding: const EdgeInsets.only(top: 12),
                            child: Material(
                                color: BeeSkyColors.surface,
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(6),
                                    side: const BorderSide(
                                        color: BeeSkyColors.border)),
                                child: Padding(
                                    padding: const EdgeInsets.all(12),
                                    child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.stretch,
                                        children: [
                                          Wrap(
                                              alignment:
                                                  WrapAlignment.spaceBetween,
                                              crossAxisAlignment:
                                                  WrapCrossAlignment.center,
                                              spacing: 12,
                                              runSpacing: 8,
                                              children: [
                                                Text(
                                                    _updateMessage ??
                                                        'Agent ${_updateInfo!.latest} đã sẵn sàng.',
                                                    style: TextStyle(
                                                        color: _updateError
                                                            ? BeeSkyColors.bad
                                                            : BeeSkyColors.text,
                                                        fontSize: 13,
                                                        fontWeight:
                                                            FontWeight.w600)),
                                                TextButton.icon(
                                                    onPressed: !_busy &&
                                                            !bridge
                                                                .runtimeUncertain
                                                        ? () => _updateKey
                                                            .currentState
                                                            ?.requestUpdate()
                                                        : null,
                                                    icon: const Icon(
                                                        Icons.system_update_alt,
                                                        size: 17),
                                                    label: const Text(
                                                        'Cập nhật Agent')),
                                              ]),
                                          if (_updating)
                                            Padding(
                                                padding: const EdgeInsets.only(
                                                    top: 8),
                                                child: LinearProgressIndicator(
                                                    value: _updateProgress))
                                        ])))),
                      LayoutBuilder(
                        builder: (context, size) {
                          if (size.maxWidth < 900)
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: bridge.running
                                  ? [status, connection, scan, startup]
                                  : [connection, scan, status, startup],
                            );
                          return Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                flex: 3,
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [connection, scan],
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                flex: 2,
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    status,
                                    startup,
                                  ],
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                      if (bridge.running)
                        Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(
                            'Dừng Agent trước khi sửa token, dải IP hoặc chu kỳ quét.',
                            style: const TextStyle(
                              color: BeeSkyColors.muted,
                              fontSize: 12,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
              child: Semantics(
                  liveRegion: true,
                  child: Text(_statusLine,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 12, color: BeeSkyColors.text)))),
          Container(
            width: double.infinity,
            decoration: const BoxDecoration(
              color: BeeSkyColors.surface,
              border: Border(top: BorderSide(color: BeeSkyColors.border)),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 10,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        icon: _changingRun
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : Icon(
                                bridge.running
                                    ? Icons.stop_rounded
                                    : Icons.play_arrow_rounded,
                                size: 20),
                        onPressed: _busy ? null : _toggleAgent,
                        label: Text(
                          _changingRun
                              ? 'Đang xử lý…'
                              : bridge.runtimeUncertain
                                  ? 'Kiểm tra trạng thái'
                                  : bridge.running
                                      ? 'Dừng Agent'
                                      : 'Bắt đầu Agent',
                        ),
                      ),
                      OutlinedButton.icon(
                        onPressed: _editable ? _saveConfig : null,
                        icon: const Icon(Icons.save_outlined, size: 18),
                        label: const Text('Lưu cấu hình'),
                      ),
                      OutlinedButton.icon(
                        onPressed: _editable ? _startTest : null,
                        icon: _testing
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.science_outlined, size: 18),
                        label: Text(_testing ? 'Đang chạy thử…' : 'Chạy thử'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
