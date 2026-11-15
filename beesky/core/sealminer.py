"""SealMiner (Bitdeer) adapter — cgminer RPC 4028 + web CGI :80.

Source: docs/vendor-docs2-mapping.md §2 — asic-rs
``asic-rs-firmwares/sealminer`` (RPC 4028 + web CGI
backends, real test-JSON fixtures), CORROBORATED with
the Bitdeer setup guides for the web-UI facts the code
does not state (dashboard on :80, Sealminer Tool).

Transport: RPC is plain cgminer-JSON on TCP 4028
(``{"command": ...}\\n``, STATUS array); the web API is
HTTP :80 CGI — POST ``/cgi-bin/login.php`` with form
body ``username=<user>&origin_pwd=<pass>`` +
``X-Requested-With: XMLHttpRequest`` → session cookie
(first segment of ``set-cookie``); later calls are
GET/POST ``/cgi-bin/<command>.php`` with a ``Cookie``
header. Default auth seal/seal (asic-rs
``default_auth``; the setup guides disagree on case —
D-SE2: the code says lowercase "seal").

Detection (mapping §2.2, divergence D-SE1): the
``version`` reply contains "bdminer" (case-insensitive
— asic-rs checks case-sensitively but its own fixtures
carry "bdminer 4.11.1" / "BDMiner").

Reads ride RPC (summary/stats/pools/devdetails) with
web enrichment best-effort (get_system_info,
miner_psu_status). The native rate is MH/s (``summary``
"MHS 5s"/"MHS av", v0.20 discipline); boards come from
the flat stats object (``"<n> Chip Count"`` minus
``"<n> Bad Chip Count"``, temp = max of the non-zero
``"<n> Temp 0..3"``, intake = first, outlet = last —
asic-rs rules).

Known limits (mapping §2.6): the "amazeui" web
fingerprint is NOT used (U-SE1, suspected Avalon
collision); restart_mining is unsupported by the
vendor's own client (empty impl); change password /
logs / factory reset / firmware upgrade are
unsupported; the web numeric mining-mode values are
undocumented (U-SE3) — the RPC ``ascset`` form is
wired instead.
"""

from __future__ import annotations

import http.client
import json
import re
import urllib.parse

from . import report
from .cgminer import CgminerClient, CgminerError, pools_normalised_from

DEFAULT_PORT = 4028
DEFAULT_WEB_PORT = 80
DEFAULT_USERNAME = "seal"
# asic-rs default_auth(); the setup guides print SEAL/SEAL in one
# place and seal/seal in another — the code is ground truth (D-SE2).
DEFAULT_PASSWORD = "seal"

MINING_MODES = ("low_power", "normal", "high_performance")


class SealMinerError(Exception):
    """Raised when a SealMiner cannot be reached or refuses."""


def is_sealminer_version(resp: dict) -> bool:
    """Detection fingerprint (mapping §2.2, D-SE1): the
    ``version`` reply contains "bdminer" (case-insensitive).
    Positive-only — no other family carries it."""
    if not isinstance(resp, dict):
        return False
    haystack = json.dumps(resp, default=str).lower()
    return "bdminer" in haystack


def _status_ok(reply: dict, code: int | None = None) -> bool:
    """A cgminer STATUS head of "S" (and, when ``code`` is
    given, that exact Code — the ascset tuning replies need
    STATUS S + Code 119, asic-rs ``set_tuning_option``)."""
    status = reply.get("STATUS")
    if not isinstance(status, list) or not status \
            or not isinstance(status[0], dict):
        return False
    head = status[0]
    if head.get("STATUS") != "S":
        return False
    if code is not None and head.get("Code") != code:
        return False
    return True


class SealMinerClient:
    """Client for one SealMiner (RPC 4028 + web CGI :80)."""

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
        self._cookie: str | None = None

    # -- web transport ------------------------------------------------------

    def _web_login(self) -> str:
        """POST /cgi-bin/login.php; the session cookie is the
        first segment of the set-cookie header."""
        body = ("username=" + urllib.parse.quote_plus(self.username)
                + "&origin_pwd="
                + urllib.parse.quote_plus(self.password))
        try:
            conn = http.client.HTTPConnection(
                self.host, self.web_port, timeout=self.timeout)
            try:
                conn.request("POST", "/cgi-bin/login.php",
                             body=body.encode("ascii"), headers={
                                 "Content-Type":
                                     "application/x-www-form-urlencoded; "
                                     "charset=UTF-8",
                                 "X-Requested-With": "XMLHttpRequest"})
                resp = conn.getresponse()
                raw = resp.read()
                set_cookie = resp.getheader("set-cookie")
                if resp.status != 200:
                    raise SealMinerError(
                        f"POST /cgi-bin/login.php -> HTTP {resp.status}")
            finally:
                conn.close()
        except SealMinerError:
            raise
        except OSError as exc:
            raise SealMinerError(
                f"cannot reach {self.host}:{self.web_port} ({exc})") from exc
        if not set_cookie:
            raise SealMinerError("no session cookie in login response")
        self._cookie = set_cookie.split(";")[0].strip()
        return self._cookie

    def _web_once(self, method: str, command: str,
                  params: dict | None = None) -> dict:
        """One web call with the current cookie (no retry)."""
        if self._cookie is None:
            self._web_login()
        headers = {"Cookie": self._cookie}
        raw_body = None
        if method == "POST" and params is not None:
            raw_body = json.dumps(params).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            conn = http.client.HTTPConnection(
                self.host, self.web_port, timeout=self.timeout)
            try:
                conn.request(method, f"/cgi-bin/{command}.php",
                             body=raw_body, headers=headers)
                resp = conn.getresponse()
                raw = resp.read()
                status = resp.status
            finally:
                conn.close()
        except OSError as exc:
            raise SealMinerError(
                f"cannot reach {self.host}:{self.web_port} ({exc})") from exc
        if status == 401:
            raise _CookieExpired("HTTP 401 from web API")
        if status != 200:
            raise SealMinerError(
                f"{method} /cgi-bin/{command}.php -> HTTP {status}")
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise SealMinerError(
                f"unparseable reply from {command}: {exc}") from exc
        if not isinstance(payload, dict):
            raise SealMinerError(f"unexpected reply shape from {command}")
        return payload

    def _web(self, method: str, command: str,
             params: dict | None = None) -> dict:
        """A web call with one re-login on a 401 (a stale
        cookie costs one extra login, never the call)."""
        try:
            return self._web_once(method, command, params)
        except _CookieExpired:
            self._cookie = None
            return self._web_once(method, command, params)

    def web_get(self, command: str) -> dict:
        """GET one CGI endpoint."""
        return self._web("GET", command)

    def web_post(self, command: str, params: dict) -> dict:
        """POST one CGI endpoint with a JSON body."""
        return self._web("POST", command, params)

    def _web_best_effort(self, command: str) -> dict | None:
        """A web read that costs the field, never the record."""
        try:
            return self.web_get(command)
        except SealMinerError:
            return None

    # -- detection ----------------------------------------------------------

    def version(self) -> dict:
        """The full ``version`` RPC reply (detection reads this)."""
        return self._cg.command("version")

    def is_sealminer(self) -> bool:
        """True when this host answers like a SealMiner."""
        try:
            return is_sealminer_version(self.version())
        except CgminerError:
            return False

    # -- reads ---------------------------------------------------------------

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        RPC reads always (summary/stats); pools and
        devdetails are best-effort enrichments; the web calls
        (get_system_info, miner_psu_status) degrade the
        fields they feed, never the record (mapping §2.3–§2.5).
        """
        ip = ip or self.host
        try:
            summary = self._cg.summary()
            stats = self._cg.stats()
        except CgminerError as exc:
            raise SealMinerError(str(exc)) from exc
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
        sysinfo = self._web_best_effort("get_system_info")
        psu_status = self._web_best_effort("miner_psu_status")

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
        model = "Sealminer"
        devdetails = devdetails_resp.get("DEVDETAILS") \
            if isinstance(devdetails_resp, dict) else None
        if isinstance(devdetails, list) and devdetails \
                and isinstance(devdetails[0], dict):
            model = str(devdetails[0].get("Model") or model)
        if model == "Sealminer" and isinstance(sysinfo, dict):
            miner_type = sysinfo.get("miner_type")
            if isinstance(miner_type, str) and miner_type:
                model = miner_type

        # --- boards (asic-rs GetHashboards rules) ---------------------------
        board_count = int(report._num(stats.get("Board Count"), 0) or 0)
        if not board_count:
            board_count = len([k for k in stats
                               if re.fullmatch(r"\d+ Chip Count", str(k))])
        chains: list[dict] = []
        intake_temps: list[float] = []
        outlet_temps: list[float] = []
        for idx in range(board_count):
            total = int(report._num(stats.get(f"{idx} Chip Count"), 0) or 0)
            bad = int(report._num(stats.get(f"{idx} Bad Chip Count"), 0) or 0)
            raw_temps = [report._num(stats.get(f"{idx} Temp {t}"))
                         for t in range(4)]
            temps = [t for t in raw_temps if t is not None and t > 0]
            if temps:
                intake_temps.append(temps[0])
                outlet_temps.append(temps[-1])
            chains.append({
                "index": idx + 1,
                "chips_total": total,
                "chips_alive": max(total - bad, 0),
                "dead_positions": [],
                "temp_c": max(temps) if temps else None,
            })

        # --- fans + power ---------------------------------------------------
        fans: list[int] = []
        fan_count = int(report._num(stats.get("Fan Count"), 0) or 0)
        for idx in range(fan_count):
            rpm = report._num(stats.get(f"{idx} Speed"))
            if rpm is not None:
                fans.append(int(rpm))
        power_w = report._num(stats.get("PSU Input Power"))
        if power_w is None and isinstance(psu_status, dict):
            power_w = report._num(psu_status.get("Power"))

        record = report._finalise_record(
            ip, model, elapsed, gh_5s, gh_av, chains, fans,
            "sealminer", power_w=power_w,
            rate_value=rate_value, rate_unit=rate_unit)
        mac = stats.get("MAC")
        if not isinstance(mac, str) or not mac:
            mac = sysinfo.get("macaddr") if isinstance(sysinfo, dict) else None
        if isinstance(mac, str) and mac:
            record["mac"] = mac
        serial = stats.get("Ctrl Board SN")
        if isinstance(serial, str) and serial:
            record["serial"] = serial
        if intake_temps:
            record["board_temp_min_c"] = min(intake_temps)
        if outlet_temps:
            record["board_temp_max_c"] = max(outlet_temps)
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
        """Full device reboot: web GET reboot.php (asic-rs
        Restart → web.reboot)."""
        return self.web_get("reboot")

    def pause(self) -> dict:
        """Suspend mining: RPC ascset "0,suspend" (asic-rs
        Pause). Success is a STATUS S reply."""
        reply = self._cg.command("ascset", "0,suspend")
        if not _status_ok(reply):
            raise SealMinerError(f"ascset suspend refused: {reply}")
        return reply

    def resume(self) -> dict:
        """Resume mining: when stats already says PM State ==
        "Running" the miner is hashing and the action is a
        no-op success (asic-rs Resume — its own guard, not
        BeeSky's); otherwise RPC `restart`."""
        try:
            stats = self._cg.stats()
        except CgminerError as exc:
            raise SealMinerError(str(exc)) from exc
        if stats.get("PM State") == "Running":
            return {"already_running": True}
        return self._cg.command("restart")

    def set_fault_light(self, on: bool) -> dict:
        """Locate LED on/off: web POST led_conf.php
        {"key": "led", "value": "on"|"off"} (asic-rs
        set_led)."""
        return self.web_post("led_conf",
                             {"key": "led",
                              "value": "on" if on else "off"})

    def _ascset_tuning(self, option: str, settings: dict) -> dict:
        """RPC ascset "0,<option>,<compact JSON>" — success is
        STATUS S + Code 119 (asic-rs set_tuning_option)."""
        parameter = ("0," + option + ","
                     + json.dumps(settings, separators=(",", ":")))
        reply = self._cg.command("ascset", parameter)
        if not _status_ok(reply, code=119):
            raise SealMinerError(
                f"ascset {option} refused (needs STATUS S, Code 119): "
                f"{reply}")
        return reply

    def set_power_limit(self, watts: int) -> dict:
        """Power limit in whole watts: RPC ascset
        "0,powerlimit,{"value":"<watts>"}" (asic-rs
        set_power_limit — whole, non-negative, u32)."""
        try:
            watts_int = int(watts)
        except (TypeError, ValueError) as exc:
            raise SealMinerError(
                f"power limit must be whole watts, got {watts!r}") from exc
        if watts_int < 0 or watts_int != watts or watts_int > 0xFFFFFFFF:
            raise SealMinerError(
                f"power limit must be whole non-negative watts, "
                f"got {watts!r}")
        return self._ascset_tuning("powerlimit",
                                   {"value": str(watts_int)})

    def set_mining_mode(self, mode: str) -> dict:
        """Mining mode: RPC ascset "0,workmode,{"mode":
        "low_power"|"normal"|"high_performance"}" (asic-rs
        set_mining_mode). low_power is A2-only (asic-rs
        set_tuning_config) — enforced by the caller."""
        if mode not in MINING_MODES:
            raise SealMinerError(
                f"mining mode must be one of {MINING_MODES}, got {mode!r}")
        return self._ascset_tuning("workmode", {"mode": mode})

    def set_pools(self, pools: list[dict]) -> dict:
        """Rewrite the pool list: RPC updatepools with the
        parameter as a JSON STRING {"pools": [{url, user,
        pass}]}, then a web reboot fire-and-forget (asic-rs
        set_pools_config — a failed updatepools is a failure;
        the reboot after a successful one is best-effort)."""
        if not pools:
            raise SealMinerError("set_pools needs at least one pool")
        norm = []
        for entry in pools:
            if not isinstance(entry, dict) or not entry.get("url"):
                raise SealMinerError("set_pools entries need a 'url'")
            norm.append({
                "url": str(entry["url"]),
                "user": str(entry.get("user") or ""),
                "pass": str(entry.get("password") or ""),
            })
        parameter = json.dumps({"pools": norm}, separators=(",", ":"))
        reply = self._cg.command("updatepools", parameter)
        if not _status_ok(reply):
            raise SealMinerError(f"updatepools refused: {reply}")
        try:
            self.reboot()
        except SealMinerError:
            pass  # fire-and-forget, asic-rs `let _ =`
        return reply


class _CookieExpired(SealMinerError):
    """Internal: the session cookie expired — re-login once."""
