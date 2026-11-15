import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';

import 'agent_bridge.dart';
import 'agent_config.dart';
import 'theme.dart';

const String _keyNote =
    'Agent key do cloud cấp và chỉ hiện MỘT lần lúc tạo agent '
    '(trang Cài đặt của cloud) — dán vào đây rồi Lưu cấu hình. '
    'Key chỉ nằm trong file cấu hình này (trên Windows được '
    'Windows mã hoá DPAPI ngay trong file); mất key thì thu hồi '
    'agent cũ trên cloud và tạo agent mới.';

const String _protectedKeyHint =
    'Key đang lưu dạng mã hoá DPAPI — để trống để giữ nguyên, '
    'nhập mới để thay.';

String _stamp() {
  final now = DateTime.now();
  String two(int v) => v.toString().padLeft(2, '0');
  return '${two(now.hour)}:${two(now.minute)}:${two(now.second)}';
}

/// The agent config window — a 1:1 port of the Tk window
/// (`beesky/agent_gui.py`): same cards, same fields, same status
/// texts, same validation (docs/agent-app-mapping.md). Process
/// work goes through [AgentBridge]; the config file through
/// [AgentConfigStore].
class AgentConfigPage extends StatefulWidget {
  final AgentBridge bridge;
  final AgentConfigStore store;
  const AgentConfigPage({super.key, required this.bridge, required this.store});

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
  bool _keyProtected = false;
  bool _testing = false;
  String _statusLine = '';
  String _testPillTone = 'dim';
  String _testPillText = 'Chưa chạy thử';
  StatusView _statusView = deriveStatusView(null);
  DateTime? _statusMtime;
  bool _autostartAvailable = true;
  bool _autostartInstalled = false;
  String _autostartHint = '';
  Timer? _timer;

  AgentBridge get bridge => widget.bridge;
  AgentConfigStore get store => widget.store;

  @override
  void initState() {
    super.initState();
    _statusLine = 'File cấu hình: ${store.path}';
    _cloudCtrl.addListener(() => setState(() {}));
    _init();
    // The Tk window polls the status file's mtime every 100 ms;
    // 2 s here (divergence D7 — status changes once per cycle).
    _timer = Timer.periodic(const Duration(seconds: 2), (_) {
      final mtime = store.statusModified();
      if (mtime != _statusMtime && mounted) {
        setState(_refreshStatusCard);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in [_cloudCtrl, _keyCtrl, _siteCtrl, _targetCtrl, _intervalCtrl]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _init() async {
    if (!store.exists()) {
      // First run: pre-fill the scan target with this machine's
      // own subnet, via the sidecar's sysinfo (D5).
      final target = await bridge.sysinfoDefaultTarget();
      if (mounted && target != null && _targetCtrl.text.isEmpty) {
        setState(() => _targetCtrl.text = target);
      }
    } else {
      try {
        final cfg = store.load();
        _fillFields(cfg);
        _statusLine =
            'Đã nạp cấu hình từ ${store.path} — sửa rồi Lưu, hoặc Chạy thử ngay.';
      } on FormatException catch (e) {
        _statusLine = 'Không đọc được cấu hình: ${e.message}';
      }
      if (mounted) setState(() {});
    }
    _refreshStatusCard();
    await _refreshAutostart();
    if (mounted) setState(() {});
  }

  void _fillFields(AgentConfig cfg) {
    _cloudCtrl.text = cfg.cloudUrl;
    _keyCtrl.text = cfg.key;
    _siteCtrl.text = cfg.site;
    _targetCtrl.text = cfg.target;
    _intervalCtrl.text = formatInterval(cfg.interval);
    _keyProtected = cfg.hasProtectedKey;
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
    if (parsed == null) {
      return (null, "chu kỳ quét '$raw' không phải số giây hợp lệ");
    }
    if (parsed <= 0) {
      return (null, 'chu kỳ quét phải lớn hơn 0 giây');
    }
    base.interval = parsed;
    return (base, null);
  }

  void _saveConfig() {
    final (cfg, error) = _currentConfig();
    if (error != null) {
      setState(() => _statusLine = 'Chưa lưu được: $error');
      return;
    }
    final missing = cfg!.missingFields();
    if (missing.isNotEmpty) {
      setState(() =>
          _statusLine = 'Chưa lưu được — còn thiếu: ${missing.join(', ')}');
      return;
    }
    try {
      store.save(cfg);
    } catch (e) {
      setState(() => _statusLine = 'Chưa lưu được: $e');
      return;
    }
    setState(() {
      _keyProtected = cfg.hasProtectedKey;
      _statusLine = 'Đã lưu cấu hình vào ${store.path} (${_stamp()}). '
          'Agent chạy bằng: beesky-agent run';
    });
  }

  // -- test cycle -----------------------------------------------------

  Future<void> _startTest() async {
    if (_testing) return;
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
    });
  }

  // -- background status ----------------------------------------------

  void _refreshStatusCard() {
    _statusMtime = store.statusModified();
    _statusView = deriveStatusView(store.readStatus());
  }

  Future<void> _openLog() async {
    if (!store.logExists()) {
      setState(() => _statusLine =
          'Chưa có file log tại ${store.logPath} — agent chưa chạy.');
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
    final installed = await bridge.taskInstalled();
    final outcome = installed
        ? await bridge.removeTask()
        : await bridge.installTask(store.path);
    await _refreshAutostart();
    if (mounted) setState(() => _statusLine = outcome.message);
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
        child: Text(text,
            style: const TextStyle(color: BeeSkyColors.muted, fontSize: 13)),
      );

  Widget _labeledField(String label, Widget field, {String? hint}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _fieldLabel(label),
          field,
          if (hint != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(hint,
                  style: const TextStyle(
                      color: BeeSkyColors.muted, fontSize: 12)),
            ),
        ],
      ),
    );
  }

  Widget _card(String title, List<Widget> children) {
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(
                    fontSize: 15, fontWeight: FontWeight.w700)),
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
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header: logo + titles + version pill.
            Row(
              children: [
                Image.asset('assets/beesky-logo.png', width: 40, height: 40),
                const SizedBox(width: 10),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('BeeSky Agent',
                        style: TextStyle(
                            fontSize: 20, fontWeight: FontWeight.w800)),
                    Text('Cấu hình agent tại trại',
                        style: TextStyle(color: BeeSkyColors.muted)),
                  ],
                ),
                const Spacer(),
                _pill('dim', 'v$agentAppVersion'),
              ],
            ),

            // Card 1: cloud connection.
            _card('Kết nối cloud', [
              _labeledField(
                'Cloud URL:',
                TextField(controller: _cloudCtrl),
                hint: cloudWarning == null ? null : '⚠ $cloudWarning',
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _fieldLabel('Agent key:'),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _keyCtrl,
                            obscureText: !_showKey,
                          ),
                        ),
                        Checkbox(
                          value: _showKey,
                          onChanged: (v) =>
                              setState(() => _showKey = v ?? false),
                        ),
                        const Text('Hiện key'),
                      ],
                    ),
                    if (_keyProtected)
                      const Padding(
                        padding: EdgeInsets.only(top: 4),
                        child: Text(_protectedKeyHint,
                            style: TextStyle(
                                color: BeeSkyColors.muted, fontSize: 12)),
                      ),
                  ],
                ),
              ),
              _labeledField(
                'Tên trại:',
                TextField(controller: _siteCtrl),
                hint: 'vd Xưởng 1',
              ),
              const Text(_keyNote,
                  style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5)),
            ]),

            // Card 2: farm scan.
            _card('Quét tại trại', [
              _labeledField(
                'Dải IP quét:',
                TextField(controller: _targetCtrl),
                hint: 'vd 192.168.1.10-192.168.1.60 — nhiều dải cách nhau bằng dấu phẩy',
              ),
              _labeledField(
                'Chu kỳ quét (giây):',
                Align(
                  alignment: Alignment.centerLeft,
                  child: SizedBox(
                    width: 120,
                    child: TextField(controller: _intervalCtrl),
                  ),
                ),
              ),
            ]),

            // Card 3: background run status.
            _card('Trạng thái chạy ngầm', [
              Row(
                children: [
                  _pill(_statusView.tone, _statusView.pillText),
                  const Spacer(),
                  OutlinedButton(
                    onPressed: () =>
                        setState(_refreshStatusCard),
                    child: const Text('Làm mới'),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton(
                    onPressed: _openLog,
                    child: const Text('Xem log'),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(_statusView.bodyText,
                  style: const TextStyle(
                      color: BeeSkyColors.muted, fontSize: 12.5)),
            ]),

            // Actions row + test pill (buttons left, pill right —
            // the buttons Wrap inside the Expanded so a narrow
            // window flows them instead of overflowing).
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 8,
                      children: [
                        FilledButton(
                          onPressed: _saveConfig,
                          child: const Text('Lưu cấu hình'),
                        ),
                        OutlinedButton(
                          onPressed: _testing ? null : _startTest,
                          child: const Text('Chạy thử'),
                        ),
                        OutlinedButton(
                          onPressed:
                              _autostartAvailable ? _toggleAutostart : null,
                          child: Text(_autostartInstalled
                              ? 'Tắt tự khởi động'
                              : 'Bật tự khởi động'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  _pill(_testPillTone, _testPillText),
                ],
              ),
            ),
            if (_autostartHint.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(_autostartHint,
                    style: const TextStyle(color: BeeSkyColors.muted)),
              ),

            // Footer status line.
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(_statusLine,
                  style: const TextStyle(color: BeeSkyColors.muted)),
            ),
          ],
        ),
      ),
    );
  }
}
