"""Braiins OS (BOSMiner) adapter — TCP 4028 cgminer-compatible API.

Source: docs/vendor-oss-mapping.md §1 — the fingerprint and the read
contract are CORROBORATED three ways:

  * Braiins Academy's BOSminer API page (official docs, worked
    examples): every 4028 reply carries
    ``STATUS[0].Description == "BOSminer+ <version>"``; the command
    list (summary / pools / fans / temps / tunerstatus / devdetails /
    devs / pause / resume) and the worked payloads for fans, temps,
    tunerstatus and devdetails are quoted there;
  * pyasic (``pyasic/miners/backends/braiins_os.py``,
    ``pyasic/rpc/bosminer.py``, ``pyasic/miners/factory.py``) — the
    BOSMiner handler reads everything over this RPC, and its factory
    detects a Braiins machine by the substring "BOSMINER" or "BOSER"
    in the ``version``/``devdetails`` reply;
  * asic-rs implements the identical "BOSMINER or BOSER" fingerprint.

Reads ride the shared CgminerClient (same envelope as stock cgminer:
``{"command": name}`` + optional ``"parameter"``). No auth for reads.
The gRPC PAPI (port 50051) is deliberately NOT used — no stdlib
HTTP/2 + protobuf (mapping U-B3); the 4028 route covers the fields
BeeSky displays. Reboot is not a 4028 command (pyasic reboots via
SSH, which BeeSky has no path for) — it stays unsupported.
"""

from __future__ import annotations

import json

from . import report
from .cgminer import CgminerClient, CgminerError

DEFAULT_PORT = 4028

# Tuner chain states pyasic treats as healthy (braiins_os.py
# _get_errors); anything else on a chain is a TUNER problem.
_TUNER_OK_STATES = ("Stable", "Testing performance profile",
                    "Tuning individual chips")


class BraiinsError(Exception):
    """Raised when a Braiins OS miner cannot be reached or refuses."""


def is_braiins_version(resp: dict) -> bool:
    """Detection fingerprint (mapping §1.2): the ``version`` reply
    contains "bosminer" or "boser" (case-insensitive).

    The Academy's worked examples put the build string in
    ``STATUS[0].Description`` ("BOSminer+ 0.2.0-ea64aec8e"); pyasic
    and asic-rs match the substring across the whole reply, so
    BeeSky does the same. Positive-only — stock answers
    "cgminer …" / "bmminer …", LuxOS "LUXminer …", and neither
    substring occurs in any of them.
    """
    try:
        text = json.dumps(resp)
    except (TypeError, ValueError):
        return False
    lowered = text.lower()
    return "bosminer" in lowered or "boser" in lowered


def _status_ok(resp: dict) -> tuple[bool, str]:
    """(accepted?, message) from a bosminer STATUS section."""
    status = resp.get("STATUS")
    if isinstance(status, list) and status \
            and isinstance(status[0], dict):
        head = status[0]
        if head.get("STATUS") == "S":
            return True, str(head.get("Msg") or "ok")
        return False, str(head.get("Msg") or
                          f"STATUS {head.get('STATUS')}")
    return False, "no STATUS section in reply"


def _board_offset(first_id) -> int:
    """pyasic's chain-ID offset: S9-style chains are numbered 6–8,
    everything else 1-based (braiins_os.py _get_hashboards)."""
    try:
        return 6 if int(first_id) in (6, 7, 8) else 1
    except (TypeError, ValueError):
        return 1


class BraiinsClient:
    """Client for one Braiins OS miner's BOSMiner RPC API (port 4028)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._cg = CgminerClient(host, port=port, timeout=timeout)

    # -- reads ------------------------------------------------------------

    def version(self) -> dict:
        """The full ``version`` reply (detection reads this)."""
        try:
            return self._cg.command("version")
        except CgminerError as exc:
            raise BraiinsError(str(exc)) from exc

    def is_braiins(self) -> bool:
        """True when this host answers like a Braiins OS miner."""
        try:
            return is_braiins_version(self.version())
        except BraiinsError:
            return False

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        Rate truth (mapping §1.3): pyasic reads ``"MHS 1m"`` from
        summary — MHS / 1e6 is the native TH/s rate (the legacy
        ``ghs_*`` fields carry MHS / 1000). Boards come from
        temps + devdetails + devs with pyasic's ID-offset rule;
        power from tunerstatus. Any failure is a BraiinsError —
        the fetch stages turn it into an error record.
        """
        ip = ip or self.host
        try:
            summary = self._cg.summary()
            pools_resp = self._cg.pools()
            fans_resp = self._cg.command("fans")
            temps_resp = self._cg.command("temps")
            devdetails_resp = self._cg.command("devdetails")
            devs_resp = self._cg.command("devs")
            tuner_resp = self._cg.command("tunerstatus")
        except CgminerError as exc:
            raise BraiinsError(str(exc)) from exc

        # --- rate + uptime ----------------------------------------------
        mhs_main = None
        for key in ("MHS 1m", "MHS 5s", "MHS av"):
            val = report._num(summary.get(key))
            if val is not None:
                mhs_main = val
                break
        mhs_5s = report._num(summary.get("MHS 5s"))
        mhs_av = report._num(summary.get("MHS av"))
        gh_5s = mhs_5s / 1000.0 if mhs_5s is not None else None
        gh_av = mhs_av / 1000.0 if mhs_av is not None else None
        if mhs_main is not None:
            rate_value, rate_unit = mhs_main / 1_000_000.0, "TH/s"
        else:
            rate_value, rate_unit = None, None
        elapsed = int(report._num(summary.get("Elapsed"), 0) or 0)

        # --- model --------------------------------------------------------
        model = "Braiins OS"
        devdetails = devdetails_resp.get("DEVDETAILS")
        if isinstance(devdetails, list) and devdetails \
                and isinstance(devdetails[0], dict):
            model = str(devdetails[0].get("Model") or model)

        # --- boards -------------------------------------------------------
        temps: dict[int, dict] = {}
        temps_list = temps_resp.get("TEMPS")
        if isinstance(temps_list, list) and temps_list:
            offset = _board_offset(temps_list[0].get("ID"))
            for entry in temps_list:
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(entry.get("ID")) - offset
                except (TypeError, ValueError):
                    continue
                temps[idx] = {
                    "chip": report._num(entry.get("Chip")),
                    "board": report._num(entry.get("Board")),
                }
        chips: dict[int, int] = {}
        if isinstance(devdetails, list) and devdetails:
            offset = _board_offset(devdetails[0].get("ID"))
            for entry in devdetails:
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(entry.get("ID")) - offset
                    count = int(report._num(entry.get("Chips")) or 0)
                except (TypeError, ValueError):
                    continue
                chips[idx] = count
        rates: dict[int, float | None] = {}
        devs_list = devs_resp.get("DEVS")
        if isinstance(devs_list, list) and devs_list:
            offset = _board_offset(devs_list[0].get("ID"))
            for entry in devs_list:
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(entry.get("ID")) - offset
                except (TypeError, ValueError):
                    continue
                rates[idx] = report._num(entry.get("MHS 1m"))

        indexes = sorted(set(temps) | set(chips) | set(rates))
        chains: list[dict] = []
        for idx in indexes:
            total = chips.get(idx, 0)
            temp = temps.get(idx, {})
            chains.append({
                "index": idx + 1,
                "chips_total": total,
                "chips_alive": total,
                "dead_positions": [],
                "temp_c": temp.get("chip"),
            })

        # --- fans + power -------------------------------------------------
        fans: list[int] = []
        fans_list = fans_resp.get("FANS")
        if isinstance(fans_list, list):
            for entry in fans_list:
                if isinstance(entry, dict):
                    rpm = report._num(entry.get("RPM"))
                    if rpm is not None:
                        fans.append(int(rpm))
        power_w = None
        tuner = tuner_resp.get("TUNERSTATUS")
        tuner_head: dict = {}
        if isinstance(tuner, list) and tuner \
                and isinstance(tuner[0], dict):
            tuner_head = tuner[0]
            power_w = report._num(
                tuner_head.get("ApproximateMinerPowerConsumption"))

        record = report._finalise_record(
            ip, model, elapsed, gh_5s, gh_av, chains, fans,
            "braiins", power_w=power_w,
            rate_value=rate_value, rate_unit=rate_unit)

        # Tuner problems (pyasic _get_errors): a chain whose tuner
        # status is not a healthy state gets a TUNER problem; the
        # record status flips to CHECK with it.
        chain_status = tuner_head.get("TunerChainStatus")
        if isinstance(chain_status, list):
            offset = 0
            if chain_status and isinstance(chain_status[0], dict):
                try:
                    first = int(chain_status[0].get("HashchainIndex"))
                    offset = 6 if first in (6, 7, 8) else 0
                except (TypeError, ValueError):
                    offset = 0
            for entry in chain_status:
                if not isinstance(entry, dict):
                    continue
                state = str(entry.get("Status") or "")
                if state in _TUNER_OK_STATES or not state:
                    continue
                try:
                    idx = int(entry.get("HashchainIndex")) - offset + 1
                except (TypeError, ValueError):
                    idx = 0
                record["problems"].append({
                    "code": "TUNER", "chain": idx,
                    "detail": f"chain {idx}: tuner status "
                              f"'{state.split(' {')[0]}'",
                })
            if record["problems"]:
                record["status"] = "CHECK"

        pools = self._pools_normalised(pools_resp)
        if pools is not None:
            record["pools"] = pools
        return record

    def _pools_normalised(self, resp: dict) -> list[dict] | None:
        """The cgminer pools shape, via the shared normaliser
        (the reply is already in hand from fetch_record)."""
        from .cgminer import pools_normalised_from

        return pools_normalised_from(resp)

    # -- actions (documented commands only) --------------------------------

    def pause(self) -> dict:
        """Pause mining (Academy: ``pause`` command).

        pyasic's stop_mining requires a JSON reply carrying a
        non-empty "PAUSE" section — BeeSky requires the same.
        """
        try:
            resp = self._cg.command("pause")
        except CgminerError as exc:
            raise BraiinsError(f"pause failed: {exc}") from exc
        section = resp.get("PAUSE")
        if not (isinstance(section, list) and section):
            raise BraiinsError("pause refused: no PAUSE section in reply")
        return resp

    def resume(self) -> dict:
        """Resume mining after a pause (``resume`` command)."""
        try:
            resp = self._cg.command("resume")
        except CgminerError as exc:
            raise BraiinsError(f"resume failed: {exc}") from exc
        section = resp.get("RESUME")
        if not (isinstance(section, list) and section):
            raise BraiinsError("resume refused: no RESUME section in reply")
        return resp
