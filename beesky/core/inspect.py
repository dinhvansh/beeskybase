"""One-device deep fetch (v0.27) — the data behind the detail tabs.

The scan record is deliberately lean: per-board chip counts and
speeds, no pools, no fan mode, no chip grades. HashCore's device
info dialog shows pools / fans / per-board chip buckets, and the
firmware BeeSky already talks to exposes all of it — just not
through the scan path (the full audit is in
docs/device-detail-mapping.md §2). This module fetches it for
ONE device, read-only, through the scan's own machinery:

  * `discover.probe_host` claims the device — family detection
    plus the v0.23/v0.24 credential resolution — and the winning
    set's token / API key / login ride the candidate into the
    section fetches, exactly like `cli._fetch_record`;
  * each section (boards / pools / fans) then reads through the
    claiming family's adapter and is reported as
    ``{"supported": True, ...}`` or ``{"supported": False,
    "reason": ...}`` — an explicit marker, never an empty
    success, and one section's failure never sinks the others.

What each family genuinely exposes (evidence in the mapping):

  * vnish (dashd): /summary carries pools (PoolStats), cooling
    (per-fan rpm/status/max_rpm, the fan mode, fan_duty) and
    per-board chip_statuses counts {grey, orange, red} — the
    firmware's grades, which ARE HashCore's buckets (grey =
    normal = STABLE, orange = degraded but hashing = SLOW,
    red = dead = CRITICAL); /boards adds the per-chip list.
  * cgminer: the STATS acs strings give per-chip characters
    ('o' = alive; any other character is a dead position by the
    record builder's own rule) — counts and positions, but NO
    grade buckets: the non-'o' alphabet has no documented
    per-grade semantics in our evidence (DATA-GAP, mapping §5).
    Pools come from the RPC `pools` command; fans from STATS,
    speeds only (no mode key exists).
  * stock: the web status CGI is cgminer-shaped, so boards and
    fan speeds work like cgminer; pools have NO CGI source, so
    the RPC `pools` command is attempted and its failure is the
    section's stated reason.
"""

from __future__ import annotations

import re
from collections import Counter

from . import report
from .bitmain import BitmainClient, BitmainError, _to_cgminer_shape
from .cgminer import CgminerClient, CgminerError
from .dashd import DashdClient, DashdError, _temp_max
from .discover import probe_host


def _unsupported(reason: str) -> dict:
    return {"supported": False, "reason": reason}


# ---------------------------------------------------------------------------
# boards from cgminer-shaped stats (the cgminer AND stock families)
# ---------------------------------------------------------------------------

def _boards_from_stats(stats: dict) -> dict:
    """Per-chain acs detail: counts + positions, no grade buckets.

    Mirrors report.build_record's acs reading exactly (same key
    order, same 'o'-vs-other rule) so inspect and the record can
    never disagree about a board.
    """
    merged = report._merged_stats(stats if isinstance(stats, dict) else {})
    acs_keys = sorted(
        (k for k in merged if re.fullmatch(r"chain_acs\d+", str(k))),
        key=lambda k: int(re.search(r"(\d+)$", str(k)).group(1)),
    )
    boards: list[dict] = []
    for key in acs_keys:
        idx = int(re.search(r"(\d+)$", str(key)).group(1))
        acs = str(merged.get(key) or "")
        others = Counter(ch for ch in acs if ch != "o")
        boards.append({
            "index": idx,
            "acs": acs,
            "chips_total": len(acs),
            "chips_ok": acs.count("o"),
            "dead_positions": [i + 1 for i, ch in enumerate(acs)
                               if ch != "o"],
            "other_chars": dict(sorted(others.items())),
            "temp_c": report._chain_temp(merged, idx),
        })
    if not boards:
        return _unsupported("stats reply carries no chain_acs data")
    return {"supported": True, "boards": boards}


def _fans_from_stats(stats: dict) -> dict:
    """Fan speeds from cgminer-shaped stats; mode has no source."""
    merged = report._merged_stats(stats if isinstance(stats, dict) else {})
    speeds = report._fan_speeds(merged)
    if not speeds:
        return _unsupported("stats reply carries no fan speeds")
    return {
        "supported": True,
        "mode": None,
        "fans": [{"id": i + 1, "rpm": rpm}
                 for i, rpm in enumerate(speeds)],
    }


def _pools_from_rpc(client: CgminerClient) -> dict:
    """The cgminer RPC `pools` reply, normalised to the wire shape."""
    resp = client.pools()
    status = resp.get("STATUS")
    if isinstance(status, list) and status and \
            isinstance(status[0], dict) and status[0].get("STATUS") == "E":
        return _unsupported(
            f"pools command refused: {status[0].get('Msg', 'error')}")
    raw = resp.get("POOLS")
    if not isinstance(raw, list):
        return _unsupported("pools reply carries no POOLS list")
    pools: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        pools.append({
            "id": entry.get("POOL"),
            "url": entry.get("URL"),
            "user": entry.get("User"),
            "status": entry.get("Status"),
            "accepted": entry.get("Accepted"),
            "rejected": entry.get("Rejected"),
        })
    return {"supported": True, "pools": pools}


# ---------------------------------------------------------------------------
# vnish (dashd) sections — everything rides the one /summary call
# ---------------------------------------------------------------------------

def _dashd_sections(client: DashdClient) -> tuple[dict, dict, dict]:
    """(boards, pools, fans) from one summary (+ /boards) fetch."""
    try:
        summary = client.summary()
    except DashdError as exc:
        reason = str(exc)
        return (_unsupported(reason), _unsupported(reason),
                _unsupported(reason))
    miner = summary.get("miner")
    if not isinstance(miner, dict) or not miner:
        reason = "dashd answered without miner stats (not mining?)"
        return (_unsupported(reason), _unsupported(reason),
                _unsupported(reason))

    # --- boards: grade counts from summary, chip list from /boards
    try:
        boards_list = client.boards()
    except DashdError:
        boards_list = None  # counts still stand; positions degrade
    boards_by_id: dict[int, dict] = {}
    if boards_list:
        for entry in boards_list:
            if isinstance(entry, dict) and isinstance(entry.get("id"), int):
                boards_by_id[entry["id"]] = entry
    boards: list[dict] = []
    for board in miner.get("chains") or []:
        if not isinstance(board, dict):
            continue
        board_id = board.get("id", len(boards))
        statuses = board.get("chip_statuses") or {}
        grey = int(statuses.get("grey") or 0)
        orange = int(statuses.get("orange") or 0)
        red = int(statuses.get("red") or 0)
        chips = None
        dead: list[int] = []
        entry = boards_by_id.get(board_id)
        if entry is not None and isinstance(entry.get("chips"), list):
            chips = []
            for chip in entry["chips"]:
                if not isinstance(chip, dict) \
                        or not isinstance(chip.get("id"), int):
                    continue
                pos = int(chip["id"]) + 1
                grade = chip.get("grade")
                if grade == "red":
                    dead.append(pos)
                chips.append({
                    "pos": pos,
                    "hr": chip.get("hr"),
                    "grade": grade,
                    "temp": chip.get("temp"),
                })
        total = grey + orange + red
        if chips is not None and total == 0:
            # Summary carried no counts: the chip list itself is
            # the source (grades counted, never assumed).
            total = len(chips)
            red = sum(1 for c in chips if c["grade"] == "red")
            orange = sum(1 for c in chips if c["grade"] == "orange")
            grey = total - red - orange
        boards.append({
            "index": int(board_id) + 1,  # dashd board ids are 0-based
            "chips_total": total,
            "stable": grey,
            "slow": orange,
            "critical": red,
            "dead_positions": dead,
            "chip_temp_c": _temp_max(board.get("chip_temp")),
            "pcb_temp_c": _temp_max(board.get("pcb_temp")),
            "chips": chips,
        })
    boards_section = (
        {"supported": True, "boards": boards} if boards
        else _unsupported("summary carries no chains"))

    # --- pools: the summary's PoolStats list (subset, verbatim values)
    raw_pools = miner.get("pools")
    if isinstance(raw_pools, list):
        pools = [{
            "id": p.get("id"),
            "url": p.get("url"),
            "user": p.get("user"),
            "status": p.get("status"),
            "accepted": p.get("accepted"),
            "rejected": p.get("rejected"),
            "stale": p.get("stale"),
            "ping": p.get("ping"),
        } for p in raw_pools if isinstance(p, dict)]
        pools_section = {"supported": True, "pools": pools}
    else:
        pools_section = _unsupported("summary carries no pools list")

    # --- fans: cooling block (mode object OR plain string — the
    # api-doc's FanSettings.mode is {name, param}; some builds and
    # the test mock serve the bare string; both are read).
    cooling = miner.get("cooling")
    if isinstance(cooling, dict) and isinstance(cooling.get("fans"), list):
        fans = [{
            "id": int(f["id"]) + 1 if isinstance(f.get("id"), int)
                  else i + 1,
            "rpm": f.get("rpm"),
            "status": f.get("status"),
            "max_rpm": f.get("max_rpm"),
        } for i, f in enumerate(cooling["fans"]) if isinstance(f, dict)]
        settings = cooling.get("settings") or {}
        mode_raw = settings.get("mode") if isinstance(settings, dict) else None
        mode, mode_param = None, None
        if isinstance(mode_raw, dict):
            mode = mode_raw.get("name")
            mode_param = mode_raw.get("param")
        elif isinstance(mode_raw, str):
            mode = mode_raw
        fans_section = {
            "supported": True,
            "mode": mode,
            "mode_param": mode_param,
            "duty_pct": cooling.get("fan_duty"),
            "fans": fans,
        }
    else:
        fans_section = _unsupported("summary carries no cooling block")

    return boards_section, pools_section, fans_section


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def inspect_device(ip: str, *, timeout: float = 3.0,
                   http_port: int = 80, cgminer_port: int = 4028,
                   username: str = "root", password: str = "root",
                   api_key: str | None = None, token: str | None = None,
                   creds: list[dict] | None = None) -> dict:
    """Deep-fetch one miner; returns the inspect document.

    The document always carries ``ip``; a claimed device adds
    ``source`` / ``model`` / ``cred_label`` and the three
    sections, an unclaimed one an ``error`` string instead.
    """
    try:
        cand = probe_host(ip, timeout=timeout, http_port=http_port,
                          cgminer_port=cgminer_port, username=username,
                          password=password, api_key=api_key, token=token,
                          creds=creds)
    except Exception as exc:  # noqa: BLE001 — a sick device must not
        # kill the bridge; the probe can raise outside the adapters'
        # error types (the v0.26 ops lesson).
        return {"ip": ip, "source": None,
                "error": f"probe failed: {exc}"}
    if cand is None or cand.source is None:
        return {"ip": ip, "source": None,
                "error": "no miner answered on the RPC or web ports"}

    doc: dict = {
        "ip": ip,
        "source": cand.source,
        "model": cand.model,
        "cred_label": cand.cred_label,
    }
    fetch_timeout = max(timeout, 2.0)

    if cand.source == "vnish":
        client = DashdClient(
            ip, port=cand.http_port, timeout=fetch_timeout,
            api_key=api_key or cand.dashd_api_key,
            token=token or cand.dashd_token)
        boards, pools, fans = _dashd_sections(client)
        doc.update({"boards": boards, "pools": pools, "fans": fans})
        return doc

    if cand.source == "stock":
        # Boards + fans ride the status payload the probe already
        # fetched (refetch only if the cache is somehow empty).
        data = cand.status_data or None
        if data is None:
            try:
                data = BitmainClient(
                    ip, port=cand.http_port, timeout=fetch_timeout,
                    username=cand.username,
                    password=cand.password).miner_status()
            except BitmainError as exc:
                reason = str(exc)
                data = None
                doc.update({"boards": _unsupported(reason),
                            "fans": _unsupported(reason)})
        if data is not None:
            _summary, stats = _to_cgminer_shape(data)
            doc["boards"] = _boards_from_stats(stats)
            doc["fans"] = _fans_from_stats(stats)
        # Pools: no stock CGI source — the bmminer RPC is the only
        # path; its failure IS the section's reason (mapping §3).
        try:
            doc["pools"] = _pools_from_rpc(CgminerClient(
                ip, port=cand.cgminer_port, timeout=fetch_timeout))
        except CgminerError as exc:
            doc["pools"] = _unsupported(
                "stock web CGI exposes no pool list; "
                f"cgminer RPC pools failed: {exc}")
        return doc

    # cgminer (also the port-open-but-silent fallback candidate —
    # its sections then fail honestly, one by one).
    client = CgminerClient(ip, port=cand.cgminer_port,
                           timeout=fetch_timeout)
    try:
        stats = client.stats()
        doc["boards"] = _boards_from_stats(stats)
        doc["fans"] = _fans_from_stats(stats)
    except CgminerError as exc:
        reason = str(exc)
        doc["boards"] = _unsupported(reason)
        doc["fans"] = _unsupported(reason)
    try:
        doc["pools"] = _pools_from_rpc(client)
    except CgminerError as exc:
        doc["pools"] = _unsupported(str(exc))
    return doc
