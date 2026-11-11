import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'creds.dart';
import 'detail.dart';
import 'grid.dart';
import 'grid_dialogs.dart';
import 'groups.dart';
import 'models.dart';
import 'ops.dart';
import 'ops_dialogs.dart';
import 'sidecar.dart';
import 'theme.dart';

/// The two content views: the app OPENS on network groups (the
/// HashCore Toolkit's home screen, v0.24); the miners table is the
/// per-group / ad-hoc scan view behind it.
enum _View { groups, miners }

/// Grid hotkey intents (v0.25) — the Flutter mirror of HashCore's
/// `package:toolkit/hot_keys/intents_and_actions/` layer.
class _SelectAllIntent extends Intent {
  const _SelectAllIntent();
}

class _SearchIntent extends Intent {
  const _SearchIntent();
}

class _RescanIntent extends Intent {
  const _RescanIntent();
}

class _ClearGridIntent extends Intent {
  const _ClearGridIntent();
}

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

  /// Grid-store override (tests point it at a temp dir); the real
  /// app uses [GridStore.appDefault] — beesky-grid.json beside the
  /// executable, the same folder as the other stores.
  final GridStore? gridStore;

  /// Ops-history override (tests point it at a temp dir); the real
  /// app uses [OpsHistoryStore.appDefault] — beesky-ops-history.json
  /// beside the executable (v0.26).
  final OpsHistoryStore? opsStore;

  /// Ops-files override (job file + export dir); defaults to
  /// [OpsFiles.appDefault] (beside the executable).
  final OpsFiles? opsFiles;

  /// Chart-history override (tests point it at a temp dir); the
  /// real app uses [HistoryStore.appDefault] — beesky-history.json
  /// beside the executable (v0.27).
  final HistoryStore? historyStore;

  /// Device-notes override (tests point it at a temp dir); the
  /// real app uses [NoteStore.appDefault] — beesky-notes.json
  /// beside the executable (v0.27).
  final NoteStore? noteStore;

  /// Row double-click opener override (tests record the URL instead
  /// of launching a browser); defaults to [openUrlInBrowser].
  final Future<void> Function(String url)? urlOpener;

  const HomePage({
    super.key,
    required this.bridge,
    this.credStore,
    this.groupStore,
    this.gridStore,
    this.opsStore,
    this.opsFiles,
    this.historyStore,
    this.noteStore,
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

  // Operations (v0.26): the persistent task history (written when
  // a task STARTS, updated when it lands) and the live run's state
  // — progress counts from the streamed per-device events.
  late final OpsHistoryStore _opsStore =
      widget.opsStore ?? OpsHistoryStore.appDefault();
  late final OpsFiles _opsFiles = widget.opsFiles ?? OpsFiles.appDefault();
  List<OpsTask> _opsHistory = const [];
  OpsTask? _runningTask;
  OpsRun? _opsRun;
  StreamSubscription<OpsEvent>? _opsSub;
  List<OpsDeviceResult> _opsResults = const [];
  String? _opsCurrentIp;

  // Data grid (v0.25): the persisted view configuration, the
  // session filter/search state, and the SELECTION MODEL the
  // v0.26 Operations bar will consume (grid.dart MinerSelection).
  late final GridStore _gridStore = widget.gridStore ?? GridStore.appDefault();
  GridConfig _grid = GridConfig();
  final MinerSelection _selection = MinerSelection();
  List<GridFilter> _filters = const [];
  final _searchCtrl = TextEditingController();
  final _searchFocus = FocusNode();
  final _gridHScroll = ScrollController();

  // Device detail (v0.27): the detail panel's tabs, the LOCAL
  // chart history (one sample per device per finished scan), the
  // per-device notes, and the on-demand inspect cache — one
  // deep fetch per device per session, keyed by IP.
  late final HistoryStore _historyStore =
      widget.historyStore ?? HistoryStore.appDefault();
  late final NoteStore _noteStore =
      widget.noteStore ?? NoteStore.appDefault();
  Map<String, List<HistorySample>> _history = {};
  Map<String, String> _notes = {};
  int _detailTab = 0;
  final Map<String, InspectResult> _inspectCache = {};
  final Set<String> _inspectLoading = {};
  final _noteCtrl = TextEditingController();
  String? _noteOwnerKey;

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
    _loadGrid();
    _loadOpsHistory();
    _loadHistory();
    _loadNotes();
    _autoscanTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _tickAutoscan(),
    );
  }

  @override
  void dispose() {
    _opsSub?.cancel();
    _opsRun?.stop();
    _autoscanTimer?.cancel();
    _targetCtrl.dispose();
    _searchCtrl.dispose();
    _searchFocus.dispose();
    _gridHScroll.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    var loaded = await _historyStore.load();
    if (!mounted) return;
    // The mock shell seeds demo samples so the chart tab renders
    // without six real scans (detail.dart demoHistory).
    if (loaded.isEmpty && widget.bridge.isMock) {
      loaded = demoHistory(DateTime.now());
    }
    setState(() => _history = loaded);
  }

  Future<void> _loadNotes() async {
    final loaded = await _noteStore.load();
    if (!mounted) return;
    setState(() => _notes = loaded);
  }

  Future<void> _saveHistory() async {
    try {
      await _historyStore.save(_history);
    } on FileSystemException {
      // History stays in memory for this session.
    }
  }

  /// One sample per LIVE device per finished scan (a FETCH_ERROR
  /// record is a failed read, not a sample of the machine's
  /// state). Called BEFORE the result lands on the table so the
  /// chart tab already includes this pass when it renders.
  void _appendHistorySamples(List<MinerRecord> records) {
    final live = records.where((r) => !r.hasFetchError).toList();
    if (live.isEmpty) return;
    final now = DateTime.now();
    for (final rec in live) {
      appendHistorySample(_history, rec, now);
    }
    _saveHistory();
  }

  Future<void> _loadGrid() async {
    final (config, _) = await _gridStore.load();
    if (!mounted) return;
    setState(() => _grid = config);
  }

  /// Persist the grid config after a change (fire-and-forget like
  /// group saves: a refused write never breaks the view).
  Future<void> _saveGrid() async {
    try {
      await _gridStore.save(_grid);
    } on FileSystemException {
      // Settings stay in memory for this session.
    }
  }

  /// The current pipeline result — rendered by the table, the
  /// heat-grid and the result-count line alike.
  GridViewResult get _gridView => applyGridView(
        _records,
        search: _searchCtrl.text,
        filters: _filters,
        selection: _selection,
        sort: _grid.sort,
        groupBy: _grid.groupBy,
      );

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
    _appendHistorySamples(result.records);
    setState(() {
      _records = result.records;
      _lastScan = result;
      _scanned = true;
      _selected = result.records.isEmpty ? null : result.records.first;
      // Checkbox selections for machines that left the fleet are
      // dropped (the selection model stays honest across rescans).
      _selection.retainOnly(result.records);
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

  // ------------------------------------------------------------------
  // Operations (v0.26): the selection becomes work — run one task
  // type over the selected miners through the core runner, stream
  // its progress into the bar, and land it in the history. Only
  // actions with a real core primitive exist (docs/operations-
  // mapping.md §3); the rest are named gaps, not fake buttons.
  // ------------------------------------------------------------------

  Future<void> _loadOpsHistory() async {
    final tasks = await _opsStore.load();
    if (!mounted) return;
    setState(() => _opsHistory = tasks);
  }

  Future<void> _saveOpsHistory() async {
    try {
      await _opsStore.save(_opsHistory);
    } on FileSystemException {
      // History stays in memory for this session.
    }
  }

  /// The task's targets: the selected records, in table order.
  List<String> _selectedTargets() => [
        for (final rec in _records)
          if (_selection.isSelected(rec.ip)) rec.ip,
      ];

  Future<void> _startOps(
    OpsTaskType type, {
    Map<String, dynamic>? payload,
  }) async {
    if (_runningTask != null || _busy) return;
    final targets = _selectedTargets();
    if (targets.isEmpty) return;
    if (type.needsConfirm) {
      final confirmed = await showOpsConfirmDialog(context, type, targets);
      if (!confirmed || !mounted) return;
    }
    final now = DateTime.now();
    final task = OpsTask(
      id: 'ops-${now.millisecondsSinceEpoch}',
      type: type,
      createdAt: now,
      finishedAt: null,
      status: OpsStatus.running,
      targets: targets,
      results: const [],
    );
    setState(() {
      _runningTask = task;
      _opsResults = const [];
      _opsCurrentIp = null;
      _opsHistory = [..._opsHistory, task];
      _status = '${type.label}: đang chạy trên ${targets.length} máy…';
    });
    _saveOpsHistory();

    final credsFile = await _credsFileForScan();
    if (!mounted) return;
    final job = <String, dynamic>{
      'type': type.wire,
      'targets': targets,
      if (payload != null) 'payload': payload,
      // In a group's scope the job resolves creds through the
      // group's own sets first (v0.24 layering), exactly like the
      // group scan the user is looking at.
      if (_activeGroup != null) 'group': _activeGroup!.name,
      if (_activeGroup != null && _groupsFile != null)
        'groups_file': _groupsFile!.path,
      if (credsFile != null) 'creds_file': credsFile,
    };
    try {
      final run = await widget.bridge.startOps(job);
      if (!mounted) {
        run.stop();
        return;
      }
      _opsRun = run;
      _opsSub = run.events.listen(_onOpsEvent, onError: (_) {});
      final summary = await run.summary;
      if (!mounted) return;
      _finishOps(summary);
    } on SidecarException catch (e) {
      if (!mounted) return;
      _finishOpsWithError('$e');
    }
  }

  void _onOpsEvent(OpsEvent event) {
    if (!mounted || event.kind != 'result' || event.ip == null) return;
    setState(() {
      _opsCurrentIp = event.ip;
      _opsResults = [
        ..._opsResults,
        OpsDeviceResult(
          ip: event.ip!,
          ok: event.ok ?? false,
          message: event.message ?? '',
        ),
      ];
      // A rescan result carries the fresh record: the row updates
      // in place (HashCore's refresh lands on the list the same
      // way), and the detail panel follows if it shows this miner.
      final fresh = event.record;
      if (fresh != null) {
        final idx = _records.indexWhere((r) => r.ip == fresh.ip);
        if (idx >= 0) {
          final next = [..._records];
          next[idx] = fresh;
          _records = next;
          if (_selected?.ip == fresh.ip) _selected = fresh;
        }
      }
    });
  }

  /// Land a finished run into the history: received results plus,
  /// for a stopped task, a cancelled marker per unstarted device
  /// (the core emits no event for those; the summary counts them).
  void _finishOps(OpsSummary summary) {
    final task = _runningTask;
    if (task == null) return;
    final results = [..._opsResults];
    if (summary.cancelled > 0) {
      final done = results.map((r) => r.ip).toSet();
      for (final ip in task.targets) {
        if (!done.contains(ip)) {
          results.add(OpsDeviceResult(
            ip: ip,
            ok: false,
            message: 'Đã hủy trước khi chạy',
            cancelled: true,
          ));
        }
      }
    }
    final landed = task.copyWith(
      finishedAt: DateTime.now(),
      status: summary.status,
      results: results,
    );
    setState(() {
      _opsHistory = [
        for (final t in _opsHistory) t.id == landed.id ? landed : t,
      ];
      _runningTask = null;
      _opsRun = null;
      _opsCurrentIp = null;
      _status = '${task.type.label}: xong ${summary.ok} · '
          'lỗi ${summary.failed}'
          '${summary.cancelled > 0 ? ' · đã hủy ${summary.cancelled}' : ''} '
          '(${task.total} máy).';
    });
    _opsSub?.cancel();
    _opsSub = null;
    _saveOpsHistory();
  }

  void _finishOpsWithError(String message) {
    final task = _runningTask;
    if (task == null) return;
    final landed = task.copyWith(
      finishedAt: DateTime.now(),
      status: OpsStatus.error,
      results: [
        for (final ip in task.targets)
          OpsDeviceResult(ip: ip, ok: false, message: message),
      ],
    );
    setState(() {
      _opsHistory = [
        for (final t in _opsHistory) t.id == landed.id ? landed : t,
      ];
      _runningTask = null;
      _opsRun = null;
      _opsCurrentIp = null;
      _status = '${task.type.label}: lỗi — $message';
    });
    _saveOpsHistory();
    _showSnack('${task.type.label}: lỗi — $message');
  }

  Future<void> _stopOps() async {
    await _opsRun?.stop();
    // The summary future now completes (the bridge synthesises
    // one when the kill leaves no summary line) and _finishOps
    // lands the task as cancelled.
  }

  /// "Xuất danh sách" — app-side (a BeeSky addition, not a
  /// HashCore port): the selected records as a JSON file, plus a
  /// history entry like any other task.
  Future<void> _exportSelection() async {
    if (_runningTask != null) return;
    final selected = [
      for (final rec in _records)
        if (_selection.isSelected(rec.ip)) rec,
    ];
    if (selected.isEmpty) return;
    String two(int v) => v.toString().padLeft(2, '0');
    final now = DateTime.now();
    final stamp = '${now.year}${two(now.month)}${two(now.day)}-'
        '${two(now.hour)}${two(now.minute)}${two(now.second)}';
    final dir = _opsFiles.exportDir();
    final file = File(
      '${dir.path}${Platform.pathSeparator}beesky-export-$stamp.json',
    );
    try {
      file.writeAsStringSync(
        const JsonEncoder.withIndent('  ')
            .convert(selected.map((r) => r.toJson()).toList()),
      );
    } on FileSystemException catch (e) {
      _showSnack('Xuất danh sách thất bại: $e');
      return;
    }
    final task = OpsTask(
      id: 'ops-${now.millisecondsSinceEpoch}',
      type: OpsTaskType.export,
      createdAt: now,
      finishedAt: now,
      status: OpsStatus.success,
      targets: [for (final r in selected) r.ip],
      results: [
        for (final r in selected)
          OpsDeviceResult(
            ip: r.ip,
            ok: true,
            message: 'Đã xuất vào ${file.path}',
          ),
      ],
    );
    setState(() {
      _opsHistory = [..._opsHistory, task];
      _status = 'Đã xuất danh sách ${selected.length} máy vào: ${file.path}';
    });
    _saveOpsHistory();
    _showSnack('Đã xuất danh sách vào: ${file.path}');
  }

  Future<void> _openOpsHistory() async {
    await showDialog<void>(
      context: context,
      builder: (_) => OpsHistoryDialog(
        tasks: _opsHistory,
        onDelete: (task) {
          setState(() {
            _opsHistory = [
              for (final t in _opsHistory)
                if (t.id != task.id) t,
            ];
          });
          _saveOpsHistory();
        },
        onClearAll: () {
          setState(() => _opsHistory = const []);
          _saveOpsHistory();
        },
        onIsolateErrors: (ips) {
          setState(() {
            _selection.selectedIps
              ..clear()
              ..addAll(ips);
            _selection.isolate = IsolateMode.errors;
          });
        },
      ),
    );
  }

  /// The task progress bar (HashCore's header progress:
  /// "{task} progress: N addresses" + Stop).
  Widget _opsProgressBar() {
    final task = _runningTask!;
    final done = _opsResults.length;
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
      child: Row(
        children: [
          Icon(task.type.icon, size: 16, color: BeeSkyColors.accent),
          const SizedBox(width: 8),
          Text(
            '${task.type.label}: $done/${task.total} địa chỉ',
            style: const TextStyle(fontSize: 12.5),
          ),
          if (_opsCurrentIp != null) ...[
            const SizedBox(width: 8),
            Text(
              '· đang xử lý $_opsCurrentIp',
              style: const TextStyle(
                  color: BeeSkyColors.muted, fontSize: 12.5),
            ),
          ],
          const SizedBox(width: 12),
          Expanded(
            child: LinearProgressIndicator(
              value: task.total == 0 ? null : done / task.total,
              minHeight: 4,
              backgroundColor: BeeSkyColors.panel2,
              color: BeeSkyColors.accent,
            ),
          ),
          const SizedBox(width: 12),
          _miniButton('Dừng', _stopOps),
        ],
      ),
    );
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

  // ------------------------------------------------------------------
  // Data-grid actions (v0.25): columns dialog, filter dialog, sort,
  // isolate, and the hotkey layer (HashCore's own architecture is
  // intents+actions too; BeeSky's key bindings are its own —
  // docs/grid-mapping.md §10).
  // ------------------------------------------------------------------

  Future<void> _editColumns() async {
    final result = await showGridColumnsDialog(context, _grid);
    if (result == null || !mounted) return;
    setState(() {
      _grid = result;
      // Editing columns IS the Custom mode's content; if the user
      // was looking at a fixed set, switch so the edit is visible.
      if (_grid.viewMode != GridViewMode.custom) {
        _grid.viewMode = GridViewMode.custom;
      }
      _status = 'Đã lưu cấu hình cột (chế độ Tùy chỉnh).';
    });
    await _saveGrid();
  }

  Future<void> _editFilters() async {
    final result = await showGridFilterDialog(
      context,
      filters: _filters,
      presets: _grid.filterPresets,
    );
    if (result == null || !mounted) return;
    setState(() {
      _filters = result.filters;
      _grid.filterPresets = result.presets;
      _status = result.filters.isEmpty
          ? 'Đã xóa bộ lọc.'
          : 'Đang lọc theo ${result.filters.length} điều kiện.';
    });
    await _saveGrid();
  }

  /// Esc / "Xóa bộ lọc": search text, filter rows, isolate and the
  /// checkbox selection all clear; the detail selection stays.
  void _clearGridModifiers() {
    setState(() {
      _searchCtrl.clear();
      _filters = const [];
      _selection.clear();
      _status = 'Đã xóa tìm kiếm, bộ lọc và vùng chọn.';
    });
  }

  void _toggleSort(String columnId) {
    setState(() {
      if (_grid.sort.field == columnId) {
        _grid.sort.ascending = !_grid.sort.ascending;
      } else {
        _grid.sort = GridSort(field: columnId, ascending: true);
      }
    });
    _saveGrid();
  }

  void _toggleIsolate(IsolateMode mode) {
    setState(() {
      _selection.isolate = _selection.isolate == mode ? IsolateMode.none : mode;
    });
  }

  /// True while a text field owns the keyboard — grid hotkeys step
  /// aside there (Ctrl+A in the target field selects TEXT there).
  bool get _editingText {
    final focus = FocusManager.instance.primaryFocus;
    if (focus == null) return false;
    var editing = false;
    focus.context?.visitAncestorElements((el) {
      if (el.widget is EditableText) editing = true;
      return !editing;
    });
    return editing;
  }

  void _hotSelectAll() {
    if (_editingText) return;
    setState(() => _selection.selectAll(_gridView.visible));
  }

  void _hotSearch() {
    if (_editingText) return;
    _searchFocus.requestFocus();
  }

  void _hotRescan() {
    if (_editingText) return;
    _runScan();
  }

  void _hotClear() {
    if (_editingText) return;
    _clearGridModifiers();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _sidebar(),
          Expanded(
            child: _view == _View.groups ? _groupsColumn() : _minersColumn(),
          ),
        ],
      ),
    );
  }

  Widget _minersColumn() {
    final column = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _header(),
        _scanBar(),
        if (_scanned) _gridToolbar(),
        if (_scanned && _records.isNotEmpty) _selectionBar(),
        if (_runningTask != null) _opsProgressBar(),
        if (_busy) const LinearProgressIndicator(minHeight: 3),
        Expanded(child: _content()),
        _statusLine(),
      ],
    );
    // The grid hotkey layer (v0.25): Ctrl+A select all visible,
    // Ctrl+F focus search, Ctrl+R / F5 rescan, Esc clear modifiers.
    // Handlers step aside while a text field owns the keyboard.
    return Shortcuts(
      shortcuts: const {
        SingleActivator(LogicalKeyboardKey.keyA, control: true):
            _SelectAllIntent(),
        SingleActivator(LogicalKeyboardKey.keyF, control: true):
            _SearchIntent(),
        SingleActivator(LogicalKeyboardKey.keyR, control: true):
            _RescanIntent(),
        SingleActivator(LogicalKeyboardKey.f5): _RescanIntent(),
        SingleActivator(LogicalKeyboardKey.escape): _ClearGridIntent(),
      },
      child: Actions(
        actions: {
          _SelectAllIntent: CallbackAction<_SelectAllIntent>(
            onInvoke: (_) => _hotSelectAll(),
          ),
          _SearchIntent: CallbackAction<_SearchIntent>(
            onInvoke: (_) => _hotSearch(),
          ),
          _RescanIntent: CallbackAction<_RescanIntent>(
            onInvoke: (_) => _hotRescan(),
          ),
          _ClearGridIntent: CallbackAction<_ClearGridIntent>(
            onInvoke: (_) => _hotClear(),
          ),
        },
        child: Focus(autofocus: true, child: column),
      ),
    );
  }

  // ------------------------------------------------------------------
  // Grid toolbar + selection bar (v0.25): search, filter, grouping,
  // data mode, density, columns — HashCore keeps the same controls
  // in the miners-list header (view_control / action_control).
  // ------------------------------------------------------------------

  Widget _gridToolbar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 0),
      child: Wrap(
        spacing: 10,
        runSpacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          SizedBox(
            width: 230,
            child: TextField(
              controller: _searchCtrl,
              focusNode: _searchFocus,
              decoration: const InputDecoration(
                hintText: 'Tìm theo IP / MAC, Pool hoặc Worker',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          OutlinedButton.icon(
            onPressed: _busy ? null : _editFilters,
            icon: const Icon(Icons.filter_alt_outlined, size: 16),
            label: Text(
              _filters.isEmpty ? 'Bộ lọc' : 'Bộ lọc (${_filters.length})',
            ),
            style: _ghostBtnStyle,
          ),
          _groupByMenu(),
          _segmented<GridViewMode>(
            value: _grid.viewMode,
            options: const [
              (GridViewMode.metric, 'Số liệu'),
              (GridViewMode.pools, 'Pools'),
              (GridViewMode.custom, 'Tùy chỉnh'),
            ],
            onChanged: (v) {
              setState(() => _grid.viewMode = v);
              _saveGrid();
            },
          ),
          _segmented<GridViewType>(
            value: _grid.viewType,
            options: const [
              (GridViewType.normal, 'Thoải mái'),
              (GridViewType.compact, 'Gọn'),
              (GridViewType.overview, 'Tổng quan'),
            ],
            onChanged: (v) {
              setState(() => _grid.viewType = v);
              _saveGrid();
            },
          ),
          if (_grid.viewType == GridViewType.overview) ...[
            _segmented<OverviewColorMode>(
              value: _grid.overviewColor,
              options: const [
                (OverviewColorMode.temperature, 'Màu: Nhiệt độ'),
                (OverviewColorMode.hashrate, 'Màu: Hashrate'),
              ],
              onChanged: (v) {
                setState(() => _grid.overviewColor = v);
                _saveGrid();
              },
            ),
            _segmented<OverviewCellSize>(
              value: _grid.overviewSize,
              options: const [
                (OverviewCellSize.small, 'Ô S'),
                (OverviewCellSize.medium, 'Ô M'),
                (OverviewCellSize.large, 'Ô L'),
              ],
              onChanged: (v) {
                setState(() => _grid.overviewSize = v);
                _saveGrid();
              },
            ),
          ],
          OutlinedButton.icon(
            onPressed: _busy ? null : _editColumns,
            icon: const Icon(Icons.view_column_outlined, size: 16),
            label: const Text('Cột'),
            style: _ghostBtnStyle,
          ),
          OutlinedButton.icon(
            onPressed: _openOpsHistory,
            icon: const Icon(Icons.history, size: 16),
            label: const Text('Lịch sử tác vụ'),
            style: _ghostBtnStyle,
          ),
        ],
      ),
    );
  }

  Widget _groupByMenu() {
    return PopupMenuButton<GridGroupBy>(
      tooltip: 'Nhóm theo',
      color: BeeSkyColors.panel2,
      initialValue: _grid.groupBy,
      onSelected: (v) {
        setState(() => _grid.groupBy = v);
        _saveGrid();
      },
      itemBuilder: (context) => [
        for (final g in GridGroupBy.values)
          PopupMenuItem(value: g, child: Text('Nhóm: ${g.label}')),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
          color: BeeSkyColors.ghostFill,
          border: Border.all(color: BeeSkyColors.glassBorder),
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.folder_open_outlined, size: 16),
            const SizedBox(width: 6),
            Text(
              'Nhóm: ${_grid.groupBy.label}',
              style: const TextStyle(fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _segmented<T>({
    required T value,
    required List<(T, String)> options,
    required ValueChanged<T> onChanged,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: BeeSkyColors.ghostFill,
        border: Border.all(color: BeeSkyColors.glassBorder),
        borderRadius: BorderRadius.circular(radiusWidget),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final (v, label) in options)
            InkWell(
              onTap: () => onChanged(v),
              borderRadius: BorderRadius.circular(radiusWidget),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: v == value
                      ? BeeSkyColors.accent.withValues(alpha: 0.16)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(radiusWidget),
                ),
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: v == value ? FontWeight.w700 : FontWeight.w400,
                    color:
                        v == value ? BeeSkyColors.accent : BeeSkyColors.muted,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// The selection bar: result count + HashCore's action_control
  /// verbs (Select all / Invert / Isolate) + — since v0.26 — the
  /// OPERATIONS bar proper: the actions that run on the selection
  /// (Quét lại / Khởi động lại / Đổi pool / Xuất danh sách).
  Widget _selectionBar() {
    final view = _gridView;
    final selCount = _selection.selectedIps.length;
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
      child: Wrap(
        spacing: 8,
        runSpacing: 6,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Text(
            'Đang hiển thị ${view.visible.length} / ${view.total} máy',
            style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
          if (selCount > 0)
            _chip('Đã chọn $selCount', dot: BeeSkyColors.accent),
          _miniButton(
            'Chọn tất cả',
            () => setState(() => _selection.selectAll(_gridView.visible)),
          ),
          _miniButton(
            'Đảo chọn',
            () => setState(() => _selection.invert(_records)),
          ),
          _miniToggle(
            'Cô lập: đã chọn',
            _selection.isolate == IsolateMode.selected,
            () => _toggleIsolate(IsolateMode.selected),
          ),
          _miniToggle(
            'Cô lập: lỗi',
            _selection.isolate == IsolateMode.errors,
            () => _toggleIsolate(IsolateMode.errors),
          ),
          if (selCount > 0 ||
              _selection.isolate != IsolateMode.none ||
              _filters.isNotEmpty ||
              _searchCtrl.text.isNotEmpty)
            _miniButton('Xóa lọc / chọn', _clearGridModifiers),
          // The OPERATIONS bar (v0.26): the selection becomes work.
          // Only actions with a real core primitive are offered —
          // the rest of HashCore's 27 types are named gaps in
          // docs/operations-mapping.md, not greyed-out fakes.
          if (selCount > 0) ...[
            const Text(
              'Thao tác:',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
            _miniButton(
              'Quét lại',
              _runningTask == null
                  ? () => _startOps(OpsTaskType.rescan)
                  : null,
            ),
            _miniButton(
              'Khởi động lại',
              _runningTask == null
                  ? () => _startOps(OpsTaskType.reboot)
                  : null,
            ),
            _miniButton(
              'Đổi pool',
              _runningTask == null
                  ? () async {
                      final payload = await showSwitchPoolDialog(context);
                      if (payload != null && mounted) {
                        _startOps(OpsTaskType.switchPool, payload: payload);
                      }
                    }
                  : null,
            ),
            _miniButton(
              'Xuất danh sách',
              _runningTask == null ? _exportSelection : null,
            ),
          ],
        ],
      ),
    );
  }

  Widget _miniButton(String label, VoidCallback? onPressed) {
    return OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        backgroundColor: BeeSkyColors.ghostFill,
        foregroundColor: BeeSkyColors.text,
        side: const BorderSide(color: BeeSkyColors.glassBorder),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        textStyle: const TextStyle(fontSize: 12),
      ),
      child: Text(label),
    );
  }

  Widget _miniToggle(String label, bool active, VoidCallback onPressed) {
    return OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        backgroundColor: active
            ? BeeSkyColors.accent.withValues(alpha: 0.16)
            : BeeSkyColors.ghostFill,
        foregroundColor: active ? BeeSkyColors.accent : BeeSkyColors.text,
        side: BorderSide(
          color: active ? BeeSkyColors.accent : BeeSkyColors.glassBorder,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        textStyle: const TextStyle(fontSize: 12),
      ),
      child: Text(label),
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
                      onPressed:
                          _busy ? null : () => _editGroup(existing: group),
                      style: _ghostBtnStyle,
                      child: const Text('Sửa'),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 19),
                      tooltip: 'Xóa nhóm',
                      onPressed: _busy ? null : () => _deleteGroup(group),
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
                : _gridBody(),
      ),
    );
  }

  /// The grid body: the pipeline result rendered as the table
  /// (two densities), the Overview heat-grid, or the filtered-
  /// empty state (HashCore's `empty_filters_*`: "No results were
  /// found using this filter" + a Clear filters action).
  Widget _gridBody() {
    final view = _gridView;
    if (view.visible.isEmpty) return _filteredEmptyState();
    if (_grid.viewType == GridViewType.overview) return _overviewGrid(view);
    return _tableView(view);
  }

  Widget _filteredEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.filter_alt_off_outlined,
              size: 56, color: BeeSkyColors.muted),
          const SizedBox(height: 12),
          const Text(
            'Không có máy nào khớp',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          const Text(
            'Không có kết quả nào với tìm kiếm / bộ lọc / cô lập '
            'hiện tại. Thử nới hoặc xóa chúng.',
            style: TextStyle(color: BeeSkyColors.muted),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: _clearGridModifiers,
            icon: const Icon(Icons.clear_all, size: 17),
            label: const Text('Xóa bộ lọc'),
            style: _ghostBtnStyle,
          ),
        ],
      ),
    );
  }

  /// Checkbox column width — the selection column is grid chrome,
  /// not one of the configurable columns.
  static const double _checkColW = 38;

  Widget _tableView(GridViewResult view) {
    final columns = _grid.activeColumns;
    // Flatten the presentation: group header rows interleaved with
    // record rows when grouping is on.
    final items = <(MinerGroup?, MinerRecord?, int)>[];
    if (view.isGrouped) {
      var idx = 0;
      for (final g in view.groups) {
        items.add((g, null, -1));
        for (final r in g.records) {
          items.add((null, r, idx++));
        }
      }
    } else {
      for (var i = 0; i < view.visible.length; i++) {
        items.add((null, view.visible[i], i));
      }
    }
    return LayoutBuilder(
      builder: (context, constraints) {
        final totalFlex = columns.fold<int>(0, (s, c) => s + c.flex);
        // Columns keep a readable minimum width; past that the
        // table scrolls horizontally instead of squeezing (a real
        // data grid's answer to 20+ columns).
        var unit = constraints.maxWidth / totalFlex;
        if (unit < 56) unit = 56;
        // +31: the 14px side paddings header and rows share,
        // plus the row's 3px accent border (drawn inside the row,
        // it eats into the cells' width).
        final tableW = _checkColW + unit * totalFlex + 31;
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: tableW,
            child: Column(
              children: [
                _tableHeader(columns, unit, view),
                const Divider(height: 1),
                Expanded(
                  child: ListView.builder(
                    itemCount: items.length,
                    itemBuilder: (context, i) {
                      final (group, rec, idx) = items[i];
                      if (group != null) return _groupHeaderRow(group);
                      return _tableRow(rec!, idx, columns, unit);
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _groupHeaderRow(MinerGroup group) {
    final dot = switch (group.key) {
      'OK' => BeeSkyColors.ok,
      'CHECK' => BeeSkyColors.warn,
      'ERROR' => BeeSkyColors.bad,
      _ => BeeSkyColors.muted,
    };
    return Container(
      color: BeeSkyColors.panel2,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Text(
            group.key,
            style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
          ),
          const SizedBox(width: 8),
          Text(
            '${group.records.length} máy',
            style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------------
  // Overview heat-grid (v0.25): one cell per miner, coloured by
  // temperature (default) or hashrate, sized S/M/L. Grouping is a
  // table-density presentation — the heat-grid always shows the
  // flat visible list (docs/grid-mapping.md §2).
  // ------------------------------------------------------------------

  Widget _overviewGrid(GridViewResult view) {
    final maxExtent = switch (_grid.overviewSize) {
      OverviewCellSize.small => 104.0,
      OverviewCellSize.medium => 138.0,
      OverviewCellSize.large => 176.0,
    };
    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: maxExtent,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: 1.02,
      ),
      itemCount: view.visible.length,
      itemBuilder: (context, i) => _overviewCell(view.visible[i], view),
    );
  }

  /// The cell's tint. Temperature mode: absolute bands ending in
  /// the ≥85 °C red rule. Hashrate mode: the miner's share of the
  /// best rate IN ITS OWN UNIT among the visible fleet (units
  /// never share a scale). Errors and value-less miners read grey /
  /// red-tinted by their state, exactly like the table's chips.
  (Color, String) _overviewCellStyle(MinerRecord rec, GridViewResult view) {
    if (rec.hasFetchError) return (BeeSkyColors.bad, 'Lỗi kết nối');
    if (_grid.overviewColor == OverviewColorMode.temperature) {
      final t = rec.maxTempC;
      if (t == null) return (BeeSkyColors.muted, '—');
      final label = '${t.toStringAsFixed(0)} °C';
      if (t >= tempLimitC) return (BeeSkyColors.hotTemp, label);
      if (t >= 80) return (const Color(0xFFF59E0B), label);
      if (t >= 70) return (BeeSkyColors.warn, label);
      return (BeeSkyColors.ok, label);
    }
    final key = rec.rateSortKey;
    if (key == null) return (BeeSkyColors.muted, '—');
    var best = 0.0;
    for (final other in view.visible) {
      final k = other.rateSortKey;
      if (k != null && k.$1 == key.$1 && k.$2 > best) best = k.$2;
    }
    final share = best == 0 ? 0.0 : key.$2 / best;
    final color = share >= 0.75
        ? BeeSkyColors.ok
        : share >= 0.4
            ? BeeSkyColors.warn
            : const Color(0xFFF59E0B);
    return (color, rec.rateText);
  }

  Widget _overviewCell(MinerRecord rec, GridViewResult view) {
    final (tint, bigValue) = _overviewCellStyle(rec, view);
    final selected = _selected?.ip == rec.ip;
    final valueSize = switch (_grid.overviewSize) {
      OverviewCellSize.small => 13.0,
      OverviewCellSize.medium => 16.0,
      OverviewCellSize.large => 20.0,
    };
    return Tooltip(
      message: '${rec.ip} • ${rec.model}\n'
          '${rec.rateText} • ${rec.tempText} • ${rec.statusLabel}',
      child: Listener(
        onPointerDown: (_) => _rowPointerDown(rec),
        child: InkWell(
          onTap: () => setState(() => _selected = rec),
          child: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: tint.withValues(alpha: selected ? 0.38 : 0.22),
              border: Border.all(
                color: selected ? BeeSkyColors.accent : tint,
                width: selected ? 2 : 1,
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        rec.ip,
                        style: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (_selection.isSelected(rec.ip))
                      const Icon(
                        Icons.check_circle,
                        size: 14,
                        color: BeeSkyColors.accent,
                      ),
                  ],
                ),
                Text(
                  rec.model,
                  style: const TextStyle(
                    color: BeeSkyColors.muted,
                    fontSize: 10.5,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                const Spacer(),
                Text(
                  bigValue,
                  style: TextStyle(
                    fontSize: valueSize,
                    fontWeight: FontWeight.w800,
                    color: tint,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  rec.statusLabel,
                  style: const TextStyle(
                    color: BeeSkyColors.muted,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
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

  /// The header row: a select-all-visible checkbox, then one
  /// tappable header per ACTIVE column — a tap sorts by that
  /// column, a second tap flips the direction (HashCore sorts
  /// "by field + direction"; the arrow shows the current one).
  Widget _tableHeader(
    List<GridColumnDef> columns,
    double unit,
    GridViewResult view,
  ) {
    final visibleCount = view.visible.length;
    final selectedVisible =
        view.visible.where((r) => _selection.isSelected(r.ip)).length;
    final bool? checkValue = visibleCount == 0
        ? false
        : selectedVisible == 0
            ? false
            : selectedVisible == visibleCount
                ? true
                : null;
    return Container(
      color: BeeSkyColors.tableHeading,
      // Left padding 17 = the rows' 14 + their 3px accent border,
      // so header labels sit exactly over the row cells.
      padding: const EdgeInsets.fromLTRB(17, 4, 14, 4),
      child: Row(
        children: [
          SizedBox(
            width: _checkColW,
            child: Checkbox(
              value: checkValue,
              tristate: true,
              visualDensity: VisualDensity.compact,
              onChanged: (_) => setState(() {
                if (checkValue == true) {
                  for (final r in view.visible) {
                    _selection.selectedIps.remove(r.ip);
                  }
                } else {
                  _selection.selectAll(view.visible);
                }
              }),
            ),
          ),
          for (final col in columns)
            SizedBox(
              width: col.flex * unit,
              child: InkWell(
                onTap: () => _toggleSort(col.id),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Flexible(
                        child: Text(
                          col.label,
                          style: TextStyle(
                            color: _grid.sort.field == col.id
                                ? BeeSkyColors.accent
                                : BeeSkyColors.muted,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.1,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (_grid.sort.field == col.id)
                        Icon(
                          _grid.sort.ascending
                              ? Icons.arrow_upward
                              : Icons.arrow_downward,
                          size: 12,
                          color: BeeSkyColors.accent,
                        ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _tableRow(
    MinerRecord rec,
    int i,
    List<GridColumnDef> columns,
    double unit,
  ) {
    final selected = _selected?.ip == rec.ip;
    final compact = _grid.viewType == GridViewType.compact;
    final bg = selected
        ? BeeSkyColors.selectBg
        : (i.isOdd ? BeeSkyColors.tableZebra : Colors.transparent);
    // Row clicks are read at the pointer level (v0.23): every
    // pointer-down selects instantly, and a second down on the
    // same row inside the double-click window opens the miner's
    // web admin. (A GestureDetector double-tap would hold the
    // single click back until the window expires — the lag BTC
    // Tools does not have.) The InkWell keeps the ripple and the
    // keyboard/accessibility activation path. The CHECKBOX is
    // outside the Listener: a checkbox tap only toggles the
    // checkbox selection, never the detail/double-click path.
    return Row(
      children: [
        Container(
          color: bg,
          width: _checkColW + 14,
          padding: EdgeInsets.symmetric(vertical: compact ? 1 : 4),
          child: Checkbox(
            value: _selection.isSelected(rec.ip),
            visualDensity: VisualDensity.compact,
            onChanged: (_) => setState(() => _selection.toggle(rec.ip)),
          ),
        ),
        Expanded(
          child: Listener(
            onPointerDown: (_) => _rowPointerDown(rec),
            child: InkWell(
              onTap: () => setState(() => _selected = rec),
              child: Container(
                decoration: BoxDecoration(
                  color: bg,
                  // The prototype marks the selected row with a 3px
                  // accent bar.
                  border: selected
                      ? const Border(
                          left:
                              BorderSide(color: BeeSkyColors.accent, width: 3),
                        )
                      : const Border(
                          left: BorderSide(color: Colors.transparent, width: 3),
                        ),
                ),
                padding: EdgeInsets.only(
                  right: 14,
                  top: compact ? 3 : 8,
                  bottom: compact ? 3 : 8,
                ),
                child: Row(
                  children: [
                    for (final col in columns)
                      _gridCell(col, rec, col.flex * unit, compact),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// One cell of the data grid. Board-temp columns reuse the
  /// NHIỆT hot-pill treatment for their single board; the status
  /// column is the OK/CHECK/ERROR chip; the combined NHIỆT column
  /// is the v0.22 per-board cell.
  Widget _gridCell(
    GridColumnDef col,
    MinerRecord rec,
    double width,
    bool compact,
  ) {
    final fontSize = compact ? 12.0 : 13.0;
    if (col.isTemps) {
      return SizedBox(width: width, child: _tempCellContent(rec));
    }
    if (col.isStatus) {
      return SizedBox(width: width, child: _statusChip(rec));
    }
    if (col.id.startsWith('boardTemp')) {
      final idx = int.parse(col.id.substring('boardTemp'.length)) - 1;
      final t = rec.boardTempAt(idx);
      if (t == null) {
        return _textCell('—', width, fontSize);
      }
      final chain = ChainInfo(
        index: idx,
        tempC: t,
        chipsAlive: idx < rec.chains.length ? rec.chains[idx].chipsAlive : 0,
        chipsTotal: idx < rec.chains.length ? rec.chains[idx].chipsTotal : 0,
      );
      return SizedBox(width: width, child: _boardTemp(chain));
    }
    return _textCell(col.textOf(rec), width, fontSize);
  }

  Widget _textCell(String text, double width, double fontSize) {
    return SizedBox(
      width: width,
      child: Text(
        text,
        style: TextStyle(fontSize: fontSize),
        overflow: TextOverflow.ellipsis,
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

  /// The NHIỆT cell shows EVERY hashboard's temperature, not only the
  /// max (owner rule added 2026-11-11 after the prototype review:
  /// "sao hok hiện hết 3 hoặc 4 hash board, cái nào nóng quá thì đỏ
  /// lên"). Values render compactly in chain order; a board at/over
  /// the core's 85 °C limit (models.tempLimitC — the threshold behind
  /// the OVER_TEMP problem) turns bold red on a soft red pill, the
  /// rest stay muted. A record with no per-chain temps falls back to
  /// the single max temp, and an unreachable row keeps "—".
  Widget _tempCellContent(MinerRecord rec) {
    final shown = rec.chains.where((c) => c.tempC != null).toList();
    if (shown.isEmpty) {
      return Text(
        rec.tempText,
        style: const TextStyle(fontSize: 13),
        overflow: TextOverflow.ellipsis,
      );
    }
    // Scale down rather than overflow when a narrow window (detail
    // panel open) squeezes the column — the temps stay on one line.
    return FittedBox(
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

  /// The detail tabs — HashCore's device-info dialog order
  /// (Metrics · Charts · Boards · Pools · Fans · Note), in
  /// BeeSky's side panel instead of a modal (the named layout
  /// divergence, docs/device-detail-mapping.md §4). The first
  /// tab is "Số liệu" (Metrics), NOT "Tổng quan" — that label
  /// already names the grid's Overview density on this screen.
  static const _detailTabNames = [
    'Số liệu',
    'Biểu đồ',
    'Board',
    'Pools',
    'Quạt',
    'Ghi chú',
  ];

  Widget _detailPanel() {
    final rec = _selected!;
    // The note editor follows the selected device (keyed like
    // history/notes: MAC when present, else IP).
    final noteKey = deviceKeyFor(rec);
    if (_noteOwnerKey != noteKey) {
      _noteOwnerKey = noteKey;
      _noteCtrl.text = _notes[noteKey] ?? '';
    }
    // The inspect-backed tabs (Board/Pools/Quạt) fetch lazily
    // for the device on show.
    if (_detailTab >= 2 && _detailTab <= 4) _maybeInspect(rec);
    return GlassCard(
      padding: const EdgeInsets.all(16),
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
          const SizedBox(height: 10),
          _detailTabBar(),
          const SizedBox(height: 12),
          Expanded(
            child: SingleChildScrollView(child: _detailTabBody(rec)),
          ),
        ],
      ),
    );
  }

  Widget _detailTabBar() {
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        for (var i = 0; i < _detailTabNames.length; i++)
          InkWell(
            borderRadius: BorderRadius.circular(999),
            onTap: () => setState(() => _detailTab = i),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: i == _detailTab
                    ? BeeSkyColors.accent
                    : BeeSkyColors.ghostFill,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                _detailTabNames[i],
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: i == _detailTab
                      ? BeeSkyColors.accentText
                      : BeeSkyColors.muted,
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _detailTabBody(MinerRecord rec) {
    return switch (_detailTab) {
      1 => _chartsTab(rec),
      2 => _boardsTab(rec),
      3 => _poolsTab(rec),
      4 => _fansTab(rec),
      5 => _noteTab(rec),
      _ => _overviewTab(rec),
    };
  }

  // ------------------------------------------------------------------
  // Inspect fetch — one deep fetch per device per session
  // ------------------------------------------------------------------

  void _maybeInspect(MinerRecord rec) {
    if (_inspectCache.containsKey(rec.ip) ||
        _inspectLoading.contains(rec.ip)) {
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _ensureInspect(rec);
    });
  }

  Future<void> _ensureInspect(MinerRecord rec) async {
    if (_inspectCache.containsKey(rec.ip) ||
        _inspectLoading.contains(rec.ip)) {
      return;
    }
    setState(() => _inspectLoading.add(rec.ip));
    try {
      final result = await widget.bridge.inspect(
        rec.ip,
        credsFile: await _credsFileForScan(),
        // In a group's scope the core resolves creds through the
        // group's sets first (v0.24 layering), like its scans.
        group: _activeGroup?.name,
        groupsFile: _groupsFile?.path,
      );
      if (!mounted) return;
      setState(() {
        _inspectCache[rec.ip] = result;
        _inspectLoading.remove(rec.ip);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _inspectCache[rec.ip] = InspectResult.failure(rec.ip, '$e');
        _inspectLoading.remove(rec.ip);
      });
    }
  }

  /// The "Số liệu" (Metrics) tab — the v0.22 panel content
  /// verbatim: the shipped panel contract (its board summary
  /// lines included) stays; the Board tab carries the deep view
  /// (the named duplication in the mapping, §4).
  Widget _overviewTab(MinerRecord rec) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
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
                      fontWeight: c.isHot ? FontWeight.w700 : FontWeight.w400,
                    ),
                  ),
                ),
            ],
      ],
    );
  }

  // ------------------------------------------------------------------
  // Charts tab — LOCAL samples only (one per finished scan)
  // ------------------------------------------------------------------

  Widget _chartsTab(MinerRecord rec) {
    final samples = _history[deviceKeyFor(rec)] ?? const <HistorySample>[];
    final rates = ratePoints(samples);
    final temps = tempPoints(samples);
    final powers = powerPoints(samples);
    if (rates.isEmpty && temps.isEmpty && powers.isEmpty) {
      return const Text(
        'Chưa có dữ liệu biểu đồ cho máy này. Biểu đồ được vẽ từ '
        'các lần quét — mỗi lần quét xong ghi thêm một mẫu, quét '
        'thêm vài lần biểu đồ sẽ hiện dần.',
        style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
      );
    }
    String two(int v) => v.toString().padLeft(2, '0');
    String hm(DateTime t) => '${two(t.hour)}:${two(t.minute)}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (rates.isNotEmpty) ...[
          MiniChart(
            title: 'Hashrate',
            unit: rateUnitOf(samples) ?? '',
            points: rates,
            color: BeeSkyColors.accent,
          ),
          const SizedBox(height: 14),
        ],
        if (temps.isNotEmpty) ...[
          MiniChart(
            title: 'Nhiệt độ tối đa',
            unit: '°C',
            points: temps,
            color: BeeSkyColors.hotTemp,
          ),
          const SizedBox(height: 14),
        ],
        if (powers.isNotEmpty) ...[
          MiniChart(
            title: 'Công suất',
            unit: 'W',
            points: powers,
            color: BeeSkyColors.ok,
          ),
          const SizedBox(height: 14),
        ],
        Text(
          '${samples.length} mẫu · ${hm(samples.first.ts)} → '
          '${hm(samples.last.ts)}'
          '${samples.length == 1 ? ' · quét thêm để thấy đường xu hướng' : ''}',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 11.5),
        ),
      ],
    );
  }

  // ------------------------------------------------------------------
  // Boards tab — record rows now, inspect enrichment when landed
  // ------------------------------------------------------------------

  Widget _boardsTab(MinerRecord rec) {
    final insp = _inspectCache[rec.ip];
    // Enrichment matches by POSITION: the record's chains and
    // the inspect boards both enumerate the machine's boards in
    // order (their `index` bases differ between the mock fleet
    // and the real core — position is the convention-free key).
    final deepBoards =
        (insp != null && insp.boards.supported) ? insp.boards.boards : null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (rec.chains.isEmpty)
          const Text(
            'Máy không báo board nào trong lần quét gần nhất.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
          )
        else
          for (var i = 0; i < rec.chains.length; i++)
            _boardBlock(
              rec.chains[i],
              (deepBoards != null && i < deepBoards.length)
                  ? deepBoards[i]
                  : null,
            ),
        if (insp == null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              _inspectLoading.contains(rec.ip)
                  ? 'Đang đọc chi tiết board từ máy…'
                  : 'Đang chuẩn bị đọc chi tiết board…',
              style: const TextStyle(
                  color: BeeSkyColors.muted, fontSize: 12),
            ),
          )
        else if (insp.error != null)
          _sectionError(insp.error!)
        else if (!insp.boards.supported)
          _sectionError(insp.boards.reason ?? 'Không đọc được board.')
        else if (!insp.boards.boards.any((b) => b.hasGrades)) ...[
          // The DATA-GAP, stated where the user would look for
          // the buckets (docs/device-detail-mapping.md §5.1).
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text(
              'Firmware này không phân loại chip Ổn định / Chậm — '
              'chỉ biết chip sống/chết theo ký tự acs.',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
          ),
        ],
      ],
    );
  }

  Widget _boardBlock(ChainInfo chain, InspectBoard? deep) {
    final lines = <Widget>[
      Text(
        'Board ${chain.index + 1}: ${chain.chipsAlive}/${chain.chipsTotal} chip'
        '${chain.tempC == null ? '' : ' • ${chain.tempC!.toStringAsFixed(0)}°C'}',
        style: TextStyle(
          color: chain.isHot ? BeeSkyColors.hotTemp : BeeSkyColors.text,
          fontSize: 12.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    ];
    if (deep != null) {
      if (deep.hasGrades) {
        lines.add(Text(
          'Ổn định ${deep.stable} · Chậm ${deep.slow} · '
          'Nghiêm trọng ${deep.critical}',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ));
      }
      if (deep.pcbTempC != null) {
        lines.add(Text(
          'PCB ${deep.pcbTempC!.toStringAsFixed(0)}°C',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ));
      }
      if (deep.otherChars.isNotEmpty) {
        lines.add(Text(
          'Ký tự acs khác: '
          '${deep.otherChars.entries.map((e) => '${e.key} ×${e.value}').join(' · ')}',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ));
      }
      if (deep.deadPositions.isNotEmpty) {
        lines.add(Text(
          'Chip chết: ${deep.deadPositions.join(', ')}',
          style: const TextStyle(color: BeeSkyColors.bad, fontSize: 12),
        ));
      }
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: lines,
      ),
    );
  }

  // ------------------------------------------------------------------
  // Pools tab — the record's pools when a core fills them, else
  // the inspect fetch (loading / unsupported shown honestly)
  // ------------------------------------------------------------------

  Widget _poolsTab(MinerRecord rec) {
    if (rec.pools.isNotEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < rec.pools.length; i++) ...[
            _kv('Pool ${i + 1} URL', rec.pools[i].url),
            _kv('Pool ${i + 1} worker', rec.pools[i].worker),
            const SizedBox(height: 6),
          ],
        ],
      );
    }
    final insp = _inspectCache[rec.ip];
    if (insp == null) {
      return Text(
        _inspectLoading.contains(rec.ip)
            ? 'Đang đọc pool từ máy…'
            : 'Đang chuẩn bị đọc pool…',
        style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
      );
    }
    if (insp.error != null) return _sectionError(insp.error!);
    if (!insp.pools.supported) {
      return _sectionError(insp.pools.reason ?? 'Không đọc được pool.');
    }
    if (insp.pools.pools.isEmpty) {
      return const Text(
        'Máy không báo pool nào.',
        style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < insp.pools.pools.length; i++) ...[
          _kv('Pool ${i + 1} URL', insp.pools.pools[i].url ?? '—'),
          _kv('Pool ${i + 1} worker', insp.pools.pools[i].user ?? '—'),
          if (insp.pools.pools[i].status != null)
            _kv('Trạng thái', insp.pools.pools[i].status!),
          if (insp.pools.pools[i].accepted != null)
            _kv(
              'Accepted / Rejected',
              '${insp.pools.pools[i].accepted} / '
              '${insp.pools.pools[i].rejected ?? '—'}',
            ),
          const SizedBox(height: 6),
        ],
      ],
    );
  }

  // ------------------------------------------------------------------
  // Fans tab — record speeds now; inspect adds mode/duty/status
  // ------------------------------------------------------------------

  Widget _fansTab(MinerRecord rec) {
    final insp = _inspectCache[rec.ip];
    final deep = (insp != null && insp.fans.supported) ? insp.fans : null;
    final children = <Widget>[];
    if (deep != null) {
      if (deep.mode != null) {
        _fanModeLine(children, deep);
      } else {
        children.add(_kv('Chế độ', '— (firmware không báo)'));
      }
    }
    final speeds = deep != null
        ? [for (final f in deep.fans) (f.id, f.rpm, f.status, f.maxRpm)]
        : [
            for (var i = 0; i < rec.fansRpm.length; i++)
              (i + 1, rec.fansRpm[i], null, null),
          ];
    if (speeds.isEmpty) {
      children.add(const Text(
        'Máy không báo tốc độ quạt.',
        style: TextStyle(color: BeeSkyColors.muted, fontSize: 12.5),
      ));
    } else {
      for (final (id, rpm, status, maxRpm) in speeds) {
        children.add(_kv(
          'Fan $id',
          '${rpm == null ? '—' : formatCount(rpm)} RPM'
          '${status != null ? ' • $status' : ''}'
          '${maxRpm != null ? ' / tối đa ${formatCount(maxRpm)}' : ''}',
          valueColor: status == 'lost' ? BeeSkyColors.bad : null,
        ));
      }
    }
    if (insp == null) {
      children.add(Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Text(
          _inspectLoading.contains(rec.ip)
              ? 'Đang đọc chi tiết quạt từ máy…'
              : 'Đang chuẩn bị đọc chi tiết quạt…',
          style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
        ),
      ));
    } else if (insp.error != null) {
      children.add(_sectionError(insp.error!));
    } else if (!insp.fans.supported) {
      children.add(
          _sectionError(insp.fans.reason ?? 'Không đọc được quạt.'));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  void _fanModeLine(List<Widget> children, InspectFans deep) {
    children.add(_kv(
      'Chế độ',
      deep.mode! +
          (deep.modeParam != null ? ' (${deep.modeParam})' : '') +
          (deep.dutyPct != null ? ' • duty ${deep.dutyPct}%' : ''),
    ));
  }

  /// An inspect section that could not be read, with the core's
  /// own reason — an honest state, never an empty list pretending
  /// to be data.
  Widget _sectionError(String message) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: BeeSkyColors.warn.withValues(alpha: 0.08),
        border: Border.all(color: BeeSkyColors.warn.withValues(alpha: 0.35)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(message, style: const TextStyle(fontSize: 12, height: 1.45)),
    );
  }

  // ------------------------------------------------------------------
  // Note tab — HashCore's Device note + Save note, per device
  // ------------------------------------------------------------------

  Widget _noteTab(MinerRecord rec) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _noteCtrl,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Ghi chú cho máy này',
            contentPadding:
                EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          ),
          style: const TextStyle(fontSize: 13),
        ),
        const SizedBox(height: 10),
        FilledButton.icon(
          onPressed: () => _saveNote(rec),
          icon: const Icon(Icons.save, size: 16),
          label: const Text('Lưu ghi chú'),
        ),
      ],
    );
  }

  Future<void> _saveNote(MinerRecord rec) async {
    final key = deviceKeyFor(rec);
    final text = _noteCtrl.text.trim();
    setState(() {
      if (text.isEmpty) {
        _notes.remove(key);
      } else {
        _notes[key] = text;
      }
      _status = 'Đã lưu ghi chú cho ${rec.ip}.';
    });
    try {
      await _noteStore.save(_notes);
    } on FileSystemException {
      // The note stays in memory for this session.
    }
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
