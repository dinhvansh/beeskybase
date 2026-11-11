import 'dart:convert';

import 'package:beesky_app/models.dart';
import 'package:flutter_test/flutter_test.dart';

/// The sample envelope mirrors the v0.21 bridge document exactly,
/// including the two machines that exposed the v0.20 unit bug.
const sampleEnvelope = '''
{"records": [
  {"ip": "192.168.2.101", "model": "Antminer S19 Pro", "source": "vnish",
   "chains": [{"index": 0, "temp_c": 65.0, "chips_alive": 114, "chips_total": 114}],
   "fans_rpm": [4120, 4080], "chips_alive": 342, "chips_total": 342,
   "max_temp_c": 65.0, "problems": [], "status": "OK",
   "cred_label": "VNish trại A",
   "rate_value": 110.5, "rate_unit": "TH/s", "ths": 110.5},
  {"ip": "192.168.2.105", "model": "Antminer S21", "source": "vnish",
   "chains": [], "fans_rpm": [4200], "chips_alive": 324, "chips_total": 324,
   "max_temp_c": 63.0, "problems": [], "status": "OK",
   "rate_value": 104.5, "rate_unit": "TH/s", "ths": 104.5},
  {"ip": "192.168.2.102", "model": "Antminer L9", "source": "cgminer",
   "chains": [{"index": 1, "temp_c": 59.0, "chips_alive": 84, "chips_total": 123}],
   "fans_rpm": [4560, 4440], "chips_alive": 330, "chips_total": 369,
   "max_temp_c": 59.0,
   "problems": [{"code": "MISSING_CHIPS", "severity": "warn",
                 "detail": "board 1: 84/123 chip"}],
   "status": "CHECK", "rate_value": 14.54, "rate_unit": "MH/s", "ths": null},
  {"ip": "192.168.2.103", "model": "Antminer Z15", "source": "cgminer",
   "chains": [], "fans_rpm": [3900], "chips_alive": 72, "chips_total": 72,
   "max_temp_c": 58.0, "problems": [], "status": "OK",
   "rate_value": 1101.0, "rate_unit": "ksol/s", "ths": null},
  {"ip": "192.168.2.104", "model": "—", "source": "cgminer",
   "chains": [], "fans_rpm": [], "chips_alive": 0, "chips_total": 0,
   "max_temp_c": null,
   "problems": [{"code": "FETCH_ERROR", "severity": "error",
                 "detail": "không kết nối được (cổng 4028/80)"}],
   "status": "CHECK", "rate_value": null, "rate_unit": null, "ths": null}
 ],
 "scanned": 254, "found": 5, "elapsed_s": 3.42}
''';

void main() {
  group('bridge envelope parsing', () {
    final result = ScanResult.fromJson(
      jsonDecode(sampleEnvelope) as Map<String, dynamic>,
    );

    test('envelope counters survive', () {
      expect(result.scanned, 254);
      expect(result.found, 5);
      expect(result.elapsedS, closeTo(3.42, 0.001));
      expect(result.records, hasLength(5));
    });

    test('native units are kept per machine (the v0.20 rule)', () {
      final byIp = {for (final r in result.records) r.ip: r};
      expect(byIp['192.168.2.102']!.rateText, '14.54 MH/s');
      expect(byIp['192.168.2.103']!.rateText, '1,101.00 ksol/s');
      expect(byIp['192.168.2.101']!.rateText, '110.50 TH/s');
      expect(byIp['192.168.2.104']!.rateText, '—');
    });

    test('problems wire key maps to issues; status chip logic', () {
      final byIp = {for (final r in result.records) r.ip: r};
      expect(byIp['192.168.2.102']!.issues.single.code, 'MISSING_CHIPS');
      expect(byIp['192.168.2.102']!.statusLabel, 'CHECK');
      expect(byIp['192.168.2.104']!.statusLabel, 'ERROR');
      expect(byIp['192.168.2.101']!.statusLabel, 'OK');
      expect(fleetProblemCount(result.records), 2);
    });

    test('header chip counts split OK / CHECK / ERROR', () {
      expect(fleetStatusCount(result.records, 'OK'), 3);
      expect(fleetStatusCount(result.records, 'CHECK'), 1);
      expect(fleetStatusCount(result.records, 'ERROR'), 1);
    });

    test('grouped totals mirror format_rate_totals', () {
      expect(
        fleetRateTotalsText(result.records),
        '215.00 TH/s · 14.54 MH/s · 1,101.00 ksol/s',
      );
      expect(fleetMaxTempC(result.records), 65.0);
    });

    test('single-unit fleet has no separator', () {
      final z15 = result.records.where((r) => r.model.contains('Z15')).toList();
      expect(fleetRateTotalsText(z15), '1,101.00 ksol/s');
      expect(fleetRateTotalsText(const []), '0.00 TH/s');
    });

    test('labels and misc text fields', () {
      final byIp = {for (final r in result.records) r.ip: r};
      expect(byIp['192.168.2.101']!.sourceLabel, 'VNish');
      expect(byIp['192.168.2.102']!.sourceLabel, 'cgminer RPC');
      expect(byIp['192.168.2.102']!.chipsText, '330/369');
      expect(byIp['192.168.2.102']!.fansText, '4560 / 4440');
      expect(byIp['192.168.2.104']!.fansText, '—');
      expect(byIp['192.168.2.104']!.tempText, '—');
    });

    test('cred_label parses when present, null when absent (v0.23)', () {
      final byIp = {for (final r in result.records) r.ip: r};
      expect(byIp['192.168.2.101']!.credLabel, 'VNish trại A');
      // cgminer RPC has no auth -> never a label.
      expect(byIp['192.168.2.102']!.credLabel, isNull);
      expect(byIp['192.168.2.104']!.credLabel, isNull);
    });
  });

  group('legacy records (pre-0.21, ths only)', () {
    test('ths is read as TH/s', () {
      final rec = MinerRecord.fromJson(const {
        'ip': '10.0.0.9',
        'model': 'Antminer S19',
        'source': 'stock',
        'chains': [],
        'fans_rpm': [],
        'chips_alive': 10,
        'chips_total': 10,
        'max_temp_c': null,
        'problems': [],
        'status': 'OK',
        'ths': 99.5,
      });
      expect(rec.rateText, '99.50 TH/s');
      expect(rec.sourceLabel, 'Bitmain gốc');
      expect(fleetRateTotalsText([rec]), '99.50 TH/s');
    });
  });

  group('per-board temps (the NHIỆT column rule)', () {
    MinerRecord recWithChains(List<Map<String, Object?>> chains,
            {double? maxTempC}) =>
        MinerRecord.fromJson({
          'ip': '10.0.0.7',
          'model': 'Antminer Z15',
          'source': 'cgminer',
          'chains': chains,
          'fans_rpm': [3900],
          'chips_alive': 72,
          'chips_total': 72,
          'max_temp_c': maxTempC,
          'problems': [],
          'status': 'OK',
          'rate_value': 1101.0,
          'rate_unit': 'ksol/s',
          'ths': null,
        });

    Map<String, Object?> chain(int index, double? tempC) => {
          'index': index,
          'temp_c': tempC,
          'chips_alive': 24,
          'chips_total': 24,
        };

    test('boardTemps lists every reported board temp in chain order', () {
      final rec = recWithChains(
        [chain(0, 71.0), chain(1, 88.0), chain(2, 73.0)],
        maxTempC: 88.0,
      );
      expect(rec.boardTemps, [71.0, 88.0, 73.0]);
    });

    test('the hot line is >= 85 — the core TEMP_LIMIT_C', () {
      final rec = recWithChains(
        [chain(0, 84.9), chain(1, 85.0), chain(2, null)],
        maxTempC: 85.0,
      );
      expect(tempLimitC, 85);
      expect(rec.chains[0].isHot, isFalse);
      expect(rec.chains[1].isHot, isTrue);
      expect(rec.chains[2].isHot, isFalse);
      // A chain that reported no temp contributes nothing to the cell.
      expect(rec.boardTemps, [84.9, 85.0]);
    });

    test('no per-chain temps -> empty boardTemps, max-temp fallback', () {
      final noChains = recWithChains(const [], maxTempC: 63.0);
      expect(noChains.boardTemps, isEmpty);
      expect(noChains.tempText, '63 °C');
      final nullTemps = recWithChains([chain(0, null), chain(1, null)]);
      expect(nullTemps.boardTemps, isEmpty);
      expect(nullTemps.tempText, '—');
    });
  });

  group('sysinfo', () {
    test('parses version + default target', () {
      final info = SysInfo.fromJson(const {
        'version': '0.23.0',
        'default_target': '192.168.2.0/24',
      });
      expect(info.version, '0.23.0');
      expect(info.defaultTarget, '192.168.2.0/24');
    });
  });
}
