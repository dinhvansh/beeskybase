"""Auradine (Teraflux) adapter — cgminer RPC 4028 + web API :8080.

Source: docs/vendor-docs2-mapping.md §1 — asic-rs
``asic-rs-firmwares/auradine`` (RPC + web backends, real
test-JSON fixtures for every command) and pyasic
(``backends/auradine.py``, ``web/auradine.py``,
``rpc/gcminer.py``), CORROBORATED; the Auradine Hardware
Reference confirms the ports (80/443/4028 TCP API/8443
REST API).

Transport: RPC is plain cgminer-JSON on TCP 4028
(``{"command": ...}\\n``, STATUS array); the web API is
HTTP :8080 with token auth — POST ``/token``
``{"command": "token", "user": ..., "password": ...}``
→ token at ``/Token/0/Token``; later requests carry a
``Token`` header. Reads (no params) ride GET; writes
ride POST with ``{"command": ..., ...params}`` (a bare
string param rides ``"parameter"``). Default auth
admin/admin, agreed by both libraries.

Detection (mapping §1.2, divergence D-AU1): the
``version`` reply contains "gcminer" or "fluxos"
(case-insensitive — asic-rs checks case-sensitively
but its own fixtures carry "GCMiner"/"FluxOS").

Reads ride RPC (summary/devs/asccount/pools/devdetails)
with web enrichment best-effort (ipreport/fan/psu/
temperature). The native rate is MH/s (``summary``
"MHS 5s"/"MHS av", v0.20 discipline); chips are
AsicCount/BoardCount per board with asic-rs's
expected-minus-failed rule for the temperature data.

Known limits (mapping §1.6): no live-miner session
yet (U-AU1); the :8443 REST API shapes are unknown
(U-AU2); fixture rate magnitudes look like a dev unit
(U-AU3); set_fan_speed is not wired — only a per-fan
form exists and BeeSky's task carries no fan selector.
"""

from __future__ import annotations

import http.client
import json
import re

from . import report
from .cgminer import CgminerClient, CgminerError, pools_normalised_from

DEFAULT_PORT = 4028
DEFAULT_WEB_PORT = 8080
DEFAULT_USERNAME = "admin"
# Both libraries agree: the factory web credentials are admin/admin.
DEFAULT_PASSWORD = "admin"

# A 401, or a STATUS error naming the token/session, means the
# token expired — re-authenticate once and retry (asic-rs web.rs).
_TOKEN_ERROR_WORDS = ("TOKEN", "SESSION", "EXPIRED", "UNAUTHORIZED")


class AuradineError(Exception):
    """Raised when an Auradine miner cannot be reached or refuses."""


def is_auradine_version(resp: dict) -> bool:
    """Detection fingerprint (mapping §1.2, D-AU1): the
    ``version`` reply contains "gcminer" or "fluxos"
    (case-insensitive). Positive-only — no other family
    carries either substring ("cgminer" is not "gcminer")."""
    if not isinstance(resp, dict):
        return False
    haystack = json.dumps(resp, default=str).lower()
    return "gcminer" in haystack or "fluxos" in haystack


def _parse_units(value) -> float | None:
    """A number out of a units string ("58.94W", "4052.00 RPM")
    — asic-rs ``parse_number_from_units``: keep digits, dot,
    minus; a bare number passes through unchanged."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = "".join(ch for ch in str(value)
                      if ch.isascii() and (ch.isdigit() or ch in ".-"))
    if not cleaned or cleaned in (".", "-"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


class AuradineClient:
    """Client for one Auradine miner (RPC 4028 + web :8080)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 web_port: int = DEFAULT_WEB_PORT,
                 username: str = DEFAULT_USERNAME,
                 password: str = DEFAULT_PASSWORD,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.username = username
        self.password = password
        self.timeout = timeout
        self._cg = CgminerClient(host, port=port, timeout=timeout)
        self._token: str | None = None

    # -- web transport ------------------------------------------------------

    def _web_auth(self) -> str:
        """POST /token; the token lives at /Token/0/Token."""
        body = json.dumps({"command": "token", "user": self.username,
                           "password": self.password}).encode("utf-8")
        try:
            conn = http.client.HTTPConnection(
                self.host, self.web_port, timeout=self.timeout)
            try:
                conn.request("POST", "/token", body=body, headers={
                    "Content-Type": "application/json"})
                resp = conn.getresponse()
                raw = resp.read()
                if resp.status != 200:
                    raise AuradineError(
                        f"POST /token -> HTTP {resp.status}")
            finally:
                conn.close()
        except AuradineError:
            raise
        except OSError as exc:
            raise AuradineError(
                f"cannot reach {self.host}:{self.web_port} ({exc})") from exc
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise AuradineError(
                f"unparseable token reply: {exc}") from exc
        try:
            token = payload["Token"][0]["Token"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AuradineError(
                "missing /Token/0/Token in token response") from exc
        if not isinstance(token, str) or not token:
            raise AuradineError("empty token in token response")
        self._token = token
        return token

    def _web_once(self, method: str, command: str,
                  params=None) -> dict:
        """One web request with the current token (no retry)."""
        if self._token is None:
            self._web_auth()
        if method == "POST":
            if params is None:
                body = {"command": command}
            elif isinstance(params, dict):
                body = {"command": command, **params}
            else:
                body = {"command": command, "parameter": params}
            raw_body = json.dumps(body).encode("utf-8")
            headers = {"Content-Type": "application/json",
                       "Token": self._token}
        else:
            raw_body = None
            headers = {"Token": self._token}
        try:
            conn = http.client.HTTPConnection(
                self.host, self.web_port, timeout=self.timeout)
            try:
                conn.request(method, f"/{command}", body=raw_body,
                             headers=headers)
                resp = conn.getresponse()
                raw = resp.read()
                status = resp.status
            finally:
                conn.close()
        except OSError as exc:
            raise AuradineError(
                f"cannot reach {self.host}:{self.web_port} ({exc})") from exc
        if status == 401:
            raise _TokenExpired("HTTP 401 from web API")
        if status != 200:
            raise AuradineError(
                f"{method} /{command} -> HTTP {status}")
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise AuradineError(
                f"unparseable reply from /{command}: {exc}") from exc
        if not isinstance(payload, dict):
            raise AuradineError(f"unexpected reply shape from /{command}")
        status_list = payload.get("STATUS")
        if isinstance(status_list, list) and status_list \
                and isinstance(status_list[0], dict):
            head = status_list[0]
            if head.get("STATUS") == "E":
                msg = str(head.get("Msg") or head.get("Description") or "")
                if any(word in msg.upper() for word in _TOKEN_ERROR_WORDS):
                    raise _TokenExpired(msg)
                raise AuradineError(f"/{command} refused: {msg}")
        return payload

    def _web(self, method: str, command: str, params=None) -> dict:
        """A web request with one token re-auth on expiry
        (asic-rs web.rs: 401 or a TOKEN/SESSION/EXPIRED/
        UNAUTHORIZED error re-authenticates once)."""
        try:
            return self._web_once(method, command, params)
        except _TokenExpired:
            self._token = None
            return self._web_once(method, command, params)

    def web_get(self, command: str) -> dict:
        """GET one web endpoint (reads carry no params)."""
        return self._web("GET", command)

    def web_post(self, command: str, params=None) -> dict:
        """POST one web command (writes carry params)."""
        return self._web("POST", command, params)

    def _web_best_effort(self, command: str) -> dict | None:
        """A web read that costs the field, never the record."""
        try:
            return self.web_get(command)
        except AuradineError:
            return None

    # -- detection ----------------------------------------------------------

    def version(self) -> dict:
        """The full ``version`` RPC reply (detection reads this)."""
        return self._cg.command("version")

    def is_auradine(self) -> bool:
        """True when this host answers like an Auradine miner."""
        try:
            return is_auradine_version(self.version())
        except CgminerError:
            return False

    # -- reads ---------------------------------------------------------------

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        RPC reads always (summary/devs/asccount); pools and
        devdetails are best-effort enrichments; the web calls
        (ipreport/fan/psu/temperature) degrade the fields they
        feed, never the record (mapping §1.3–§1.5).
        """
        ip = ip or self.host
        try:
            summary = self._cg.summary()
            devs_resp = self._cg.command("devs")
            asccount_resp = self._cg.command("asccount")
        except CgminerError as exc:
            raise AuradineError(str(exc)) from exc
        pools_resp = None
        try:
            pools_resp = self._cg.pools()
        except CgminerError:
            pools_resp = None
        devdetails_resp = None
        try:
            devdetails_resp = self._cg.command("devdetails")
        except CgminerError:
            devdetails_resp = None

        # --- rate + uptime --------------------------------------------------
        mhs_5s = report._num(summary.get("MHS 5s"))
        mhs_av = report._num(summary.get("MHS av"))
        gh_5s = mhs_5s / 1000.0 if mhs_5s is not None else None
        gh_av = mhs_av / 1000.0 if mhs_av is not None else None
        if mhs_av is not None:
            rate_value, rate_unit = mhs_av / 1_000_000.0, "TH/s"
        else:
            rate_value, rate_unit = None, None
        elapsed = int(report._num(summary.get("Elapsed"), 0) or 0)

        # --- model ----------------------------------------------------------
        model = "Auradine"
        devdetails = devdetails_resp.get("DEVDETAILS") \
            if isinstance(devdetails_resp, dict) else None
        if isinstance(devdetails, list) and devdetails \
                and isinstance(devdetails[0], dict):
            model = str(devdetails[0].get("Model") or model)

        # --- web enrichment (best-effort) -----------------------------------
        ipreport = self._web_best_effort("ipreport")
        fan_resp = self._web_best_effort("fan")
        psu_resp = self._web_best_effort("psu")
        temp_resp = self._web_best_effort("temperature")
        if isinstance(ipreport, dict):
            ipr = ipreport.get("IPReport")
            if isinstance(ipr, list) and ipr and isinstance(ipr[0], dict):
                if model == "Auradine" and ipr[0].get("model"):
                    model = str(ipr[0]["model"])

        # --- chips per board (asic-rs expected-minus-failed rule) -----------
        asccount = asccount_resp.get("ASCCount") \
            if isinstance(asccount_resp, dict) else None
        chips_per_board = 0
        board_count = 0
        if isinstance(asccount, list) and asccount \
                and isinstance(asccount[0], dict):
            chips_per_board = int(
                report._num(asccount[0].get("AsicCount"), 0) or 0) // max(
                    int(report._num(asccount[0].get("BoardCount"), 1) or 1), 1)
            board_count = int(
                report._num(asccount[0].get("BoardCount"), 0) or 0)
        # Chip-level working data from the temperature endpoint:
        # a chip is working when temp > 0 or voltage > 0 or
        # frequency > 0; failed = present-but-not-working.
        chip_working: dict[int, dict[int, bool]] = {}
        if isinstance(temp_resp, dict):
            temp_list = temp_resp.get("Temperature")
            if isinstance(temp_list, list):
                for entry in temp_list:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        board_id = int(entry.get("ID"))
                    except (TypeError, ValueError):
                        continue
                    if board_id < 1:
                        continue  # ID 0 is the control board
                    for chip in entry.get("ChipTemp") or []:
                        if not isinstance(chip, dict):
                            continue
                        try:
                            chip_id = int(chip.get("ID"))
                        except (TypeError, ValueError):
                            continue
                        temp = report._num(chip.get("Temperature"))
                        working = temp is not None and temp > 0
                        chip_working.setdefault(board_id, {})[chip_id] = working
        volt_resp = self._web_best_effort("voltage")
        freq_resp = self._web_best_effort("frequency")
        if isinstance(volt_resp, dict):
            for entry in volt_resp.get("Voltage") or []:
                if not isinstance(entry, dict):
                    continue
                try:
                    board_id = int(entry.get("ID"))
                except (TypeError, ValueError):
                    continue
                if board_id < 1:
                    continue
                for chip in entry.get("ChipVoltage") or []:
                    if not isinstance(chip, dict):
                        continue
                    try:
                        chip_id = int(chip.get("ID"))
                    except (TypeError, ValueError):
                        continue
                    volt = report._num(chip.get("Voltage"))
                    if volt is not None and volt > 0:
                        chip_working.setdefault(board_id, {})[chip_id] = True
        if isinstance(freq_resp, dict):
            for entry in freq_resp.get("Frequency") or []:
                if not isinstance(entry, dict):
                    continue
                try:
                    board_id = int(entry.get("ID"))
                except (TypeError, ValueError):
                    continue
                if board_id < 1:
                    continue
                for chip in entry.get("ChipFrequency") or []:
                    if not isinstance(chip, dict):
                        continue
                    try:
                        chip_id = int(chip.get("ID"))
                    except (TypeError, ValueError):
                        continue
                    freq = report._num(chip.get("Frequency"))
                    if freq is not None and freq > 0:
                        chip_working.setdefault(board_id, {})[chip_id] = True

        # --- boards ---------------------------------------------------------
        chains: list[dict] = []
        devs_list = devs_resp.get("DEVS") \
            if isinstance(devs_resp, dict) else None
        if isinstance(devs_list, list):
            for entry in devs_list:
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(entry.get("ID", entry.get("DEV")))
                except (TypeError, ValueError):
                    continue
                total = chips_per_board
                failed = sum(1 for working in
                             chip_working.get(idx, {}).values()
                             if not working)
                chains.append({
                    "index": idx,
                    "chips_total": total,
                    "chips_alive": max(total - failed, 0),
                    "dead_positions": [],
                    "temp_c": report._num(entry.get("Temperature")),
                })
        if not chains and board_count:
            # No devs reply — fall back to the board count alone.
            for idx in range(1, board_count + 1):
                failed = sum(1 for working in
                             chip_working.get(idx, {}).values()
                             if not working)
                chains.append({
                    "index": idx,
                    "chips_total": chips_per_board,
                    "chips_alive": max(chips_per_board - failed, 0),
                    "dead_positions": [],
                    "temp_c": None,
                })

        # --- fans + power ---------------------------------------------------
        fans: list[int] = []
        if isinstance(fan_resp, dict):
            fan_list = fan_resp.get("Fan")
            if isinstance(fan_list, list):
                for entry in fan_list:
                    if not isinstance(entry, dict):
                        continue
                    rpm = _parse_units(entry.get("Speed"))
                    if rpm is not None:
                        fans.append(int(rpm))
        power_w = report._num(summary.get("Wattage"))
        if power_w is None and isinstance(psu_resp, dict):
            psu_list = psu_resp.get("PSU")
            if isinstance(psu_list, list) and psu_list \
                    and isinstance(psu_list[0], dict):
                power_w = _parse_units(psu_list[0].get("PowerIn"))

        record = report._finalise_record(
            ip, model, elapsed, gh_5s, gh_av, chains, fans,
            "auradine", power_w=power_w,
            rate_value=rate_value, rate_unit=rate_unit)
        if isinstance(ipreport, dict):
            ipr = ipreport.get("IPReport")
            if isinstance(ipr, list) and ipr and isinstance(ipr[0], dict):
                head = ipr[0]
                if isinstance(head.get("hostname"), str) and head["hostname"]:
                    record["hostname"] = head["hostname"]
                if isinstance(head.get("mac"), str) and head["mac"]:
                    record["mac"] = head["mac"]
                if isinstance(head.get("SerialNo"), str) and head["SerialNo"]:
                    record["serial"] = head["SerialNo"]
        # Board temperature spread from the temperature endpoint
        # (inlet/outlet = min/max of the hash-board BoardTemp
        # values, asic-rs rule) — present only when the web call
        # succeeded; never invented.
        board_temps: list[float] = []
        if isinstance(temp_resp, dict):
            for entry in temp_resp.get("Temperature") or []:
                if not isinstance(entry, dict):
                    continue
                try:
                    board_id = int(entry.get("ID"))
                except (TypeError, ValueError):
                    continue
                if board_id < 1:
                    continue
                for sensor in entry.get("BoardTemp") or []:
                    if not isinstance(sensor, dict):
                        continue
                    temp = report._num(sensor.get("Temperature"))
                    if temp is not None and temp > 0:
                        board_temps.append(temp)
        if board_temps:
            record["board_temp_min_c"] = min(board_temps)
            record["board_temp_max_c"] = max(board_temps)
        accepted = report._num(summary.get("Accepted"))
        rejected = report._num(summary.get("Rejected"))
        if accepted is not None:
            record["accepted"] = accepted
        if rejected is not None:
            record["rejected"] = rejected
        pools = pools_normalised_from(pools_resp) if pools_resp else None
        if pools is not None:
            record["pools"] = pools
        return record

    # -- actions (documented / library-verified params only) ---------------

    def reboot(self) -> dict:
        """Full device reboot: POST `restart` with no params
        (asic-rs Restart, pyasic reboot)."""
        return self.web_post("restart")

    def restart_mining(self) -> dict:
        """Restart only the mining program: POST `restart` with
        param "gcminer" (asic-rs, pyasic restart_gcminer)."""
        return self.web_post("restart", "gcminer")

    def set_sleep(self, on: bool) -> dict:
        """Sleep the miner (pause) or wake it (resume): POST
        `mode` {"sleep": "on"/"off"} (asic-rs Pause/Resume,
        pyasic stop/resume_mining)."""
        return self.web_post("mode", {"sleep": "on" if on else "off"})

    def set_fault_light(self, on: bool) -> dict:
        """Locate LED on (code 3) / off (code 2): POST `led`
        {"code": ...} (asic-rs SetFaultLight, pyasic
        fault_light_on/off)."""
        return self.web_post("led", {"code": 3 if on else 2})

    def set_power_limit(self, watts: int) -> dict:
        """Target power in watts: POST `mode` {"mode": "custom",
        "tune": "power", "power": <watts>} (asic-rs
        SetPowerLimit, pyasic set_power_limit)."""
        if int(watts) < 0:
            raise AuradineError(
                f"target power must be >= 0, got {watts!r}")
        return self.web_post("mode", {"mode": "custom",
                                      "tune": "power",
                                      "power": int(watts)})

    def set_pools(self, pools: list[dict]) -> dict:
        """Rewrite the pool list (max 3): POST `updatepools`
        {"pools": [{url, user, pass}]} — an empty password
        becomes "x" (asic-rs build_update_pools_payload)."""
        if not pools or len(pools) > 3:
            raise AuradineError("set_pools needs 1-3 pools")
        norm = []
        for entry in pools:
            if not isinstance(entry, dict) or not entry.get("url"):
                raise AuradineError("set_pools entries need a 'url'")
            password = str(entry.get("password") or "")
            norm.append({
                "url": str(entry["url"]),
                "user": str(entry.get("user") or ""),
                "pass": password if password else "x",
            })
        return self.web_post("updatepools", {"pools": norm})


class _TokenExpired(AuradineError):
    """Internal: the token expired — re-authenticate once."""
