#!/usr/bin/env python3
"""v0.20 unit-correctness suite — hashrate units + diagnosis audit.

Pure-Python (no servers, no display): records are built through
``report.build_record`` from cgminer-shaped summary/stats fixtures,
then every consumer of the rate is asserted — record fields, GUI row
values, CLI table, repair tickets, grouped fleet totals, the cloud
store's aggregations and the watch engine's drop events.

Fixtures are built from the cgminer API conventions + the owner's
fleet photos (BTC Tools as ground truth):

  * Antminer L9  — GHS av 14.54 with MHS av 14540 (bmminer emits the
    pair, MHS = GHS x 1000) -> BeeSky must display "14.54 MH/s"; its
    stats carry 3 chains of 123 acs chars with 110 'o' each (the
    photo's 330/369), temps <= 60 C, fans ~6620.
  * Antminer Z15 — GHS av 1101000 (the sol rate in sol/s riding the
    GHS fields) -> BeeSky must display "1101.00 ksol/s".
  * Antminer S19 Pro — the tests/mock_miner.py fixture itself; its
    record must stay identical to tests/mock_scan.json (the record
    the full pipeline produced before v0.20), rate fields aside.
"""

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def close(a, b, eps=1e-9) -> bool:
    return a is not None and abs(a - b) < eps


# ----------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------

def _acs(total: int, alive: int) -> str:
    """chain_acs string: `alive` 'o' out of `total`, dead spread out."""
    chars = ["o"] * total
    for i in range(total - alive):
        chars[9 * i + 4] = "x"
    return "".join(chars)


def l9_stats() -> dict:
    return {
        "Type": "Antminer L9",
        "chain_acs1": _acs(123, 110), "chain_acs2": _acs(123, 110),
        "chain_acs3": _acs(123, 110),
        "temp1": 58, "temp2": 60, "temp3": 57,
        "fan1": 6620, "fan2": 6620, "fan3": 6630, "fan4": 6620,
    }


def z15_stats() -> dict:
    return {
        "Type": "Antminer Z15",
        "chain_acs1": "o" * 36, "chain_acs2": "o" * 36,
        "chain_acs3": "o" * 36,
        "temp1": 62, "temp2": 64, "temp3": 63,
        "fan1": 8160, "fan2": 8160,
    }


def build_l9(summary: dict):
    from beesky.core import report
    return report.build_record("192.168.2.38", summary, l9_stats(),
                               source="cgminer")


def build_z15(summary: dict):
    from beesky.core import report
    return report.build_record("192.168.2.50", summary, z15_stats(),
                               source="cgminer")


def build_s19():
    """The mock_miner S19 Pro, through the same parse the RPC path uses."""
    from beesky.core import report
    import mock_miner
    summary = mock_miner.summary_reply()["SUMMARY"][0]
    return report.build_record("127.0.0.1", summary,
                               mock_miner.stats_reply(), source="cgminer")


# ----------------------------------------------------------------------
# record level
# ----------------------------------------------------------------------

def record_checks() -> None:
    from beesky.core import report

    # -- S19 Pro regression: identical to the pre-v0.20 pipeline record.
    s19 = build_s19()
    expected = json.loads(
        (ROOT / "tests" / "mock_scan.json").read_text(encoding="utf-8"))[0]
    for field in ("model", "source", "elapsed_s", "ghs_5s", "ghs_av",
                  "ths", "chips_alive", "chips_total", "max_temp_c",
                  "fans_rpm", "status", "problems"):
        check(f"s19 regression: field {field} unchanged",
              s19[field] == expected[field],
              f"{s19[field]!r} != {expected[field]!r}")
    check("s19: native rate is its TH/s rate",
          s19["rate_value"] == s19["ths"] and s19["rate_unit"] == "TH/s",
          f"{s19['rate_value']} {s19['rate_unit']}")
    check("s19: format_rate renders the historical string",
          report.format_rate(s19) == "102.90 TH/s",
          report.format_rate(s19))
    check("s19: ths_equivalent == ths",
          report.ths_equivalent(s19) == s19["ths"])

    # -- L9: the photo machine (av-only rate fields).
    l9 = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                   "GHS av": 14.54, "MHS av": 14540.0})
    check("l9: display rate is 14.54 MH/s (BTC Tools ground truth)",
          close(l9["rate_value"], 14.54) and l9["rate_unit"] == "MH/s",
          f"{l9['rate_value']} {l9['rate_unit']}")
    check("l9: format_rate", report.format_rate(l9) == "14.54 MH/s",
          report.format_rate(l9))
    check("l9: legacy ths field untouched (0.01454)",
          close(l9["ths"], 0.01454, 1e-12), str(l9["ths"]))
    check("l9: ths_equivalent == ths (H/s family converts)",
          close(report.ths_equivalent(l9), l9["ths"], 1e-12))
    check("l9: chips are the machine's own acs counts (330/369)",
          (l9["chips_alive"], l9["chips_total"]) == (330, 369),
          f"{l9['chips_alive']}/{l9['chips_total']}")
    check("l9: max temp 60, fans as reported",
          l9["max_temp_c"] == 60
          and l9["fans_rpm"] == [6620, 6620, 6630, 6620],
          f"{l9['max_temp_c']} {l9['fans_rpm']}")
    check("l9: flagged CHECK by MISSING_CHIPS x3 (self-report, by design)",
          l9["status"] == "CHECK"
          and [p["code"] for p in l9["problems"]] == ["MISSING_CHIPS"] * 3
          and all(p["missing"] == 13 for p in l9["problems"]),
          json.dumps(l9["problems"]))

    # -- L9 with 5s fields: the 5s figure wins, as for `ths`.
    l9b = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                    "GHS 5s": 14.50, "GHS av": 14.54,
                    "MHS 5s": 14500.0, "MHS av": 14540.0})
    check("l9 (5s+av): native rate follows the MHS 5s figure",
          close(l9b["rate_value"], 14.50) and l9b["rate_unit"] == "MH/s",
          f"{l9b['rate_value']} {l9b['rate_unit']}")

    # -- L9 with MHS fields only: the pre-v0.20 gh fallback is intact.
    l9c = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                    "MHS av": 14540.0})
    check("l9 (MHS only): gh_av fallback intact, display 14.54 MH/s",
          close(l9c["ghs_av"], 14.54)
          and report.format_rate(l9c) == "14.54 MH/s",
          f"{l9c['ghs_av']} {report.format_rate(l9c)}")

    # -- Z15: the photo machine (av-only) and a 5s variant.
    z15 = build_z15({"Type": "Antminer Z15", "Elapsed": 700000,
                     "GHS av": 1101000.0})
    check("z15: display rate is 1101.00 ksol/s (BTC Tools ground truth)",
          close(z15["rate_value"], 1101.0) and z15["rate_unit"] == "ksol/s",
          f"{z15['rate_value']} {z15['rate_unit']}")
    check("z15: format_rate", report.format_rate(z15) == "1101.00 ksol/s",
          report.format_rate(z15))
    check("z15: healthy per its own report (OK, no problems)",
          z15["status"] == "OK" and z15["problems"] == [],
          json.dumps(z15["problems"]))
    check("z15: sol rate has NO TH/s equivalent",
          report.ths_equivalent(z15) is None)
    z15b = build_z15({"Type": "Antminer Z15", "Elapsed": 700000,
                      "GHS 5s": 1100500.0, "GHS av": 1101000.0})
    check("z15 (5s+av): native rate follows the 5s figure",
          close(z15b["rate_value"], 1100.50)
          and z15b["rate_unit"] == "ksol/s",
          f"{z15b['rate_value']} {z15b['rate_unit']}")

    # -- explicit sol fields (cgminer convention) beat the GHS guess.
    sol = report.build_record(
        "10.0.0.7", {"Type": "Antminer Z15", "Elapsed": 60,
                     "KSol/s av": 880.0, "GHS av": 880000.0},
        z15_stats(), source="cgminer")
    check("sol fields: KSol/s av wins over the GHS fields",
          close(sol["rate_value"], 880.0) and sol["rate_unit"] == "ksol/s",
          f"{sol['rate_value']} {sol['rate_unit']}")
    small = report.build_record(
        "10.0.0.8", {"Type": "Antminer Z9", "Elapsed": 60,
                     "Sol/s av": 950.0}, z15_stats(), source="cgminer")
    check("sol fields: sub-1000 Sol/s stays in sol/s",
          close(small["rate_value"], 950.0)
          and small["rate_unit"] == "sol/s",
          f"{small['rate_value']} {small['rate_unit']}")

    # -- unknown model, MHS only: field-family fallback.
    unk = report.build_record(
        "10.0.0.9", {"Elapsed": 60, "MHS av": 504000.0}, z15_stats(),
        source="cgminer")
    check("unknown model (MHS only): MH/s display from the field family",
          report.format_rate(unk) == "504.00 MH/s",
          report.format_rate(unk))

    # -- legacy (pre-v0.20) record shapes keep working.
    legacy = {"ip": "10.0.0.10", "ths": 42.5}
    check("legacy record: rate reads back as TH/s",
          report.record_rate(legacy) == (42.5, "TH/s")
          and report.format_rate(legacy) == "42.50 TH/s"
          and report.ths_equivalent(legacy) == 42.5)
    check("error record: no rate anywhere",
          report.record_rate(report.error_record("10.0.0.11", "boom")) is None
          and report.format_rate(report.error_record("10.0.0.11", "x")) == "-")


# ----------------------------------------------------------------------
# totals + display surfaces
# ----------------------------------------------------------------------

def totals_and_display_checks() -> None:
    from beesky.core import report
    s19 = build_s19()
    l9 = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                   "GHS av": 14.54, "MHS av": 14540.0})
    z15 = build_z15({"Type": "Antminer Z15", "Elapsed": 700000,
                     "GHS av": 1101000.0})
    fleet = [s19, l9, z15]

    totals = report.fleet_rate_totals(fleet)
    check("totals: grouped per unit, canonical order, never mixed",
          [u for _v, u in totals] == ["TH/s", "MH/s", "ksol/s"]
          and close(totals[0][0], 102.9) and close(totals[1][0], 14.54)
          and close(totals[2][0], 1101.0),
          str(totals))
    check("totals: grouped rendering matches the fleet example shape",
          report.format_rate_totals(fleet)
          == "102.90 TH/s · 14.54 MH/s · 1,101.00 ksol/s",
          report.format_rate_totals(fleet))
    check("totals: single-unit fleet renders as before",
          report.format_rate_totals([s19]) == "102.90 TH/s")
    check("totals: empty fleet renders '-'",
          report.format_rate_totals([]) == "-")

    # GUI row values (pure function — no window needed).
    from beesky.gui import row_values
    check("gui rows: native value+unit per row",
          row_values(s19)[3] == "102.90 TH/s"
          and row_values(l9)[3] == "14.54 MH/s"
          and row_values(z15)[3] == "1101.00 ksol/s",
          f"{row_values(s19)[3]} | {row_values(l9)[3]} | "
          f"{row_values(z15)[3]}")

    # CLI table.
    from beesky.cli import _print_table
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _print_table(fleet)
    out = buf.getvalue()
    check("cli table: Hashrate header + native units in rows",
          "Hashrate" in out and "102.90 TH/s" in out
          and "14.54 MH/s" in out and "1101.00 ksol/s" in out,
          out)

    # Repair tickets.
    check("tickets: hashrate line carries the native unit",
          "Hashrate: 14.54 MH/s" in report.make_ticket(l9)
          and "Hashrate: 102.90 TH/s" in report.make_ticket(s19))


# ----------------------------------------------------------------------
# cloud store aggregations
# ----------------------------------------------------------------------

def store_checks() -> None:
    from beesky.cloud.store import CloudStore

    s19 = build_s19()
    l9 = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                   "GHS av": 14.54, "MHS av": 14540.0})
    z15 = build_z15({"Type": "Antminer Z15", "Elapsed": 700000,
                     "GHS av": 1101000.0})

    tmp = Path(tempfile.mkdtemp(prefix="beesky-v20-store-"))
    store = CloudStore(str(tmp / "store.db"))
    t0 = 1_700_000_000.0

    mixed = store.create_agent("Trại Hỗn Hợp", "units-key-a")
    store.add_snapshot(mixed, t0, [s19, l9, z15])
    summaries = {s["site"]: s for s in store.sites_summary()}
    site = summaries["Trại Hỗn Hợp"]
    check("store: rate_totals groups the mixed snapshot per unit",
          site["rate_totals"] == [
              {"unit": "TH/s", "value": 102.9},
              {"unit": "MH/s", "value": 14.54},
              {"unit": "ksol/s", "value": 1101.0}],
          json.dumps(site["rate_totals"]))
    check("store: total_ths is the H/s-family sum only (102.91)",
          site["total_ths"] == 102.91, str(site["total_ths"]))
    check("store: farm_ths counts S19 + L9 equivalent, excludes the Z15",
          store.farm_ths("Trại Hỗn Hợp") == 102.9145,
          str(store.farm_ths("Trại Hỗn Hợp")))
    rows = store.history_series("Trại Hỗn Hợp", 0)
    check("store: history sample carries the same H/s-family total",
          len(rows) == 1 and rows[0]["total_ths"] == 102.9145,
          json.dumps(rows))

    equi = store.create_agent("Trại Z15", "units-key-b")
    store.add_snapshot(equi, t0, [z15])
    check("store: Equihash-only site has no farm_ths (poller skips it)",
          store.farm_ths("Trại Z15") is None,
          str(store.farm_ths("Trại Z15")))
    zsite = {s["site"]: s for s in store.sites_summary()}["Trại Z15"]
    check("store: Equihash-only site totals: 0 TH/s + its ksol/s group",
          zsite["total_ths"] == 0
          and zsite["rate_totals"] == [{"unit": "ksol/s", "value": 1101.0}],
          json.dumps(zsite))

    legacy = store.create_agent("Trại Cũ", "units-key-c")
    store.add_snapshot(legacy, t0, [
        {"ip": "10.0.9.1", "model": "Antminer S19 Pro", "source": "dashd",
         "status": "OK", "ths": 100.0, "max_temp_c": 70.0,
         "chips_alive": 342, "chips_total": 342, "fans_rpm": [4000],
         "problems": []}])
    lsite = {s["site"]: s for s in store.sites_summary()}["Trại Cũ"]
    check("store: pre-v0.20 snapshot aggregates exactly as before",
          lsite["total_ths"] == 100.0
          and lsite["rate_totals"] == [{"unit": "TH/s", "value": 100.0}]
          and store.farm_ths("Trại Cũ") == 100.0,
          json.dumps(lsite))


# ----------------------------------------------------------------------
# watch engine: drop detection is a per-miner ratio (unit-safe)
# ----------------------------------------------------------------------

def events_checks() -> None:
    from beesky.core.events import EventEngine

    cfg = {"cooldown_s": 0, "baseline_min_samples": 2}

    engine = EventEngine(cfg)
    l9 = build_l9({"Type": "Antminer L9", "Elapsed": 712345,
                   "GHS av": 14.54, "MHS av": 14540.0})
    l9_slow = build_l9({"Type": "Antminer L9", "Elapsed": 712400,
                        "GHS av": 7.27, "MHS av": 7270.0})
    ip = l9["ip"]
    engine.observe_cycle({ip: l9}, now=1000.0)
    engine.observe_cycle({ip: l9}, now=1010.0)
    events = engine.observe_cycle({ip: l9_slow}, now=1020.0)
    drops = [e for e in events if e["type"] == "HASHRATE_DROP"]
    check("events: L9 rate halved -> HASHRATE_DROP in native units",
          len(drops) == 1 and "MH/s" in drops[0]["detail"]
          and "14.54 -> 7.27" in drops[0]["detail"]
          and drops[0]["data"]["drop_pct"] == 50.0,
          json.dumps(events))

    engine2 = EventEngine(cfg)
    s19 = build_s19()
    s19_slow = dict(s19, rate_value=60.0, ths=60.0,
                    ghs_5s=60000.0, ghs_av=60000.0)
    ip2 = s19["ip"]
    engine2.observe_cycle({ip2: s19}, now=1000.0)
    engine2.observe_cycle({ip2: s19}, now=1010.0)
    events2 = engine2.observe_cycle({ip2: s19_slow}, now=1020.0)
    drops2 = [e for e in events2 if e["type"] == "HASHRATE_DROP"]
    check("events: S19 drop keeps the historical TH/s wording + payload",
          len(drops2) == 1 and "TH/s" in drops2[0]["detail"]
          and drops2[0]["data"]["baseline_ths"] == 102.9
          and drops2[0]["data"]["current_ths"] == 60.0,
          json.dumps(events2))


def main() -> int:
    record_checks()
    totals_and_display_checks()
    store_checks()
    events_checks()
    print()
    if FAILURES:
        print(f"UNITS TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print("UNITS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
