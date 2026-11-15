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
# native rate units (v0.20)
#
# The cgminer SUMMARY names its rate fields after the unit the value is
# in ("GHS av", "MHS av", ...), and non-SHA256 fleets report in their
# own quantity entirely: Bitmain's fleet displays quote Scrypt miners
# in MH/s and Equihash miners in ksol/s. Until v0.20 every record was
# squeezed into a TH/s number, so an Antminer L9 rendered as "0.01" in
# a TH/s column and a Z15's sol rate was summed into fleet totals as
# if it were TH/s. Records now also carry the rate in its NATIVE unit
# (``rate_value`` / ``rate_unit``); the legacy ``ghs_*`` / ``ths``
# fields are computed exactly as before.
# --------------------------------------------------------------------------

RATE_UNIT_ORDER = ("TH/s", "GH/s", "MH/s", "ksol/s", "sol/s")
HASH_UNITS = ("TH/s", "GH/s", "MH/s")  # sol/s is a different quantity

# Bitmain model families whose rate is not a SHA256 hashrate. The Z
# series is Equihash (sol/s); the L series is Scrypt (MH/s display).
_EQUIHASH_MODEL = re.compile(r"\bZ\d{1,2}\b", re.IGNORECASE)
_SCRYPT_MODEL = re.compile(r"\bL\d{1,2}\b", re.IGNORECASE)


def _field_main(summary: dict, key_5s: str, key_av: str):
    """The main rate of a unit field pair: 5s figure preferred, else av."""
    value = _num(summary.get(key_5s))
    return value if value is not None else _num(summary.get(key_av))


def _native_rate(summary: dict, model) -> tuple:
    """(value, unit) of the miner's rate in its native unit.

    Returns (None, None) when the summary carries no rate field.
    Conventions pinned by the owner's fleet photos (BTC Tools as the
    ground truth: Antminer L9 -> "14.54 MH/s", Antminer Z15 ->
    "1101 ksol/s"):

      * explicit "KSol/s .." / "Sol/s .." fields are the sol rate;
      * a Z-series model's GHS fields carry its sol rate in sol/s, so
        the GHS value / 1000 is the rate in ksol/s;
      * an L-series model's MHS fields are its Scrypt rate — the
        fleet display is the MHS value / 1000, labelled MH/s;
      * otherwise the field's own family: GHS -> value / 1000 in TH/s,
        MHS -> value / 1000 in MH/s (the historical display scale).
    """
    ksol = _field_main(summary, "KSol/s 5s", "KSol/s av")
    if ksol is not None:
        return ksol, "ksol/s"
    sol = _field_main(summary, "Sol/s 5s", "Sol/s av")
    if sol is not None:
        return (sol / 1000.0, "ksol/s") if sol >= 1000 else (sol, "sol/s")
    ghs = _field_main(summary, "GHS 5s", "GHS av")
    mhs = _field_main(summary, "MHS 5s", "MHS av")
    model = str(model or "")
    if ghs is not None and _EQUIHASH_MODEL.search(model):
        return ghs / 1000.0, "ksol/s"
    if mhs is not None and _SCRYPT_MODEL.search(model):
        return mhs / 1000.0, "MH/s"
    if ghs is not None:
        return ghs / 1000.0, "TH/s"
    if mhs is not None:
        return mhs / 1000.0, "MH/s"
    return None, None


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
                     power_w=None, rate_value=None, rate_unit=None) -> dict:
    """Apply the problem rules and assemble a status record.

    Shared by every vendor adapter. *chains* entries must carry ``index``,
    ``chips_total``, ``chips_alive``, ``dead_positions`` (possibly empty when
    the vendor API only reports counts) and ``temp_c``. *power_w* is the
    miner's wall power draw in watts when the source reports one (v0.9 —
    VNish dashd ``power_consumption``, some cgminer stats), else ``None``;
    the cloud integrates it into energy reports. *rate_value* / *rate_unit*
    carry the rate in its native unit (v0.20); when the caller does not
    supply them they are derived from the GH/s main rate as TH/s, which
    is exactly the historical ``ths`` semantics (HTTP adapters report
    in TH/s already).
    """
    gh_main = gh_5s if gh_5s is not None else gh_av
    if rate_unit is None and gh_main is not None:
        rate_value, rate_unit = gh_main / 1000.0, "TH/s"
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
        "rate_value": rate_value,
        "rate_unit": rate_unit,
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
    rate_value, rate_unit = _native_rate(summary, model)

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
                            power_w=_power_w(summary, stats),
                            rate_value=rate_value, rate_unit=rate_unit)


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
        "ghs_5s": None, "ghs_av": None, "ths": None,
        "rate_value": None, "rate_unit": None, "power_w": None,
        "chains": [], "fans_rpm": [], "chips_alive": 0, "chips_total": 0,
        "max_temp_c": None,
        "problems": [{"code": "FETCH_ERROR", "detail": message}],
        "status": "CHECK",
    }


# --------------------------------------------------------------------------
# rate access for display + aggregation (v0.20)
# --------------------------------------------------------------------------

def record_rate(record) -> tuple | None:
    """(value, unit) of a record's rate in its native unit, or None.

    Pre-v0.20 records (old agents, stored snapshots) carry no rate
    fields; their ``ths`` IS a TH/s rate and is reported as such.
    """
    if not isinstance(record, dict):
        return None
    value, unit = record.get("rate_value"), record.get("rate_unit")
    if value is not None and unit:
        return float(value), str(unit)
    ths = record.get("ths")
    if ths is not None:
        return float(ths), "TH/s"
    return None


def format_rate(record) -> str:
    """One record's rate as displayed: "14.54 MH/s", "-" when unknown."""
    rate = record_rate(record)
    return f"{rate[0]:.2f} {rate[1]}" if rate else "-"


def fleet_rate_totals(records) -> list[tuple]:
    """[(value, unit)] — rates summed per native unit, canonical order.

    Aggregation NEVER mixes units: a mixed SHA256 + Scrypt + Equihash
    fleet yields one total per unit instead of a single meaningless
    number (the pre-v0.20 fleet total did exactly that).
    """
    sums: dict[str, float] = {}
    for record in records or []:
        rate = record_rate(record)
        if rate is not None:
            sums[rate[1]] = sums.get(rate[1], 0.0) + rate[0]
    return [(sums[unit], unit) for unit in RATE_UNIT_ORDER if unit in sums]


def format_rate_totals(records) -> str:
    """Grouped fleet total: "102.90 TH/s · 14.54 MH/s · 1,101.00 ksol/s".

    A single-unit fleet renders exactly as the historical total did
    ("110.13 TH/s"); several units join with thousands separators.
    """
    groups = fleet_rate_totals(records)
    if not groups:
        return "-"
    if len(groups) == 1:
        value, unit = groups[0]
        return f"{value:.2f} {unit}"
    return " · ".join(f"{value:,.2f} {unit}" for value, unit in groups)


def ths_equivalent(record):
    """The record's rate as a true TH/s figure, or None.

    Only H/s-family rates convert: the native display value of an
    MH/s record is its MHS field / 1000, so its TH/s equivalent is
    that value / 1000 again (MHS / 1e6 — identical to the record's
    ``ths`` whenever both exist). A sol rate is a different physical
    quantity: it returns None and must never be summed into a
    hashrate total (pool comparison, farm history).
    """
    rate = record_rate(record)
    if rate is None:
        return None
    value, unit = rate
    if unit == "TH/s":
        return value
    if unit == "GH/s":
        return value / 1000.0
    if unit == "MH/s":
        return value / 1000.0
    return None


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
    rate = record_rate(record)
    if rate is not None:
        lines.append(f"Hashrate: {rate[0]:.2f} {rate[1]}")
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


def _ticket_problem_lines(text: str) -> list[str]:
    """The bullet lines of a ticket's "Vấn đề phát hiện:" section.

    The section runs from its header to the first blank line —
    make_ticket's format is fixed, so the parse is exact, not a
    heuristic.
    """
    lines = text.splitlines()
    try:
        start = lines.index("Vấn đề phát hiện:") + 1
    except ValueError:
        return []
    problems: list[str] = []
    for line in lines[start:]:
        if not line.strip():
            break
        if line.startswith("- "):
            problems.append(line[2:])
    return problems


def list_tickets(outdir: str | Path) -> list[dict]:
    """List the ticket files in *outdir*, newest first (v0.32).

    The read side of write_tickets, backing the read-only
    `beesky tickets` verb and the Flutter Lịch sử sửa view. Each
    entry: {file, ip, modified, model, problems, text} — ip from
    the filename (write_tickets' own encoding), model from the
    ticket's "Model:" line, problems from its problem section,
    modified = the file's mtime as local ISO time (the ticket
    text itself carries no timestamp). A missing directory is
    an empty history, not an error. Local ticket files carry
    NO status — that concept exists only in the cloud repairs
    table, and none is invented here.
    """
    import time as _time

    out = Path(outdir)
    if not out.is_dir():
        return []
    entries: list[tuple[float, dict]] = []
    for path in out.glob("ticket-*.txt"):
        try:
            text = path.read_text(encoding="utf-8")
            mtime = path.stat().st_mtime
        except OSError:
            continue
        stem = path.name[len("ticket-"):-len(".txt")]
        model = ""
        for line in text.splitlines():
            if line.startswith("Model: "):
                model = line[len("Model: "):].strip()
                break
        entries.append((mtime, {
            "file": path.name,
            "ip": stem.replace("_", "."),
            "modified": _time.strftime(
                "%Y-%m-%dT%H:%M:%S", _time.localtime(mtime)),
            "model": model,
            "problems": _ticket_problem_lines(text),
            "text": text,
        }))
    entries.sort(key=lambda item: item[0], reverse=True)
    return [entry for _mtime, entry in entries]
