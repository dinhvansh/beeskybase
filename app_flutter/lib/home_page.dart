import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';

import 'creds.dart';
import 'groups.dart';
import 'models.dart';
import 'sidecar.dart';
import 'theme.dart';

/// The two content views: the app OPENS on network groups (the
/// HashCore Toolkit's home screen, v0.24); the miners table is the
/// per-group / ad-hoc scan view behind it.
enum _View { groups, miners }

/// The main window — v0.22 layout, restructured after the owner rejected
/// the v0.21 hero-card layout ("card to để làm gì, người ta muốn thấy
/// máy đào" — what are the big cards FOR, people want to SEE THE
/// MINERS). The structure now mirrors the HashCore Toolkit he pointed
/// at: a left sidebar (brand + nav + version), a slim header whose stats
/// are compact chips in ONE row, one slim scan bar, and the miners table
/// filling everything else. The detail view is a right-hand panel that
/// only takes width while a row is selected. BeeSky's palette and the
/// sidecar wiring are unchanged — structure changed, identity didn't.
class HomePage extends StatefulWidget {
  final BeeSkyBridge bridge;

  /// Credential-store override (tests point it at a temp dir); the
  /// real app uses [CredStore.appDefault] — beesky-creds.json beside
  /// the executable.
  final CredStore? credStore;

  /// Group-store override (tests point it at a temp dir); the real
  /// app uses [GroupStore.appDefault] — beesky-groups.json beside
  /// the executable, the same folder as the creds file.
  final GroupStore? groupStore;

  /// Row double-click opener override (tests record the URL instead
  /// of launching a browser); defaults to [openUrlInBrowser].
  final Future<void> Function(String url)? urlOpener;

  const HomePage({
    super.key,
    required this.bridge,
    this.credStore,
    this.groupStore,
    this.urlOpener,
  });

  @override
  State<HomePage> createState() => _HomePageState();
}

/// Demo credential sets for the MOCK shell only: the dialog shows a
/// realistic mix (one vnish, one stock, one "any") instead of an
/// empty list. In-memory — persisted only if the user saves them.
final _demoCreds = [
  CredSet(
    label: 'VNish trại A',
    user: 'root',
    secret: 'vnish-pw',
    type: 'vnish',
  ),
  CredSet(
    label: 'Kho S19 gốc',
    user: 'root',
    secret: 'root',
    type: 'stock',
  ),
  CredSet(
    label: 'Dự phòng chung',
    user: 'root',
    secret: 'root',
    type: 'any',
  ),
];

class _HomePageState extends State<HomePage> {
  final _targetCtrl = TextEditingController();

  SysInfo? _sysinfo;
  bool _sysinfoFailed = false;
  List<MinerRecord> _records = const [];
  ScanResult? _lastScan;
  MinerRecord? _selected;
  bool _scanned = false;
  bool _busy = false;
  String _status = 'Sẵn sàng.';

  late final CredStore _store = widget.credStore ?? CredStore.appDefault();
  List<CredSet> _creds = const [];
  File? _credsFile;

  // Network groups (v0.24): the app opens on the groups view; a
  // group scan scopes the miners view to that group until the user
  // edits the target away from the group's ranges.
  _View _view = _View.groups;
  late final GroupStore _groupStore =
      widget.groupStore ?? GroupStore.appDefault();
  List<NetGroup> _groups = const [];
  File? _groupsFile;
  NetGroup? _activeGroup;

  // App-side autoscan (pre-approved divergence — HashCore's runs
  // app-side too): a slow timer re-scans the ACTIVE group when its
  // own interval has elapsed. The always-on equivalent is the
  // farm agent, not this timer.
  Timer? _autoscanTimer;
  final Map<String, DateTime> _lastAutoscanRun = {};

  @override
  void initState() {
    super.initState();
    // The mock shell shows its demo sets instantly (the mixed-type
    // list is part of the demo); the file load below still replaces
    // them when a real creds file exists.
    if (widget.bridge.isMock) {
      _creds = _demoCreds.map((c) => c.copy()).toList();
      _groups = demoGroups();
    }
    _loadSysinfo();
    _loadCreds();
    _loadGroups();
    _autoscanTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _tickAutoscan(),
    );
  }

  @override
  void dispose() {
    _autoscanTimer?.cancel();
    _targetCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadCreds() async {
    final (creds, file) = await _store.load();
    if (!mounted) return;
    // An existing file wins over the mock demo seed; an empty load
    // leaves the seed (mock) or the empty list (real) untouched.
    if (creds.isEmpty) return;
    setState(() {
      _creds = creds;
      _credsFile = file;
    });
  }

  /// The creds-file path a scan should use, or null: no sets saved,
  /// or the mock bridge (which never reads files). In-memory-only
  /// sets are persisted on first use so the sidecar can read them.
  Future<String?> _credsFileForScan() async {
    if (_creds.isEmpty || widget.bridge.isMock) return null;
    if (_credsFile != null) return _credsFile!.path;
    final file = await _store.save(_creds);
    _credsFile = file;
    return file.path;
  }

  Future<void> _editCreds() async {
    final result = await showCredsDialog(context, _creds);
    if (result == null || !mounted) return;
    File? file;
    try {
      file = await _store.save(result);
    } on FileSystemException {
      // Saving failed everywhere — keep the sets for this session;
      // scans will persist on demand via _credsFileForScan.
      file = null;
    }
    if (!mounted) return;
    setState(() {
      _creds = result;
      _credsFile = file;
      _status = 'Đã lưu ${result.length} bộ tài khoản máy đào.';
    });
  }

  // ------------------------------------------------------------------
  // Network groups: load/save, editor, delete, group scans, autoscan
  // ------------------------------------------------------------------

  Future<void> _loadGroups() async {
    final (groups, file) = await _groupStore.load();
    if (!mounted) return;
    // An existing file wins over the mock demo seed; an empty load
    // leaves the seed (mock) or the empty list (real) untouched.
    if (groups.isEmpty) return;
    setState(() {
      _groups = groups;
      _groupsFile = file;
      // Re-point the active group at the fresh object (a group scan
      // reloads the store after the core persisted last_scan).
      final active = _activeGroup;
      if (active != null) {
        for (final g in groups) {
          if (g.id == active.id) _activeGroup = g;
        }
      }
    });
  }

  Future<void> _saveGroups() async {
    try {
      _groupsFile = await _groupStore.save(_groups);
    } on FileSystemException {
      // Saving failed everywhere — the in-memory list stands for
      // this session; a later edit retries the write.
    }
  }

  Future<void> _editGroup({NetGroup? existing}) async {
    final result = await showGroupEditorDialog(context, existing: existing);
    if (result == null || !mounted) return;
    final clash = _groups.any(
      (g) => g.name == result.name && g.id != result.id,
    );
    if (clash) {
      setState(
        () => _status = 'Đã có nhóm tên "${result.name}" — '
            'tên nhóm phải khác nhau.',
      );
      _showSnack('Đã có nhóm tên "${result.name}".');
      return;
    }
    setState(() {
      if (existing == null) {
        _groups = [..._groups, result];
        _status = 'Đã thêm nhóm ${result.name}.';
      } else {
        _groups = [
          for (final g in _groups) g.id == existing.id ? result : g,
        ];
        if (_activeGroup?.id == existing.id) _activeGroup = result;
        _status = 'Đã sửa nhóm ${result.name}.';
      }
    });
    await _saveGroups();
  }

  Future<void> _deleteGroup(NetGroup group) async {
    // HashCore asks before removing a group, naming it — mirrored.
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: BeeSkyColors.panel,
        title: const Text('Xóa nhóm?'),
        content: Text(
          'Nhóm "${group.name}" sẽ bị xóa khỏi danh sách. '
          'Các máy trong nhóm không bị ảnh hưởng.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() {
      _groups = _groups.where((g) => g.id != group.id).toList();
      if (_activeGroup?.id == group.id) _activeGroup = null;
      _status = 'Đã xóa nhóm ${group.name}.';
    });
    await _saveGroups();
  }

  /// Enter a group from its card: the miners view scopes to it and
  /// the group scan starts immediately.
  void _scanGroup(NetGroup group) {
    setState(() {
      _activeGroup = group;
      _view = _View.miners;
      _targetCtrl.text = group.targets;
    });
    _runGroupScan(group);
  }

  /// One scan THROUGH the group: the core resolves targets, merges
  /// the group's creds ahead of the global file's, and persists
  /// last_scan (mock mode updates the demo group in memory instead).
  Future<void> _runGroupScan(NetGroup group) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _status = 'Đang quét nhóm ${group.name} …';
    });
    try {
      final result = widget.bridge.isMock
          ? await widget.bridge.scan(group.targets)
          : await widget.bridge.scanGroup(
              group.name,
              credsFile: await _credsFileForScan(),
              groupsFile: _groupsFile?.path,
            );
      if (!mounted) return;
      _applyScanResult(result);
      _lastAutoscanRun[group.id] = DateTime.now();
      setState(
        () => _status = 'Quét nhóm ${group.name} xong: tìm thấy '
            '${result.found} máy trong ${result.scanned} địa chỉ '
            '(${result.elapsedS.toStringAsFixed(1)} giây).',
      );
      if (widget.bridge.isMock) {
        setState(() => group.lastScan = _summaryOf(result));
      } else {
        await _loadGroups();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Lỗi quét nhóm ${group.name}: $e');
      _showSnack('Lỗi quét nhóm: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// A GroupLastScan from a finished pass, counted exactly like
  /// the core's scan_summary (mock mode only — the real core
  /// persists its own).
  GroupLastScan _summaryOf(ScanResult result) {
    final ok = fleetStatusCount(result.records, 'OK');
    final error = fleetStatusCount(result.records, 'ERROR');
    return GroupLastScan(
      at: DateTime.now().toIso8601String(),
      scanned: result.scanned,
      found: result.records.length,
      ok: ok,
      check: result.records.length - ok - error,
      error: error,
    );
  }

  void _tickAutoscan() {
    if (!mounted || _busy) return;
    final group = _activeGroup;
    if (group == null) return;
    final last = _lastAutoscanRun[group.id] ?? group.lastScan?.atTime;
    if (autoscanDue(group, last, DateTime.now())) {
      _runGroupScan(group);
    }
  }

  Future<void> _loadSysinfo() async {
    try {
      final info = await widget.bridge.sysinfo();
      if (!mounted) return;
      setState(() {
        _sysinfo = info;
        _sysinfoFailed = false;
        // Pre-fill the target with this machine's own /24 (the v0.19.6
        // lesson: a hard-coded foreign subnet finds nothing at a farm),
        // unless the user already typed something.
        if (_targetCtrl.text.isEmpty) {
          _targetCtrl.text = info.defaultTarget;
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sysinfoFailed = true;
        _status = 'Không đọc được sysinfo từ beesky: $e';
      });
    }
  }

  String get _target => _targetCtrl.text.trim().isEmpty
      ? '192.168.1.0/24'
      : _targetCtrl.text.trim();

  /// Land a finished pass on the table (both scan paths share it):
  /// v0.19.7 behaviour — the first row is selected so the detail
  /// panel is alive immediately.
  void _applyScanResult(ScanResult result) {
    setState(() {
      _records = result.records;
      _lastScan = result;
      _scanned = true;
      _selected = result.records.isEmpty ? null : result.records.first;
    });
  }

  Future<void> _runScan() async {
    if (_busy) return;
    // In a group's scope with the group's own ranges still in the
    // target field, the scan IS a group scan (core-side resolution,
    // merged creds, last_scan persisted). Editing the target away
    // from the group's ranges leaves the scope — an ad-hoc scan.
    final group = _activeGroup;
    if (group != null && _target == group.targets) {
      await _runGroupScan(group);
      return;
    }
    if (group != null) setState(() => _activeGroup = null);
    setState(() {
      _busy = true;
      _status = 'Đang quét $_target …';
    });
    try {
      final result = await widget.bridge.scan(
        _target,
        credsFile: await _credsFileForScan(),
      );
      if (!mounted) return;
      _applyScanResult(result);
      setState(
        () => _status = 'Quét xong: tìm thấy ${result.found} máy trong '
            '${result.scanned} địa chỉ '
            '(${result.elapsedS.toStringAsFixed(1)} giây).',
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Lỗi quét: $e');
      _showSnack('Lỗi quét: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _exportTickets() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _status = 'Đang xuất phiếu sửa…';
    });
    try {
      final dest = await widget.bridge.exportTickets(
        _target,
        credsFile: await _credsFileForScan(),
      );
      if (!mounted) return;
      setState(() => _status = 'Đã xuất phiếu sửa vào: $dest');
      _showSnack('Đã xuất phiếu sửa vào: $dest');
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Lỗi xuất phiếu: $e');
      _showSnack('Lỗi xuất phiếu: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Double-click a row: open that miner's own web admin in the OS
  /// browser (BTC Tools-style), and select the row as a single click
  /// would.
  void _openMinerWeb(MinerRecord rec) {
    setState(() => _selected = rec);
    final opener = widget.urlOpener ?? openUrlInBrowser;
    opener('http://${rec.ip}');
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _sidebar(),
          Expanded(
            child: _view == _View.groups
                ? _groupsColumn()
                : _minersColumn(),
          ),
        ],
      ),
    );
  }

  Widget _minersColumn() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _header(),
        _scanBar(),
        if (_busy) const LinearProgressIndicator(minHeight: 3),
        Expanded(child: _content()),
        _statusLine(),
      ],
    );
  }

  Widget _groupsColumn() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _groupsHeader(),
        if (_busy) const LinearProgressIndicator(minHeight: 3),
        Expanded(child: _groupsContent()),
        _statusLine(),
      ],
    );
  }

  // ------------------------------------------------------------------
  // Sidebar
  // ------------------------------------------------------------------

  Widget _sidebar() {
    return Container(
      width: 228,
      decoration: const BoxDecoration(
        color: BeeSkyColors.panel,
        border: Border(right: BorderSide(color: BeeSkyColors.border)),
      ),
      padding: const EdgeInsets.fromLTRB(18, 20, 14, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Image.asset('assets/beesky-logo.png', width: 40, height: 40),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'BeeSky',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      'QUẢN LÝ MÁY ĐÀO',
                      style: TextStyle(
                        color: BeeSkyColors.muted,
                        fontSize: 10,
                        letterSpacing: 1.6,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          // The app opens on network groups — the HashCore home
          // screen (v0.24); the miners table is one click away.
          _navItem(
            Icons.device_hub,
            'Nhóm mạng',
            active: _view == _View.groups,
            onTap: () => setState(() => _view = _View.groups),
          ),
          _navItem(
            Icons.memory,
            'Máy đào',
            active: _view == _View.miners,
            onTap: () => setState(() => _view = _View.miners),
          ),
          // Roadmap views: listed so the structure matches where the
          // product is going, greyed + "SAU" until they are real —
          // no fake functionality behind them.
          _navItem(Icons.grid_on, 'Bản đồ nhiệt', upcoming: true),
          _navItem(Icons.bolt, 'Điện năng', upcoming: true),
          _navItem(Icons.build, 'Lịch sử sửa', upcoming: true),
          _navItem(Icons.notifications_none, 'Sự kiện', upcoming: true),
          _navItem(Icons.settings, 'Cài đặt', upcoming: true),
          const Spacer(),
          _sidebarFooter(),
        ],
      ),
    );
  }

  Widget _navItem(
    IconData icon,
    String label, {
    bool active = false,
    bool upcoming = false,
    VoidCallback? onTap,
  }) {
    final row = Container(
      height: 38,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        // The approved prototype tints the active item with the
        // accent itself instead of a neutral fill.
        color: active
            ? BeeSkyColors.accent.withValues(alpha: 0.13)
            : Colors.transparent,
        borderRadius: BorderRadius.circular(radiusWidget),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            size: 18,
            color: active ? BeeSkyColors.accent : BeeSkyColors.muted,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: active ? BeeSkyColors.accent : BeeSkyColors.muted,
                fontSize: 13,
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (upcoming) _soonTag(),
        ],
      ),
    );
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: onTap == null
          ? row
          : InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(radiusWidget),
              child: row,
            ),
    );
  }

  Widget _soonTag() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: BeeSkyColors.entryFill,
        borderRadius: BorderRadius.circular(radiusPill),
      ),
      child: const Text(
        'SAU',
        style: TextStyle(
          color: BeeSkyColors.muted,
          fontSize: 9,
          letterSpacing: 0.6,
        ),
      ),
    );
  }

  /// (dot colour, label) for the sidebar footer: mock mode, sidecar
  /// found and talking, sidecar exe missing beside the app, or the
  /// sysinfo probe still in flight / failed.
  (Color, String) _sidecarStatus() {
    if (widget.bridge.isMock) {
      return (BeeSkyColors.warn, 'Ruột quét: dữ liệu mẫu');
    }
    final exe = widget.bridge.exePath;
    if (exe != null &&
        exe.contains(Platform.pathSeparator) &&
        !File(exe).existsSync()) {
      return (BeeSkyColors.bad, 'Ruột quét: thiếu beesky.exe');
    }
    if (_sysinfo != null) return (BeeSkyColors.ok, 'Ruột quét: đã nối');
    if (_sysinfoFailed) return (BeeSkyColors.bad, 'Ruột quét: không nối được');
    return (BeeSkyColors.muted, 'Ruột quét: đang kiểm tra…');
  }

  Widget _sidebarFooter() {
    final (dot, label) = _sidecarStatus();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(color: BeeSkyColors.muted, fontSize: 11),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          _sysinfo == null ? 'BeeSky v…' : 'BeeSky v${_sysinfo!.version}',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 11),
        ),
      ],
    );
  }

  // ------------------------------------------------------------------
  // Header: view title + network line, then the stat chips in ONE row
  // (the approved prototype's arrangement — chips are pills, never
  // big cards)
  // ------------------------------------------------------------------

  String get _headerSub {
    if (_busy) return 'Đang quét $_target …';
    final scan = _lastScan;
    if (_scanned && scan != null) {
      return 'Mạng $_target • ${scan.found} máy • '
          '${scan.elapsedS.toStringAsFixed(1)} giây';
    }
    return 'Mạng $_target';
  }

  Widget _header() {
    final ok = _scanned ? fleetStatusCount(_records, 'OK') : null;
    final check = _scanned ? fleetStatusCount(_records, 'CHECK') : null;
    final error = _scanned ? fleetStatusCount(_records, 'ERROR') : null;
    final maxTemp = fleetMaxTempC(_records);
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: BeeSkyColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                'Máy đào',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
              ),
              // Scoped to a group: the header names it (the scan
              // bar's "Quét ngay" then runs AS a group scan).
              if (_activeGroup != null) ...[
                const SizedBox(width: 10),
                _chip('Nhóm: ${_activeGroup!.name}'),
              ],
            ],
          ),
          const SizedBox(height: 3),
          Text(
            _headerSub,
            style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _chip(_scanned ? 'Tổng ${_records.length} máy' : 'Tổng — máy'),
              const SizedBox(width: 8),
              _chip('OK ${ok ?? '—'}', dot: BeeSkyColors.ok),
              const SizedBox(width: 8),
              _chip('Cần kiểm tra ${check ?? '—'}', dot: BeeSkyColors.warn),
              const SizedBox(width: 8),
              _chip('Lỗi ${error ?? '—'}', dot: BeeSkyColors.bad),
              const SizedBox(width: 8),
              Flexible(
                child: _chip(
                  _scanned ? fleetRateTotalsText(_records) : 'Hashrate —',
                  shrink: true,
                ),
              ),
              const SizedBox(width: 8),
              _chip(
                maxTemp == null
                    ? 'Max — °C'
                    : 'Max ${maxTemp.toStringAsFixed(0)} °C',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _chip(String text, {Color? dot, bool shrink = false}) {
    final label = Text(
      text,
      style: const TextStyle(fontSize: 12),
      overflow: TextOverflow.ellipsis,
      softWrap: false,
    );
    return Container(
      height: 26,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: BeeSkyColors.ghostFill,
        border: Border.all(color: BeeSkyColors.glassBorder),
        borderRadius: BorderRadius.circular(radiusPill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (dot != null) ...[
            Container(
              width: 7,
              height: 7,
              decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
            ),
            const SizedBox(width: 6),
          ],
          if (shrink) Flexible(child: label) else label,
        ],
      ),
    );
  }

  // ------------------------------------------------------------------
  // Scan bar: one slim row, wraps when the window is narrow
  // ------------------------------------------------------------------

  static final ButtonStyle _scanBtnStyle = FilledButton.styleFrom(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
    textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
  );

  static final ButtonStyle _ghostBtnStyle = OutlinedButton.styleFrom(
    backgroundColor: BeeSkyColors.ghostFill,
    foregroundColor: BeeSkyColors.text,
    side: const BorderSide(color: BeeSkyColors.glassBorder),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(radiusWidget),
    ),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    textStyle: const TextStyle(fontSize: 13),
  );

  Widget _scanBar() {
    const fieldPad = EdgeInsets.symmetric(horizontal: 12, vertical: 9);
    // The prototype draws the scan bar as its own slim card; the fields
    // carry hints instead of floating labels (the values — a subnet,
    // "root" — speak for themselves).
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: BeeSkyColors.panel,
          border: Border.all(color: BeeSkyColors.border),
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        child: Wrap(
          spacing: 10,
          runSpacing: 10,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            SizedBox(
              width: 300,
              child: TextField(
                controller: _targetCtrl,
                decoration: const InputDecoration(
                  hintText: 'Mục tiêu: 192.168.1.0/24, 192.168.0.10-60, …',
                  contentPadding: fieldPad,
                ),
              ),
            ),
            FilledButton.icon(
              onPressed: _busy ? null : _runScan,
              icon: const Icon(Icons.radar, size: 17),
              label: const Text('Quét ngay'),
              style: _scanBtnStyle,
            ),
            // Saved credential sets live behind this one button now
            // (v0.23): the fleet has many machine lines with many
            // logins — a single user/password pair is not enough.
            OutlinedButton.icon(
              onPressed: _busy ? null : _editCreds,
              icon: const Icon(Icons.key, size: 16),
              label: Text('Tài khoản: ${_creds.length} bộ'),
              style: _ghostBtnStyle,
            ),
            OutlinedButton(
              onPressed: _busy ? null : _exportTickets,
              style: _ghostBtnStyle,
              child: const Text('Xuất phiếu sửa'),
            ),
          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------------
  // Content: the table is the screen; detail is a side panel
  // ------------------------------------------------------------------

  Widget _content() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(child: _tableCard()),
          if (_selected != null) ...[
            const SizedBox(width: 14),
            SizedBox(width: 300, child: _detailPanel()),
          ],
        ],
      ),
    );
  }

  Widget _statusLine() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 0, 18, 10),
      child: Text(
        _status,
        style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        overflow: TextOverflow.ellipsis,
      ),
    );
  }

  // ------------------------------------------------------------------
  // Groups view: header chips + group cards (the HashCore home)
  // ------------------------------------------------------------------

  Widget _groupsHeader() {
    final scannedCount = _groups.where((g) => !g.isNew).length;
    final totalErrors = _groups.fold<int>(
      0,
      (sum, g) => sum + (g.lastScan?.error ?? 0),
    );
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: BeeSkyColors.border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Nhóm mạng',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                ),
              ),
              FilledButton.icon(
                onPressed: _busy ? null : () => _editGroup(),
                icon: const Icon(Icons.add, size: 17),
                label: const Text('Thêm nhóm'),
                style: _scanBtnStyle,
              ),
            ],
          ),
          const SizedBox(height: 3),
          const Text(
            'Mỗi nhóm là một dải mạng của trại, có tài khoản riêng '
            'và lịch tự quét riêng.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _chip('Tổng ${_groups.length} nhóm'),
              const SizedBox(width: 8),
              _chip('Đã quét $scannedCount'),
              const SizedBox(width: 8),
              _chip('Lỗi $totalErrors', dot: BeeSkyColors.bad),
            ],
          ),
        ],
      ),
    );
  }

  Widget _groupsContent() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
      child: _groups.isEmpty
          ? _groupsEmptyState()
          : ListView.builder(
              itemCount: _groups.length,
              itemBuilder: (context, i) => _groupCard(_groups[i]),
            ),
    );
  }

  Widget _groupsEmptyState() {
    // HashCore's empty state mirrored: icon + line + the create
    // action, inside a card — never a blank screen.
    return GlassCard(
      padding: EdgeInsets.zero,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.device_hub, size: 64, color: BeeSkyColors.muted),
            const SizedBox(height: 14),
            const Text(
              'Chưa có nhóm mạng nào',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            const Text(
              'Tạo nhóm để gom các dải IP của trại — mỗi nhóm quét '
              'và đăng nhập theo cách riêng của nó.',
              style: TextStyle(color: BeeSkyColors.muted),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => _editGroup(),
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Thêm nhóm'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _newTag() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: BeeSkyColors.accent.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(radiusPill),
      ),
      child: const Text(
        'MỚI',
        style: TextStyle(
          color: BeeSkyColors.accent,
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
        ),
      ),
    );
  }

  Widget _groupCard(NetGroup group) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassCard(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          group.name,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      // HashCore's "new" tag for a never-scanned group.
                      if (group.isNew) ...[
                        const SizedBox(width: 8),
                        _newTag(),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    group.targets,
                    style: const TextStyle(
                      color: BeeSkyColors.muted,
                      fontSize: 12,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    group.lastScan == null
                        ? 'Chưa quét'
                        : group.lastScan!.summaryText,
                    style: const TextStyle(fontSize: 12),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    group.autoscanText,
                    style: const TextStyle(
                      color: BeeSkyColors.muted,
                      fontSize: 12,
                    ),
                  ),
                  if (group.creds.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      'Tài khoản riêng: ${group.creds.length} bộ',
                      style: const TextStyle(
                        color: BeeSkyColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                FilledButton.icon(
                  onPressed: _busy ? null : () => _scanGroup(group),
                  icon: const Icon(Icons.radar, size: 15),
                  label: const Text('Quét nhóm'),
                  style: _scanBtnStyle,
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    OutlinedButton(
                      onPressed: _busy
                          ? null
                          : () => _editGroup(existing: group),
                      style: _ghostBtnStyle,
                      child: const Text('Sửa'),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 19),
                      tooltip: 'Xóa nhóm',
                      onPressed:
                          _busy ? null : () => _deleteGroup(group),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _tableCard() {
    return GlassCard(
      padding: EdgeInsets.zero,
      child: Container(
        decoration: BoxDecoration(
          color: BeeSkyColors.tableWell,
          borderRadius: BorderRadius.circular(radiusCard),
        ),
        child: !_scanned
            ? _emptyState()
            : _records.isEmpty
                ? _noResultsState()
                : Column(
                    children: [
                      _tableHeader(),
                      const Divider(height: 1),
                      Expanded(
                        child: ListView.builder(
                          itemCount: _records.length,
                          itemBuilder: (context, i) =>
                              _tableRow(_records[i], i),
                        ),
                      ),
                    ],
                  ),
      ),
    );
  }

  Widget _emptyState() {
    // The polish detail the owner admired in the Toolkit: a real empty
    // state (icon + line + action), not a blank grid — it lives inside
    // the table area so the table stays the screen.
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.radar, size: 64, color: BeeSkyColors.muted),
          const SizedBox(height: 14),
          const Text(
            'Chưa quét',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          const Text(
            'Bấm Quét ngay để tìm máy đào trong mạng của bạn.',
            style: TextStyle(color: BeeSkyColors.muted),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _busy ? null : _runScan,
            icon: const Icon(Icons.radar, size: 18),
            label: const Text('Quét ngay'),
          ),
        ],
      ),
    );
  }

  Widget _noResultsState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.search_off, size: 56, color: BeeSkyColors.muted),
          const SizedBox(height: 12),
          const Text(
            'Không tìm thấy máy nào',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            'Kiểm tra lại dải quét: $_target',
            style: const TextStyle(color: BeeSkyColors.muted),
          ),
        ],
      ),
    );
  }

  static const _columns = <(String, int)>[
    ('IP', 3),
    ('MODEL', 4),
    ('NGUỒN', 3),
    ('HASHRATE', 3),
    ('CHIP', 2),
    // NHIỆT carries EVERY board's temp since the owner's follow-up
    // rule, so it gets a wider share; QUẠT gives one back (its long
    // strings ellipsised anyway).
    ('NHIỆT', 3),
    ('QUẠT', 3),
    ('TRẠNG THÁI', 2),
  ];

  Widget _tableHeader() {
    return Container(
      color: BeeSkyColors.tableHeading,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      child: Row(
        children: [
          for (final (label, flex) in _columns)
            Expanded(
              flex: flex,
              child: Text(
                label,
                style: const TextStyle(
                  color: BeeSkyColors.muted,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.1,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _tableRow(MinerRecord rec, int i) {
    final selected = _selected?.ip == rec.ip;
    final bg = selected
        ? BeeSkyColors.selectBg
        : (i.isOdd ? BeeSkyColors.tableZebra : Colors.transparent);
    // Row clicks are read at the pointer level (v0.23): every
    // pointer-down selects instantly, and a second down on the
    // same row inside the double-click window opens the miner's
    // web admin. (A GestureDetector double-tap would hold the
    // single click back until the window expires — the lag BTC
    // Tools does not have.) The InkWell keeps the ripple and the
    // keyboard/accessibility activation path.
    return Listener(
      onPointerDown: (_) => _rowPointerDown(rec),
      child: InkWell(
        onTap: () => setState(() => _selected = rec),
        child: Container(
        decoration: BoxDecoration(
          color: bg,
          // The prototype marks the selected row with a 3px accent bar.
          border: selected
              ? const Border(
                  left: BorderSide(color: BeeSkyColors.accent, width: 3),
                )
              : const Border(
                  left: BorderSide(color: Colors.transparent, width: 3),
                ),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        child: Row(
          children: [
            _cell(rec.ip, 3),
            _cell(rec.model, 4),
            _cell(rec.sourceLabel, 3),
            _cell(rec.rateText, 3),
            _cell(rec.chipsText, 2),
            _tempCell(rec),
            _cell(rec.fansText, 3),
            Expanded(flex: 2, child: _statusChip(rec)),
          ],
        ),
        ),
      ),
    );
  }

  /// Pointer-level row click (v0.23): select on every down; a
  /// second down on the SAME row within the double-click window
  /// also opens that miner's web admin in the default browser.
  String? _lastRowIp;
  DateTime? _lastRowTapAt;

  void _rowPointerDown(MinerRecord rec) {
    final now = DateTime.now();
    final isDouble = _lastRowIp == rec.ip &&
        _lastRowTapAt != null &&
        now.difference(_lastRowTapAt!) < const Duration(milliseconds: 400);
    _lastRowIp = rec.ip;
    _lastRowTapAt = now;
    setState(() => _selected = rec);
    if (isDouble) _openMinerWeb(rec);
  }

  Widget _cell(String text, int flex) {
    return Expanded(
      flex: flex,
      child: Text(
        text,
        style: const TextStyle(fontSize: 13),
        overflow: TextOverflow.ellipsis,
      ),
    );
  }

  /// The NHIỆT cell shows EVERY hashboard's temperature, not only the
  /// max (owner rule added 2026-11-11 after the prototype review:
  /// "sao hok hiện hết 3 hoặc 4 hash board, cái nào nóng quá thì đỏ
  /// lên"). Values render compactly in chain order; a board at/over
  /// the core's 85 °C limit (models.tempLimitC — the threshold behind
  /// the OVER_TEMP problem) turns bold red on a soft red pill, the
  /// rest stay muted. A record with no per-chain temps falls back to
  /// the single max temp, and an unreachable row keeps "—".
  Widget _tempCell(MinerRecord rec) {
    final shown = rec.chains.where((c) => c.tempC != null).toList();
    if (shown.isEmpty) return _cell(rec.tempText, 3);
    return Expanded(
      flex: 3,
      // Scale down rather than overflow when a narrow window (detail
      // panel open) squeezes the column — the temps stay on one line.
      child: FittedBox(
        fit: BoxFit.scaleDown,
        alignment: Alignment.centerLeft,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (var i = 0; i < shown.length; i++) ...[
              if (i > 0) const SizedBox(width: 6),
              _boardTemp(shown[i]),
            ],
          ],
        ),
      ),
    );
  }

  Widget _boardTemp(ChainInfo chain) {
    final label = '${chain.tempC!.toStringAsFixed(0)}°';
    if (!chain.isHot) {
      return Text(
        label,
        style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
      );
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
      decoration: BoxDecoration(
        color: BeeSkyColors.hotTemp.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(5),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: BeeSkyColors.hotTemp,
          fontSize: 12.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }

  Widget _statusChip(MinerRecord rec) {
    final (bg, fg) = switch (rec.statusLabel) {
      'OK' => (const Color(0x2634D399), BeeSkyColors.ok),
      'ERROR' => (const Color(0x26F87171), BeeSkyColors.bad),
      _ => (const Color(0x26FBBF24), BeeSkyColors.warn),
    };
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(radiusPill),
        ),
        child: Text(
          rec.statusLabel,
          style: TextStyle(
            color: fg,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }

  // ------------------------------------------------------------------
  // Detail panel (only present while a row is selected)
  // ------------------------------------------------------------------

  Widget _detailPanel() {
    final rec = _selected!;
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    rec.model,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  tooltip: 'Đóng chi tiết',
                  visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(
                    minWidth: 28,
                    minHeight: 28,
                  ),
                  onPressed: () => setState(() => _selected = null),
                ),
              ],
            ),
            Text(
              '${rec.ip} • ${rec.sourceLabel}',
              style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
            const SizedBox(height: 12),
            _kv('Hashrate', rec.rateText),
            _kv('Chip sống', '${rec.chipsAlive} / ${rec.chipsTotal}'),
            _kv(
              'Nhiệt độ',
              rec.maxTempC == null
                  ? '—'
                  : '${rec.maxTempC!.toStringAsFixed(0)} °C',
            ),
            _kv('Quạt', rec.fansRpm.isEmpty ? '—' : '${rec.fansText} RPM'),
            _kv(
              'Trạng thái',
              rec.statusLabel,
              valueColor: rec.statusLabel == 'OK'
                  ? BeeSkyColors.ok
                  : rec.statusLabel == 'ERROR'
                      ? BeeSkyColors.bad
                      : BeeSkyColors.warn,
            ),
            // Which saved login authenticated to this machine
            // (v0.23) — only present when a creds-file set won.
            if (rec.credLabel != null) _kv('Đăng nhập', rec.credLabel!),
            const SizedBox(height: 4),
            if (rec.issues.isEmpty)
              const Text(
                'Không phát hiện vấn đề.',
                style: TextStyle(color: BeeSkyColors.muted),
              )
            else
              for (final p in rec.issues) _issueBox(p),
            if (rec.chains.isNotEmpty) ...[
              const SizedBox(height: 8),
              // One line per board the machine ACTUALLY reports
              // (len(chains) — never an assumed 3), each with that
              // board's OWN temperature when the record carries one
              // (steering 2026-11-11: "nhiệt độ máy có 4 hashboard
              // thì sao" — a 4-board machine shows 4 lines).
              for (final c in rec.chains)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  // A hot board's line (>= the 85 °C limit) takes the
                  // same red treatment as its pill in the table's
                  // NHIỆT cell, so table and panel agree.
                  child: Text(
                    'Board ${c.index + 1}: ${c.chipsAlive}/${c.chipsTotal} chip'
                    '${c.tempC == null ? '' : ' • ${c.tempC!.toStringAsFixed(0)}°C'}',
                    style: TextStyle(
                      color:
                          c.isHot ? BeeSkyColors.hotTemp : BeeSkyColors.muted,
                      fontSize: 12,
                      fontWeight:
                          c.isHot ? FontWeight.w700 : FontWeight.w400,
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  /// One diagnosed problem as a tinted box (the prototype's treatment):
  /// the code on its own line, the human detail underneath.
  Widget _issueBox(Problem p) {
    final isError = p.severity == 'error';
    final fg = isError ? BeeSkyColors.bad : BeeSkyColors.warn;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: fg.withValues(alpha: 0.08),
        border: Border.all(color: fg.withValues(alpha: 0.35)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '[${p.code}]',
            style: TextStyle(
              color: fg,
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.4,
            ),
          ),
          const SizedBox(height: 4),
          Text(p.detail, style: const TextStyle(fontSize: 12, height: 1.45)),
        ],
      ),
    );
  }

  Widget _kv(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 86,
            child: Text(
              label,
              style: const TextStyle(color: BeeSkyColors.muted, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: valueColor ?? BeeSkyColors.text,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
