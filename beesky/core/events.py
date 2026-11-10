"""Event engine — turns successive status records into fleet events.

The scanner is a snapshot tool; *watch mode* feeds it the same normalised
record (see :mod:`beesky.core.report`) once per interval, and this engine
diffs each miner against its own history to emit events:

  OFFLINE        a miner that was seen before stops answering
  BACK_ONLINE    a miner returns after an OFFLINE
  HASHRATE_DROP  hashrate fell vs the miner's own rolling baseline
  OVER_TEMP      max temp rose vs baseline, or crossed the absolute limit
  CHIPS_LOST     alive-chip count decreased vs the previous record
  CHAIN_DOWN     a chain that had chips now reports 0

Two-layer design, borrowed from EMCD Monitoring (researched 2026-11-09):
*detection* is sensitive — a >5 % hashrate drop or >5 °C rise vs baseline
already detects — while *severity* follows EMCD's 3-step scales
(15/30/50 % and 10/20/30 °C → warning/major/critical, below the first step
is ``info``). The notify layer (:mod:`beesky.core.notify`) then gates on
severity, exactly like EMCD's notification thresholds gate the raw
5 %-level events their platform detects.

Anti-flap: each (miner, event type) pair has a latch. A level-triggered
condition (drop still in progress, miner still offline) fires once, then
stays latched until the condition clears; a fresh episode inside the
cooldown window after a fire is swallowed instead of spamming channels.

The engine is pure state + diffing: feed it one *cycle* at a time with
:meth:`EventEngine.observe_cycle`, and persist :meth:`EventEngine.state`
between runs (the CLI does this with ``--state``) so one-shot invocations
detect changes too. State is plain JSON data.
"""

from __future__ import annotations

import statistics
import time

SEVERITIES = ("info", "warning", "major", "critical")

EVENT_TYPES = (
    "OFFLINE", "BACK_ONLINE", "HASHRATE_DROP",
    "OVER_TEMP", "CHIPS_LOST", "CHAIN_DOWN",
)

DEFAULT_CONFIG = {
    "cooldown_s": 300,          # min seconds between two fires of one type
    "baseline_window": 12,      # rolling samples kept per miner
    "baseline_min_samples": 3,  # samples needed before deviation checks
    "drop_floor_pct": 5.0,      # EMCD-style detection floor (hashrate)
    "temp_rise_floor_c": 5.0,   # EMCD-style detection floor (temperature)
    "over_temp_abs_c": 85.0,    # absolute red-line (matches report.TEMP_LIMIT_C)
    "drop_steps_pct": (15.0, 30.0, 50.0),   # → warning / major / critical
    "temp_steps_c": (10.0, 20.0, 30.0),     # → warning / major / critical
}


def severity_rank(severity: str) -> int:
    return SEVERITIES.index(severity)


def _rate_value(record: dict):
    """(value, unit) of the record's rate for drop tracking (v0.20).

    The drop check is a ratio against the miner's OWN rolling
    baseline, so it stays unit-safe as long as one miner is tracked
    in one consistent series: the record's native rate when it
    carries one (L9 in MH/s, Z15 in ksol/s), else the historical
    ``ths`` series with its ``ghs_av`` fallback. Event payloads keep
    the legacy ``baseline_ths`` / ``current_ths`` key names — for
    non-SHA256 miners they carry the tracked native-scale values.
    """
    value = record.get("rate_value")
    if value is not None:
        return float(value), str(record.get("rate_unit") or "TH/s")
    cur = record.get("ths")
    if cur is None and record.get("ghs_av") is not None:
        cur = record["ghs_av"] / 1000.0
    return (float(cur) if cur is not None else None), "TH/s"


def _step_severity(value: float, steps) -> str:
    """Map a deviation onto the 3-step scale (below step 1 = info)."""
    if value >= steps[2]:
        return "critical"
    if value >= steps[1]:
        return "major"
    if value >= steps[0]:
        return "warning"
    return "info"


def _max_severity(*severities: str) -> str:
    return max(severities, key=severity_rank)


def _event(now: float, record_or_state: dict, etype: str, severity: str,
           detail: str, data: dict) -> dict:
    return {
        "ts": now,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
        "ip": record_or_state["ip"],
        "model": record_or_state.get("model", "Unknown"),
        "source": record_or_state.get("source"),
        "type": etype,
        "severity": severity,
        "detail": detail,
        "data": data,
    }


class EventEngine:
    """Diffs successive per-miner status records into events."""

    def __init__(self, config: dict | None = None):
        self.cfg = dict(DEFAULT_CONFIG)
        if config:
            self.cfg.update({k: v for k, v in config.items()
                             if k in DEFAULT_CONFIG})
        self.cfg["drop_steps_pct"] = tuple(self.cfg["drop_steps_pct"])
        self.cfg["temp_steps_c"] = tuple(self.cfg["temp_steps_c"])
        self._miners: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # state persistence (plain JSON)
    # ------------------------------------------------------------------

    def state(self) -> dict:
        return {"miners": self._miners}

    def load_state(self, state: dict) -> None:
        if isinstance(state, dict) and isinstance(state.get("miners"), dict):
            self._miners = state["miners"]

    def known_ips(self) -> list[str]:
        return sorted(self._miners)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _new_miner_state(self, record: dict, now: float) -> dict:
        return {
            "ip": record["ip"],
            "model": record.get("model", "Unknown"),
            "source": record.get("source"),
            "online": True,
            "last_seen": now,
            "hr_hist": [],
            "temp_hist": [],
            "chips_alive": record.get("chips_alive"),
            "chains": {str(c["index"]): c["chips_alive"]
                       for c in record.get("chains", [])},
            "latch": {},
        }

    def _should_fire(self, st: dict, etype: str, triggered: bool,
                     now: float) -> bool:
        """Latch + cooldown gate. Returns True exactly once per episode."""
        latch = st["latch"].setdefault(
            etype, {"active": False, "last_fired": None})
        if not triggered:
            latch["active"] = False
            return False
        if latch["active"]:
            return False
        latch["active"] = True
        last = latch["last_fired"]
        if last is not None and now - last < float(self.cfg["cooldown_s"]):
            return False  # re-triggered inside cooldown: swallow, stay latched
        latch["last_fired"] = now
        return True

    def _baseline(self, hist: list[float]):
        if len(hist) < int(self.cfg["baseline_min_samples"]):
            return None
        return statistics.median(hist)

    def _push(self, hist: list[float], value) -> None:
        if value is None:
            return
        hist.append(float(value))
        window = int(self.cfg["baseline_window"])
        if len(hist) > window:
            del hist[: len(hist) - window]

    # ------------------------------------------------------------------
    # main entry point
    # ------------------------------------------------------------------

    def observe_cycle(self, present: dict[str, dict],
                      now: float | None = None) -> list[dict]:
        """Feed one scan pass; return the events it produced.

        *present* maps IP → status record for every miner that answered
        this pass. Any previously-known miner missing from the mapping
        (not discovered, or its fetch failed) counts as unreachable.
        First sightings only seed history — they never emit events.
        """
        now = time.time() if now is None else float(now)
        events: list[dict] = []

        # --- miners that vanished --------------------------------------
        for ip, st in self._miners.items():
            if ip in present:
                continue
            was_online = st["online"]
            st["online"] = False
            if was_online and self._should_fire(st, "OFFLINE", True, now):
                events.append(_event(
                    now, st, "OFFLINE", "critical",
                    "miner went offline / unreachable",
                    {"last_seen": st["last_seen"]}))
            elif not was_online:
                self._should_fire(st, "OFFLINE", True, now)  # keep latch warm

        # --- miners that answered --------------------------------------
        for ip, record in present.items():
            st = self._miners.get(ip)
            if st is None:
                st = self._new_miner_state(record, now)
                self._miners[ip] = st
                self._push(st["hr_hist"], _rate_value(record)[0])
                self._push(st["temp_hist"], record.get("max_temp_c"))
                continue

            st["model"] = record.get("model", st["model"])
            st["source"] = record.get("source", st["source"])
            st["last_seen"] = now
            self._should_fire(st, "OFFLINE", False, now)  # clear offline latch

            if not st["online"]:
                st["online"] = True
                events.append(_event(
                    now, record, "BACK_ONLINE", "info",
                    "miner is back online", {}))

            events.extend(self._check_hashrate(st, record, now))
            events.extend(self._check_temp(st, record, now))
            events.extend(self._check_chains(st, record, now))

        return events

    # ------------------------------------------------------------------
    # per-miner checks (each updates its own history afterwards)
    # ------------------------------------------------------------------

    def _check_hashrate(self, st: dict, record: dict, now: float) -> list[dict]:
        cur, unit = _rate_value(record)
        baseline = self._baseline(st["hr_hist"])
        fired: list[dict] = []
        drop_pct = None
        if cur is not None and baseline:
            drop_pct = (baseline - cur) / baseline * 100.0
        triggered = drop_pct is not None and drop_pct >= float(
            self.cfg["drop_floor_pct"])
        if self._should_fire(st, "HASHRATE_DROP", triggered, now):
            severity = _step_severity(drop_pct, self.cfg["drop_steps_pct"])
            fired.append(_event(
                now, record, "HASHRATE_DROP", severity,
                f"hashrate dropped {drop_pct:.1f}% vs baseline "
                f"({baseline:.2f} -> {cur:.2f} {unit})",
                {"baseline_ths": round(baseline, 2),
                 "current_ths": round(float(cur), 2),
                 "drop_pct": round(drop_pct, 1)}))
        self._push(st["hr_hist"], cur)
        return fired

    def _check_temp(self, st: dict, record: dict, now: float) -> list[dict]:
        cur = record.get("max_temp_c")
        baseline = self._baseline(st["temp_hist"])
        fired: list[dict] = []
        rise = None
        if cur is not None and baseline is not None:
            rise = float(cur) - baseline
        limit = float(self.cfg["over_temp_abs_c"])
        over_abs = cur is not None and cur >= limit
        triggered = over_abs or (
            rise is not None and rise >= float(self.cfg["temp_rise_floor_c"]))
        if self._should_fire(st, "OVER_TEMP", triggered, now):
            severities = []
            if rise is not None and rise >= float(self.cfg["temp_rise_floor_c"]):
                severities.append(
                    _step_severity(rise, self.cfg["temp_steps_c"]))
            if over_abs:
                overshoot = float(cur) - limit
                severities.append("critical" if overshoot >= 20
                                  else "major" if overshoot >= 10
                                  else "warning")
            if rise is not None and rise >= float(self.cfg["temp_rise_floor_c"]):
                detail = (f"max temp {cur:.0f} C, up {rise:.0f} C vs "
                          f"baseline {baseline:.0f} C")
            else:
                detail = f"max temp {cur:.0f} C >= {limit:.0f} C limit"
            fired.append(_event(
                now, record, "OVER_TEMP", _max_severity(*severities),
                detail,
                {"temp_c": float(cur),
                 "baseline_temp_c": (round(baseline, 1)
                                     if baseline is not None else None),
                 "rise_c": (round(rise, 1) if rise is not None else None),
                 "limit_c": limit}))
        self._push(st["temp_hist"], cur)
        return fired

    def _check_chains(self, st: dict, record: dict, now: float) -> list[dict]:
        fired: list[dict] = []
        chains = record.get("chains") or []
        if not chains:
            return fired  # this API gave no per-chain data; nothing to diff
        prev = st["chains"]
        new = {str(c["index"]): c["chips_alive"] for c in chains}

        down = sorted(
            int(idx) for idx, alive in prev.items()
            if alive > 0 and new.get(idx, 0) == 0)
        if self._should_fire(st, "CHAIN_DOWN", bool(down), now):
            fired.append(_event(
                now, record, "CHAIN_DOWN", "critical",
                f"chain(s) {', '.join(map(str, down))} stopped responding "
                f"(0 chips)",
                {"chains": down}))

        # Chips lost on chains that are still alive (fully-down chains are
        # reported as CHAIN_DOWN, not double-counted here).
        lost = sum(max(0, prev[idx] - new[idx])
                   for idx in prev.keys() & new.keys() if new[idx] > 0)
        prev_alive = st["chips_alive"]
        if self._should_fire(st, "CHIPS_LOST", lost > 0, now):
            frac = lost / prev_alive if prev_alive else 0.0
            severity = ("critical" if frac >= 0.25
                        else "major" if frac >= 0.05 else "warning")
            fired.append(_event(
                now, record, "CHIPS_LOST", severity,
                f"lost {lost} chip(s) "
                f"({prev_alive} -> {record.get('chips_alive')} alive)",
                {"chips_before": prev_alive,
                 "chips_after": record.get("chips_alive"),
                 "lost": lost}))

        st["chains"] = new
        st["chips_alive"] = record.get("chips_alive")
        return fired
