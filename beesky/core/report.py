"""Status records, problem rules, and repair tickets.

Every miner is normalised into one JSON-friendly *status record*. The CLI
table, the JSON export, and the Vietnamese repair tickets are all rendered
from that record — this normalisation layer is BeeSky's core, the same role
the per-vendor "repository" layer plays in bigger fleet tools.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMP_LIMIT_C = 85        # flag any chain at or above this temperature
NO_HASH_ELAPSED_S = 300  # hashrate 0 only counts as a problem after 5 min up


# --------------------------------------------------------------------------
# small tolerant helpers (firmware JSON types are notoriously inconsistent)
# --------------------------------------------------------------------------

def _num(value, default=None):
    """Best-effort numeric conversion (handles '1,234.5', None, junk)."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _merged_stats(stats: dict) -> dict:
    """Accept either a raw cgminer stats reply or an already-merged dict."""
    if not isinstance(stats, dict):
        return {}
    entries = stats.get("STATS")
    if isinstance(entries, list):
        merged: dict = {}
        for entry in entries:
            if isinstance(entry, dict):
                merged.update(entry)
        return merged
    return stats


def _chain_temp(stats: dict, idx: int):
    """Find the temperature for chain *idx* across firmware key variants."""
    for key in (f"temp{idx}", f"temp2_{idx}", f"temp_{idx}", f"chip_temp{idx}"):
        val = _num(stats.get(key))
        if val is not None:
            return val
    match = [v for k, v in stats.items()
             if re.fullmatch(rf"temp\d*_{idx}", str(k)) and _num(v) is not None]
    return _num(match[0]) if match else None


def _fan_speeds(stats: dict) -> list[int]:
    """Collect fan RPM values (fan1..fanN or a fan_speeds list)."""
    speeds: list[int] = []
    listed = stats.get("fan_speeds")
    if isinstance(listed, list):
        speeds = [int(v) for v in (_num(x) for x in listed) if v is not None]
    else:
        numbered = []
        for key, val in stats.items():
            m = re.fullmatch(r"fan(\d+)", str(key))
            if m and _num(val) is not None:
                numbered.append((int(m.group(1)), int(_num(val))))
        speeds = [rpm for _n, rpm in sorted(numbered)]
    return speeds


# --------------------------------------------------------------------------
# record building
# --------------------------------------------------------------------------

def _finalise_record(ip: str, model: str, elapsed_s: int, gh_5s, gh_av,
                     chains: list[dict], fans: list[int], source: str,
                     power_w=None) -> dict:
    """Apply the problem rules and assemble a status record.

    Shared by every vendor adapter. *chains* entries must carry ``index``,
    ``chips_total``, ``chips_alive``, ``dead_positions`` (possibly empty when
    the vendor API only reports counts) and ``temp_c``. *power_w* is the
    miner's wall power draw in watts when the source reports one (v0.9 —
    VNish dashd ``power_consumption``, some cgminer stats), else ``None``;
    the cloud integrates it into energy reports.
    """
    gh_main = gh_5s if gh_5s is not None else gh_av
    for chain in chains:
        chain["chips_missing"] = chain["chips_total"] - chain["chips_alive"]
    temps = [c["temp_c"] for c in chains if c["temp_c"] is not None]

    problems: list[dict] = []
    for chain in chains:
        if chain["chips_total"] > 0 and chain["chips_alive"] == 0:
            problems.append({
                "code": "CHAIN_DOWN", "chain": chain["index"],
                "detail": f"chain {chain['index']}: 0/{chain['chips_total']} chips responding",
            })
        elif chain["chips_missing"] > 0:
            detail = (f"chain {chain['index']}: missing {chain['chips_missing']} chip(s)")
            if chain["dead_positions"]:
                detail += f", dead at position(s) {chain['dead_positions']}"
            else:
                detail += " (API reports counts only, no dead positions)"
            problems.append({
                "code": "MISSING_CHIPS", "chain": chain["index"],
                "missing": chain["chips_missing"],
                "dead_positions": chain["dead_positions"],
                "detail": detail,
            })
        if chain["temp_c"] is not None and chain["temp_c"] >= TEMP_LIMIT_C:
            problems.append({
                "code": "OVER_TEMP", "chain": chain["index"],
                "temp_c": chain["temp_c"],
                "detail": f"chain {chain['index']}: {chain['temp_c']:.0f} C >= {TEMP_LIMIT_C} C limit",
            })
    if gh_main is not None and gh_main == 0 and elapsed_s > NO_HASH_ELAPSED_S:
        problems.append({
            "code": "NO_HASHRATE",
            "detail": f"hashrate 0 after {elapsed_s} s uptime",
        })

    return {
        "ip": ip,
        "model": model,
        "source": source,
        "elapsed_s": elapsed_s,
        "ghs_5s": gh_5s,
        "ghs_av": gh_av,
        "ths": (gh_main / 1000.0) if gh_main is not None else None,
        "power_w": float(power_w) if power_w is not None else None,
        "chains": chains,
        "fans_rpm": fans,
        "chips_alive": sum(c["chips_alive"] for c in chains),
        "chips_total": sum(c["chips_total"] for c in chains),
        "max_temp_c": max(temps) if temps else None,
        "problems": problems,
        "status": "CHECK" if problems else "OK",
    }


# Stat/summary keys under which some cgminer firmwares report wall power
# (watts). Absent on classic Bitmain bmminer — the record then keeps
# power_w=None and energy accounting skips the miner (v0.9).
_POWER_KEYS = ("Power", "Wattage", "power_consumption", "Power Consumption")


def _power_w(summary: dict, stats: dict):
    """Wall power in watts from a cgminer summary/stats pair, or None."""
    for source in (stats, summary):
        for key in _POWER_KEYS:
            val = _num(source.get(key))
            if val is not None and val > 0:
                return val
    return None


def build_record(ip: str, summary: dict, stats: dict, source: str = "cgminer") -> dict:
    """Normalise one miner's cgminer-shaped summary+stats into a record."""
    summary = summary if isinstance(summary, dict) else {}
    stats = _merged_stats(stats if isinstance(stats, dict) else {})

    model = (summary.get("Type") or stats.get("Type")
             or summary.get("Model") or stats.get("Model") or "Unknown")
    elapsed = int(_num(summary.get("Elapsed"), _num(stats.get("Elapsed"), 0)) or 0)
    gh_5s = _num(summary.get("GHS 5s"))
    gh_av = _num(summary.get("GHS av"))
    if gh_av is None and _num(summary.get("MHS av")) is not None:
        gh_av = _num(summary.get("MHS av")) / 1000.0

    # --- per-chain data from chain_acs strings ('o' = alive chip) ---------
    chains: list[dict] = []
    acs_keys = sorted(
        (k for k in stats if re.fullmatch(r"chain_acs\d+", str(k))),
        key=lambda k: int(re.search(r"(\d+)$", str(k)).group(1)),
    )
    for key in acs_keys:
        idx = int(re.search(r"(\d+)$", str(key)).group(1))
        acs = str(stats.get(key) or "")
        alive = acs.count("o")
        dead_positions = [i + 1 for i, ch in enumerate(acs) if ch != "o"]
        chains.append({
            "index": idx,
            "chips_total": len(acs),
            "chips_alive": alive,
            "dead_positions": dead_positions,
            "temp_c": _chain_temp(stats, idx),
        })

    return _finalise_record(ip, model, elapsed, gh_5s, gh_av,
                            chains, _fan_speeds(stats), source,
                            power_w=_power_w(summary, stats))


def build_record_from_boards(ip: str, *, model: str = "Unknown", elapsed_s: int = 0,
                             ths_realtime=None, ths_average=None,
                             chains=(), fans_rpm=(), source: str,
                             power_w=None) -> dict:
    """Build a record from already-parsed per-board data (HTTP adapters).

    Hashrates are given in TH/s (the unit HTTP dashboards use); chain entries
    are dicts with ``index``, ``chips_total``, ``chips_alive``, optional
    ``dead_positions`` and ``temp_c``.
    """
    norm_chains = [{
        "index": int(c["index"]),
        "chips_total": int(c["chips_total"]),
        "chips_alive": int(c["chips_alive"]),
        "dead_positions": list(c.get("dead_positions") or []),
        "temp_c": c.get("temp_c"),
    } for c in chains]
    gh_5s = ths_realtime * 1000.0 if ths_realtime is not None else None
    gh_av = ths_average * 1000.0 if ths_average is not None else None
    return _finalise_record(ip, model, int(elapsed_s or 0), gh_5s, gh_av,
                            norm_chains, [int(f) for f in fans_rpm], source,
                            power_w=power_w)


def error_record(ip: str, message: str, source: str = "cgminer") -> dict:
    """Status record for a candidate that stopped answering its API."""
    return {
        "ip": ip, "model": "Unknown", "source": source, "elapsed_s": 0,
        "ghs_5s": None, "ghs_av": None, "ths": None, "power_w": None,
        "chains": [], "fans_rpm": [], "chips_alive": 0, "chips_total": 0,
        "max_temp_c": None,
        "problems": [{"code": "FETCH_ERROR", "detail": message}],
        "status": "CHECK",
    }


# --------------------------------------------------------------------------
# repair tickets (Vietnamese) — BeeSky's differentiator vs generic exports
# --------------------------------------------------------------------------

_SUGGESTIONS = {
    "MISSING_CHIPS": (
        "Đo điện áp từng domain trên board (điểm đo/PIC), kiểm tra cáp dữ liệu "
        "và mối hàn quanh các vị trí chip chết; đối chiếu vị trí chip với sơ đồ "
        "domain của board để khoanh vùng trước khi thay chip."
    ),
    "CHAIN_DOWN": (
        "Board không lên chip: kiểm tra nguồn cấp cho board, đầu nối nguồn, cáp "
        "dữ liệu, PIC và điện áp ra của board trước khi nghi ngờ chip ASIC."
    ),
    "OVER_TEMP": (
        "Kiểm tra quạt và đường gió, vệ sinh bụi, kiểm tra keo tản nhiệt và lực "
        "ép ốc heatsink của board; chạy lại và đo nhiệt sau khi xử lý."
    ),
    "NO_HASHRATE": (
        "Máy chạy lâu nhưng không có hashrate: kiểm tra cấu hình pool, kết nối "
        "mạng và log kernel (SSH/API) trước khi tháo board."
    ),
    "FETCH_ERROR": (
        "Không đọc được API của máy: kiểm tra nguồn, cáp mạng, IP và cổng 4028."
    ),
}


def _problem_line_vi(problem: dict) -> str:
    code = problem["code"]
    chain = problem.get("chain")
    if code == "MISSING_CHIPS":
        if problem.get("dead_positions"):
            return (f"Board {chain}: thiếu {problem['missing']} chip "
                    f"(vị trí chết: {', '.join(map(str, problem['dead_positions']))})")
        return (f"Board {chain}: thiếu {problem['missing']} chip "
                f"(API không cho vị trí chip chết)")
    if code == "CHAIN_DOWN":
        return f"Board {chain}: không lên chip nào (0 chip phản hồi)"
    if code == "OVER_TEMP":
        return f"Board {chain}: nhiệt độ cao {problem['temp_c']:.0f}°C (ngưỡng {TEMP_LIMIT_C}°C)"
    if code == "NO_HASHRATE":
        return "Hashrate bằng 0 dù máy đã chạy lâu"
    if code == "FETCH_ERROR":
        return f"Không lấy được dữ liệu: {problem['detail']}"
    return problem["detail"]


def make_ticket(record: dict) -> str:
    """Render one plain-text repair ticket (Vietnamese) for a problem miner."""
    lines = [
        "PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO — BeeSky",
        "=" * 46,
        f"IP: {record['ip']}",
        f"Model: {record['model']}",
    ]
    if record.get("ths") is not None:
        lines.append(f"Hashrate: {record['ths']:.2f} TH/s")
    lines.append(f"Thời gian đã chạy: {record['elapsed_s']} giây")
    lines.append(f"Tổng chip sống: {record['chips_alive']}/{record['chips_total']}")
    lines.append("")
    lines.append("Vấn đề phát hiện:")
    for problem in record["problems"]:
        lines.append(f"- {_problem_line_vi(problem)}")
    lines.append("")
    lines.append("Chi tiết từng board:")
    if record["chains"]:
        for chain in record["chains"]:
            temp = f"{chain['temp_c']:.0f}°C" if chain["temp_c"] is not None else "n/a"
            lines.append(
                f"- Board {chain['index']}: {chain['chips_alive']}/{chain['chips_total']} "
                f"chip, nhiệt {temp}"
            )
    else:
        lines.append("- (không đọc được dữ liệu board)")
    lines.append("")
    lines.append("Gợi ý kiểm tra:")
    seen: list[str] = []
    for problem in record["problems"]:
        suggestion = _SUGGESTIONS.get(problem["code"])
        if suggestion and problem["code"] not in seen:
            seen.append(problem["code"])
            lines.append(f"- {suggestion}")
    return "\n".join(lines) + "\n"


def write_tickets(records: list[dict], outdir: str | Path) -> list[Path]:
    """Write one ticket file per problem miner; return the paths written."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for record in records:
        if not record["problems"]:
            continue
        path = out / f"ticket-{record['ip'].replace('.', '_')}.txt"
        path.write_text(make_ticket(record), encoding="utf-8")
        written.append(path)
    return written
