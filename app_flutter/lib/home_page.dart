import 'package:flutter/material.dart';

import 'models.dart';
import 'sidecar.dart';
import 'theme.dart';

/// The main window — mirrors the Tk app's structure (v0.19.x) so current
/// users recognise it instantly: header, scan card, 4 stat tiles, miners
/// table + detail panel, status line.
class HomePage extends StatefulWidget {
  final BeeSkyBridge bridge;
  const HomePage({super.key, required this.bridge});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _targetCtrl = TextEditingController();
  final _userCtrl = TextEditingController(text: 'root');
  final _passCtrl = TextEditingController();

  SysInfo? _sysinfo;
  List<MinerRecord> _records = const [];
  MinerRecord? _selected;
  bool _scanned = false;
  bool _busy = false;
  String _status = 'Sẵn sàng.';

  @override
  void initState() {
    super.initState();
    _loadSysinfo();
  }

  @override
  void dispose() {
    _targetCtrl.dispose();
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadSysinfo() async {
    try {
      final info = await widget.bridge.sysinfo();
      if (!mounted) return;
      setState(() {
        _sysinfo = info;
        // Pre-fill the target with this machine's own /24 (the v0.19.6
        // lesson: a hard-coded foreign subnet finds nothing at a farm),
        // unless the user already typed something.
        if (_targetCtrl.text.isEmpty) {
          _targetCtrl.text = info.defaultTarget;
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Không đọc được sysinfo từ beesky: $e');
    }
  }

  String get _target => _targetCtrl.text.trim().isEmpty
      ? '192.168.1.0/24'
      : _targetCtrl.text.trim();

  Future<void> _runScan() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _status = 'Đang quét $_target …';
    });
    try {
      final result = await widget.bridge.scan(
        _target,
        user: _userCtrl.text.trim(),
        password: _passCtrl.text,
      );
      if (!mounted) return;
      setState(() {
        _records = result.records;
        _scanned = true;
        // v0.19.7 behaviour: land on the first row so the detail panel
        // is alive immediately after a scan.
        _selected = result.records.isEmpty ? null : result.records.first;
        _status =
            'Quét xong: tìm thấy ${result.found} máy trong '
            '${result.scanned} địa chỉ (${result.elapsedS.toStringAsFixed(1)} giây).';
      });
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
        user: _userCtrl.text.trim(),
        password: _passCtrl.text,
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

  Future<void> _openWeb() async {
    try {
      await widget.bridge.openLocalWeb(_target);
      if (!mounted) return;
      setState(() => _status = 'Đã mở web tại chỗ: http://localhost:8787');
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Lỗi mở web: $e');
    }
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _header(),
            const SizedBox(height: 16),
            _scanCard(),
            if (_busy) ...[
              const SizedBox(height: 10),
              const LinearProgressIndicator(minHeight: 3),
            ],
            const SizedBox(height: 16),
            _tilesRow(),
            const SizedBox(height: 16),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(child: _tableCard()),
                  const SizedBox(width: 16),
                  SizedBox(width: 340, child: _detailCard()),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              _status,
              style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _header() {
    return Row(
      children: [
        Image.asset('assets/beesky-logo.png', width: 44, height: 44),
        const SizedBox(width: 12),
        const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'BeeSky',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
            ),
            Text(
              'Giám sát & chẩn đoán máy đào ASIC',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
          ],
        ),
        const Spacer(),
        if (widget.bridge.isMock)
          _pill('MOCK', BeeSkyColors.warn)
        else if (_sysinfo != null)
          _pill('v${_sysinfo!.version}', BeeSkyColors.muted),
      ],
    );
  }

  Widget _pill(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: BeeSkyColors.ghostFill,
        border: Border.all(color: BeeSkyColors.glassBorder),
        borderRadius: BorderRadius.circular(radiusPill),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 12)),
    );
  }

  Widget _scanCard() {
    return GlassCard(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: _targetCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Mục tiêu quét',
                    hintText: '192.168.1.0/24 hoặc 192.168.0.10-60, …',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              SizedBox(
                width: 140,
                child: TextField(
                  controller: _userCtrl,
                  decoration: const InputDecoration(labelText: 'User'),
                ),
              ),
              const SizedBox(width: 12),
              SizedBox(
                width: 140,
                child: TextField(
                  controller: _passCtrl,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Mật khẩu'),
                ),
              ),
              const SizedBox(width: 14),
              FilledButton.icon(
                onPressed: _busy ? null : _runScan,
                icon: const Icon(Icons.radar, size: 18),
                label: const Text('Quét ngay'),
              ),
              const SizedBox(width: 10),
              OutlinedButton(
                onPressed: _busy ? null : _exportTickets,
                child: const Text('Xuất phiếu sửa'),
              ),
              const SizedBox(width: 10),
              OutlinedButton(
                onPressed: _busy ? null : _openWeb,
                child: const Text('Mở web tại chỗ'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'User / Mật khẩu — tài khoản web của máy chạy firmware gốc. '
            'Quét lại: bấm Quét ngay lần nữa.',
            style: TextStyle(color: BeeSkyColors.muted, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _tilesRow() {
    final maxTemp = fleetMaxTempC(_records);
    final problems = fleetProblemCount(_records);
    return Row(
      children: [
        _tile('Tổng số máy', _scanned ? '${_records.length}' : '—'),
        const SizedBox(width: 16),
        _tile('Tổng hashrate', _scanned ? fleetRateTotalsText(_records) : '—'),
        const SizedBox(width: 16),
        _tile(
          'Máy có vấn đề',
          _scanned ? '$problems' : '—',
          valueColor: problems > 0 ? BeeSkyColors.bad : null,
        ),
        const SizedBox(width: 16),
        _tile(
          'Nhiệt độ cao nhất',
          maxTemp == null ? '—' : '${maxTemp.toStringAsFixed(0)} °C',
        ),
      ],
    );
  }

  Widget _tile(String label, String value, {Color? valueColor}) {
    return Expanded(
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: const TextStyle(color: BeeSkyColors.muted, fontSize: 12),
            ),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.w700,
                color: valueColor ?? BeeSkyColors.text,
              ),
              overflow: TextOverflow.ellipsis,
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
                      itemBuilder: (context, i) => _tableRow(_records[i], i),
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _emptyState() {
    // The polish detail the owner admired in the Toolkit: a real empty
    // state (icon + line + action), not a blank grid.
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
    ('Model', 4),
    ('Nguồn', 3),
    ('Hashrate', 3),
    ('Chip', 2),
    ('Nhiệt độ', 2),
    ('Quạt', 4),
    ('Trạng thái', 2),
  ];

  Widget _tableHeader() {
    return Container(
      color: BeeSkyColors.tableHeading,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          for (final (label, flex) in _columns)
            Expanded(
              flex: flex,
              child: Text(
                label,
                style: const TextStyle(
                  color: BeeSkyColors.muted,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
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
    return InkWell(
      onTap: () => setState(() => _selected = rec),
      child: Container(
        color: bg,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
        child: Row(
          children: [
            _cell(rec.ip, 3),
            _cell(rec.model, 4),
            _cell(rec.sourceLabel, 3),
            _cell(rec.rateText, 3),
            _cell(rec.chipsText, 2),
            _cell(rec.tempText, 2),
            _cell(rec.fansText, 4),
            Expanded(flex: 2, child: _statusChip(rec)),
          ],
        ),
      ),
    );
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

  Widget _statusChip(MinerRecord rec) {
    final (bg, fg) = switch (rec.statusLabel) {
      'OK' => (const Color(0x2634D399), BeeSkyColors.ok),
      'ERROR' => (const Color(0x26F87171), BeeSkyColors.bad),
      _ => (const Color(0x26FBBF24), BeeSkyColors.warn),
    };
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
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

  Widget _detailCard() {
    final rec = _selected;
    return GlassCard(
      child: rec == null
          ? const Center(
              child: Text(
                'Chọn một máy trong bảng để xem chi tiết.',
                style: TextStyle(color: BeeSkyColors.muted),
                textAlign: TextAlign.center,
              ),
            )
          : SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${rec.ip} — ${rec.model}',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    rec.sourceLabel,
                    style: const TextStyle(
                      color: BeeSkyColors.muted,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _kv('Hashrate', rec.rateText),
                  _kv('Chip', rec.chipsText),
                  _kv(
                    'Nhiệt độ',
                    rec.maxTempC == null
                        ? '—'
                        : '${rec.maxTempC!.toStringAsFixed(0)} °C',
                  ),
                  _kv(
                    'Quạt',
                    rec.fansRpm.isEmpty ? '—' : '${rec.fansText} RPM',
                  ),
                  _kv(
                    'Trạng thái',
                    rec.statusLabel,
                    valueColor: rec.statusLabel == 'OK'
                        ? BeeSkyColors.ok
                        : rec.statusLabel == 'ERROR'
                        ? BeeSkyColors.bad
                        : BeeSkyColors.warn,
                  ),
                  const Divider(height: 22),
                  const Text(
                    'Vấn đề:',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  if (rec.issues.isEmpty)
                    const Text(
                      'Không phát hiện vấn đề.',
                      style: TextStyle(color: BeeSkyColors.muted),
                    )
                  else
                    for (final p in rec.issues)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text(
                          '• [${p.code}] ${p.detail}',
                          style: TextStyle(
                            color: p.severity == 'error'
                                ? BeeSkyColors.bad
                                : BeeSkyColors.warn,
                          ),
                        ),
                      ),
                  if (rec.chains.isNotEmpty) ...[
                    const Divider(height: 22),
                    for (final c in rec.chains)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text(
                          'Board ${c.index + 1}: ${c.chipsAlive}/${c.chipsTotal} chip'
                          '${c.tempC == null ? '' : ', nhiệt ${c.tempC!.toStringAsFixed(0)} °C'}',
                          style: const TextStyle(
                            color: BeeSkyColors.muted,
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ],
              ),
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
