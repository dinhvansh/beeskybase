import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import 'models.dart';

/// The Operations task system (v0.26) — the HashCore Toolkit's
/// Operations model ported per docs/operations-mapping.md.
///
/// A task = one action type run over a set of selected miners, with
/// per-device results, a streamed progress, a Stop, and a persistent
/// history. The CORE runner (beesky/core/ops.py) is stateless per
/// run: the sidecar bridge spawns `beesky ops --job FILE` and
/// streams its NDJSON events; THIS app owns the task records and
/// their history (beesky-ops-history.json beside the executable —
/// HashCore keeps its history in the app too; its storage medium
/// is UNKNOWN, mapping §1.11).
///
/// Only actions with a real core primitive exist: rescan (the scan
/// pipeline), reboot and switchPool (core/actions.py — the cloud
/// agent's executors). `export` is a BeeSky app-side addition (the
/// selected records serialised locally), NOT a HashCore port. The
/// other 20+ HashCore task types are named PRIMITIVE-GAPs in the
/// mapping doc — they are absent here on purpose, not faked.
enum OpsTaskType {
  rescan('rescan', 'Quét lại', Icons.radar_outlined),
  reboot('reboot', 'Khởi động lại', Icons.restart_alt),
  switchPool('switch_pool', 'Đổi pool', Icons.swap_horiz_outlined),
  export('export', 'Xuất danh sách', Icons.ios_share_outlined);

  final String wire;
  final String label;
  final IconData icon;
  const OpsTaskType(this.wire, this.label, this.icon);

  static OpsTaskType fromWire(String wire) => OpsTaskType.values.firstWhere(
        (t) => t.wire == wire,
        orElse: () => OpsTaskType.rescan,
      );

  /// Device-mutating types ask first (HashCore's "Confirm
  /// operation" dialog); the read-only rescan and the local
  /// export run immediately.
  bool get needsConfirm => this == reboot || this == switchPool;
}

/// Task-level status — the names HashCore's enum.task_status uses
/// for the states the bridge can observe (Waiting/Processing
/// collapse into `running`; mapping §4.2).
enum OpsStatus {
  running('running', 'Đang chạy'),
  success('success', 'Thành công'),
  hasErrors('hasErrors', 'Có lỗi'),
  error('error', 'Lỗi'),
  cancelled('cancelled', 'Đã hủy');

  final String wire;
  final String label;
  const OpsStatus(this.wire, this.label);

  static OpsStatus fromWire(String? wire) => OpsStatus.values.firstWhere(
        (s) => s.wire == wire,
        orElse: () => OpsStatus.error,
      );
}

/// One device's outcome inside a task.
class OpsDeviceResult {
  final String ip;
  final bool ok;
  final String message;

  /// True when the device never ran because the task was stopped
  /// (the app synthesises these from the summary's cancelled
  /// count; the core emits no event for unstarted devices).
  final bool cancelled;

  const OpsDeviceResult({
    required this.ip,
    required this.ok,
    required this.message,
    this.cancelled = false,
  });

  factory OpsDeviceResult.fromJson(Map<String, dynamic> json) =>
      OpsDeviceResult(
        ip: (json['ip'] ?? '') as String,
        ok: json['ok'] == true,
        message: (json['message'] ?? '') as String,
        cancelled: json['cancelled'] == true,
      );

  Map<String, dynamic> toJson() => {
        'ip': ip,
        'ok': ok,
        'message': message,
        if (cancelled) 'cancelled': true,
      };
}

/// One Operations task — the history entry and the live run's state
/// in a single model (the entry is written when the task STARTS,
/// so an app closed mid-run leaves a `running` entry the history
/// dialog honestly renders as "Chưa hoàn tất").
class OpsTask {
  final String id;
  final OpsTaskType type;
  final DateTime createdAt;
  final DateTime? finishedAt;
  final OpsStatus status;
  final List<String> targets;
  final List<OpsDeviceResult> results;

  const OpsTask({
    required this.id,
    required this.type,
    required this.createdAt,
    required this.finishedAt,
    required this.status,
    required this.targets,
    required this.results,
  });

  int get total => targets.length;
  int get completed => results.where((r) => !r.cancelled).length;
  int get okCount => results.where((r) => r.ok).length;
  int get failCount =>
      results.where((r) => !r.ok && !r.cancelled).length;
  int get cancelledCount => results.where((r) => r.cancelled).length;

  Duration? get duration => finishedAt?.difference(createdAt);

  OpsTask copyWith({
    DateTime? finishedAt,
    OpsStatus? status,
    List<OpsDeviceResult>? results,
  }) =>
      OpsTask(
        id: id,
        type: type,
        createdAt: createdAt,
        finishedAt: finishedAt ?? this.finishedAt,
        status: status ?? this.status,
        targets: targets,
        results: results ?? this.results,
      );

  factory OpsTask.fromJson(Map<String, dynamic> json) => OpsTask(
        id: (json['id'] ?? '') as String,
        type: OpsTaskType.fromWire((json['type'] ?? '') as String),
        createdAt:
            DateTime.tryParse((json['created_at'] ?? '') as String) ??
                DateTime.fromMillisecondsSinceEpoch(0),
        finishedAt: json['finished_at'] == null
            ? null
            : DateTime.tryParse(json['finished_at'] as String),
        status: OpsStatus.fromWire(json['status'] as String?),
        targets: ((json['targets'] as List<dynamic>?) ?? const [])
            .map((e) => '$e')
            .toList(),
        results: ((json['results'] as List<dynamic>?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(OpsDeviceResult.fromJson)
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.wire,
        'created_at': createdAt.toIso8601String(),
        'finished_at': finishedAt?.toIso8601String(),
        'status': status.wire,
        'targets': targets,
        'results': results.map((r) => r.toJson()).toList(),
      };

  /// The copyable info block — HashCore's operations_dialog
  /// task_info shape ("{task} / started / finished / duration /
  /// total iterations, completed, errors"), Vietnamese labels.
  String infoText() {
    String fmt(DateTime? t) => t == null
        ? '—'
        : '${t.hour.toString().padLeft(2, '0')}:'
            '${t.minute.toString().padLeft(2, '0')}:'
            '${t.second.toString().padLeft(2, '0')} '
            '${t.day}/${t.month}/${t.year}';
    final d = duration;
    final dur = d == null
        ? '—'
        : (d.inMinutes >= 1
            ? '${d.inMinutes} phút, ${d.inSeconds % 60} giây'
            : '${d.inSeconds} giây');
    return '${type.label}\n\n'
        'bắt đầu: ${fmt(createdAt)}; kết thúc: ${fmt(finishedAt)}; '
        'thời lượng: $dur\n'
        'tổng số máy: $total, đã xong: $completed, lỗi: $failCount';
  }
}

/// One streamed progress event from the core runner (NDJSON line).
class OpsEvent {
  final String kind; // "start" | "result" | "summary"
  final int done;
  final int total;
  final String? ip;
  final bool? ok;
  final String? message;

  /// The fresh health record riding a rescan result event.
  final MinerRecord? record;

  const OpsEvent({
    required this.kind,
    this.done = 0,
    this.total = 0,
    this.ip,
    this.ok,
    this.message,
    this.record,
  });

  factory OpsEvent.fromJson(Map<String, dynamic> json) => OpsEvent(
        kind: (json['event'] ?? '') as String,
        done: ((json['done'] as num?) ?? 0).toInt(),
        total: ((json['total'] as num?) ?? 0).toInt(),
        ip: json['ip'] as String?,
        ok: json['ok'] as bool?,
        message: json['message'] as String?,
        record: json['record'] is Map<String, dynamic>
            ? MinerRecord.fromJson(json['record'] as Map<String, dynamic>)
            : null,
      );
}

/// The runner's final accounting — also SYNTHESISED by the bridge
/// when the process dies without one (a Windows kill leaves no
/// summary line; the received results + the job's target count
/// still account every device, mapping §4.7).
class OpsSummary {
  final int total;
  final int completed;
  final int ok;
  final int failed;
  final int cancelled;
  final OpsStatus status;
  final double elapsedS;

  const OpsSummary({
    required this.total,
    required this.completed,
    required this.ok,
    required this.failed,
    required this.cancelled,
    required this.status,
    required this.elapsedS,
  });

  factory OpsSummary.fromJson(Map<String, dynamic> json) => OpsSummary(
        total: ((json['total'] as num?) ?? 0).toInt(),
        completed: ((json['completed'] as num?) ?? 0).toInt(),
        ok: ((json['ok'] as num?) ?? 0).toInt(),
        failed: ((json['failed'] as num?) ?? 0).toInt(),
        cancelled: ((json['cancelled'] as num?) ?? 0).toInt(),
        status: OpsStatus.fromWire(json['status'] as String?),
        elapsedS: ((json['elapsed_s'] as num?) ?? 0).toDouble(),
      );
}

/// A running task's handle: the event stream, the summary future
/// (always completes — never throws), and the Stop.
abstract class OpsRun {
  Stream<OpsEvent> get events;
  Future<OpsSummary> get summary;
  Future<void> stop();
}

/// Where the ops files live — the job file the sidecar consumes
/// and the exported-lists folder. Same locations strategy as the
/// other stores: beside the executable, %APPDATA%\BeeSky fallback.
class OpsFiles {
  final Directory primaryDir;
  final Directory fallbackDir;

  const OpsFiles({required this.primaryDir, required this.fallbackDir});

  factory OpsFiles.appDefault() {
    final exeDir = File(Platform.resolvedExecutable).parent;
    final appData = Platform.environment['APPDATA'];
    final fallback = (appData != null && appData.isNotEmpty)
        ? Directory('$appData${Platform.pathSeparator}BeeSky')
        : Directory(
            '${Directory.systemTemp.path}${Platform.pathSeparator}BeeSky');
    return OpsFiles(primaryDir: exeDir, fallbackDir: fallback);
  }

  static const jobFileName = 'beesky-ops-job.json';

  File get jobFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$jobFileName');

  /// Directory for exported lists: the primary dir, or the
  /// fallback when the primary refuses the write.
  Directory exportDir() {
    try {
      final probe =
          File('${primaryDir.path}${Platform.pathSeparator}.beesky-write-test');
      probe.writeAsStringSync('');
      probe.deleteSync();
      return primaryDir;
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      return fallbackDir;
    }
  }
}

/// The persistent task history — beesky-ops-history.json beside
/// the executable (the CredStore pattern). Corrupt reads as empty
/// (the app must not brick on a file it can rewrite). Retention:
/// the newest [retention] entries (a BeeSky choice — HashCore's
/// cap is UNKNOWN, mapping §4.8).
class OpsHistoryStore {
  final Directory primaryDir;
  final Directory fallbackDir;

  const OpsHistoryStore({
    required this.primaryDir,
    required this.fallbackDir,
  });

  factory OpsHistoryStore.appDefault() {
    final files = OpsFiles.appDefault();
    return OpsHistoryStore(
      primaryDir: files.primaryDir,
      fallbackDir: files.fallbackDir,
    );
  }

  static const fileName = 'beesky-ops-history.json';
  static const retention = 100;

  File get primaryFile =>
      File('${primaryDir.path}${Platform.pathSeparator}$fileName');
  File get fallbackFile =>
      File('${fallbackDir.path}${Platform.pathSeparator}$fileName');

  Future<List<OpsTask>> load() async {
    for (final file in [primaryFile, fallbackFile]) {
      try {
        if (!file.existsSync()) continue;
        final decoded = jsonDecode(file.readAsStringSync());
        if (decoded is List) {
          return decoded
              .whereType<Map<String, dynamic>>()
              .map(OpsTask.fromJson)
              .toList();
        }
      } on FileSystemException {
        continue;
      } on FormatException {
        continue;
      }
    }
    return [];
  }

  Future<File> save(List<OpsTask> tasks) async {
    final capped = tasks.length <= retention
        ? tasks
        : tasks.sublist(tasks.length - retention);
    final text = const JsonEncoder.withIndent('  ')
        .convert(capped.map((t) => t.toJson()).toList());
    try {
      primaryFile.writeAsStringSync(text);
      return primaryFile;
    } on FileSystemException {
      fallbackDir.createSync(recursive: true);
      fallbackFile.writeAsStringSync(text);
      return fallbackFile;
    }
  }
}
