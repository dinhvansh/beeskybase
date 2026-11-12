"""ePIC adapter — HTTP JSON API on port 4028.

Source: docs/epic-mapping.md — Epic's own published material:

  * the API docs (APIv2 for epic-miner v4.0.0 on the SC200,
    APIv3 for PowerPlay): HTTP JSON to ``http://<ip>:<port>/...``;
    GET needs no password; POST carries
    ``{"param": ..., "password": ...}`` and answers
    ``{"result": bool, "error": string|null}``;
  * the port is 4028, pinned three times in the dashboard's
    own code (``src/portscan.js:24``, ``src/main.js:100``,
    ``src/app.jsx:1201``) — the docs only ever write
    ``<port>``;
  * detection is the dashboard's own scan
    (``src/portscan.js``): GET ``:4028/summary``, parse the
    JSON, take ``.Hostname`` — BeeSky adds the structural
    gate (mapping §2): Hostname + Session/"Average MHs" +
    HBs. No other BeeSky family serves HTTP JSON on 4028
    (cgminer text, Whatsminer envelope), so the fingerprint
    cannot mis-claim one;
  * control params are the dashboard's ``handleApi`` bodies
    (``src/app.jsx``) wherever they exist — the docs'
    ``<string>``/``<uint>`` placeholders alone are never
    enough (mapping §4).

Reads ride one ``/summary`` GET (plus one ``/capabilities``
GET for the model/presets/coins — a failure there degrades
the model to the family label, never the record). The native
rate is MH/s (``Session["Average MHs"]``, v0.20 discipline).

Known limits (mapping §5–§6): chips are 0/0 (the API
reports no chip counts — ``/hashrate`` is the unconfirmed
candidate, U-E5); fans carry no rpm — one speed % rides the
record as ``fan_speed_pct``; ``/miner`` has no evidenced
"start" value, so resume is not implemented (U-E3).
"""

from __future__ import annotations

import http.client
import json

from . import report

DEFAULT_PORT = 4028
# README: "By default all of the miners have a password of letmein."
DEFAULT_PASSWORD = "letmein"


class EpicError(Exception):
    """Raised when an ePIC miner cannot be reached or refuses."""


def is_epic_summary(payload: dict) -> bool:
    """Detection fingerprint (mapping §2): a ``/summary`` JSON
    object with a non-empty Hostname, a Session object carrying
    a numeric "Average MHs", and an HBs list. Positive-only —
    no other family serves this shape on 4028."""
    if not isinstance(payload, dict):
        return False
    hostname = payload.get("Hostname")
    if not isinstance(hostname, str) or not hostname:
        return False
    session = payload.get("Session")
    if not isinstance(session, dict):
        return False
    if report._num(session.get("Average MHs")) is None:
        return False
    return isinstance(payload.get("HBs"), list)


class EpicClient:
    """Client for one ePIC miner's HTTP JSON API (port 4028)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 password: str = DEFAULT_PASSWORD,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout

    # -- transport ---------------------------------------------------------

    def _get(self, path: str) -> dict:
        """GET a JSON object; raises EpicError on any failure."""
        try:
            conn = http.client.HTTPConnection(
                self.host, self.port, timeout=self.timeout)
            try:
                conn.request("GET", path)
                resp = conn.getresponse()
                raw = resp.read()
                if resp.status != 200:
                    raise EpicError(
                        f"GET {path} -> HTTP {resp.status}")
            finally:
                conn.close()
        except EpicError:
            raise
        except OSError as exc:
            raise EpicError(
                f"cannot reach {self.host}:{self.port} ({exc})") from exc
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise EpicError(
                f"unparseable reply from {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EpicError(f"unexpected reply shape from {path}")
        return payload

    def _post(self, path: str, param) -> dict:
        """POST {"param": ..., "password": ...}; success is
        "result": true, anything else raises with the miner's
        own error verbatim (mapping §4)."""
        body = json.dumps({"param": param,
                           "password": self.password}).encode("utf-8")
        try:
            conn = http.client.HTTPConnection(
                self.host, self.port, timeout=self.timeout)
            try:
                conn.request("POST", path, body=body, headers={
                    "Content-Type": "application/json"})
                resp = conn.getresponse()
                raw = resp.read()
                if resp.status != 200:
                    raise EpicError(
                        f"POST {path} -> HTTP {resp.status}")
            finally:
                conn.close()
        except EpicError:
            raise
        except OSError as exc:
            raise EpicError(
                f"cannot reach {self.host}:{self.port} ({exc})") from exc
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise EpicError(
                f"unparseable reply from {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EpicError(f"unexpected reply shape from {path}")
        if payload.get("result") is not True:
            raise EpicError(
                f"{path} refused: {payload.get('error')!r}")
        return payload

    # -- detection ----------------------------------------------------------

    def summary(self) -> dict:
        """The full ``/summary`` payload (detection reads this)."""
        return self._get("/summary")

    def capabilities(self) -> dict | None:
        """The ``/capabilities`` payload, or None when the miner
        does not answer it (v2 miners may not; the fetch
        degrades instead of failing)."""
        try:
            return self._get("/capabilities")
        except EpicError:
            return None

    def is_epic(self) -> bool:
        """True when this host answers like an ePIC miner."""
        try:
            return is_epic_summary(self.summary())
        except EpicError:
            return False

    # -- reads ---------------------------------------------------------------

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        Rate truth (mapping §3): ``Session["Average MHs"]``
        is the native MH/s rate; the "LastAverageMHs" sample
        is the 5s-equivalent. Boards come from ``HBs[]``
        (temp + input/output power; Index verbatim, mapping
        §3). Chips are 0/0 — the API reports no chip counts
        (U-E5). Fans carry no rpm — one speed % rides the
        record as ``fan_speed_pct``.
        """
        ip = ip or self.host
        summary = self.summary()
        caps = self.capabilities()
        session = summary.get("Session") or {}
        if not isinstance(session, dict):
            session = {}

        avg_mhs = report._num(session.get("Average MHs"))
        last = session.get("LastAverageMHs")
        last_mhs = (report._num(last.get("Hashrate"))
                    if isinstance(last, dict) else None)
        gh_av = avg_mhs / 1000.0 if avg_mhs is not None else None
        gh_5s = last_mhs / 1000.0 if last_mhs is not None else None
        rate_value = avg_mhs
        rate_unit = "MH/s" if avg_mhs is not None else None
        elapsed = int(report._num(session.get("Uptime"), 0) or 0)

        model = "Epic"
        if isinstance(caps, dict):
            model = str(caps.get("Model") or model)

        chains: list[dict] = []
        hbs = summary.get("HBs")
        input_power = 0.0
        output_power = 0.0
        if isinstance(hbs, list):
            for pos, entry in enumerate(hbs):
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(entry.get("Index", pos))
                except (TypeError, ValueError):
                    idx = pos
                temp = report._num(entry.get("Temperature"))
                in_p = report._num(entry.get("Input Power"))
                out_p = report._num(entry.get("Output Power"))
                if in_p is not None:
                    input_power += in_p
                if out_p is not None:
                    output_power += out_p
                chains.append({
                    "index": idx,
                    "chips_total": 0,
                    "chips_alive": 0,
                    "dead_positions": [],
                    "temp_c": temp,
                })
        psu = summary.get("Power Supply Stats")
        psu_power = (report._num(psu.get("Input Power"))
                     if isinstance(psu, dict) else None)
        power_w = psu_power
        if power_w is None and input_power:
            power_w = input_power
        if power_w is None and output_power:
            power_w = output_power

        fans: list[int] = []
        fan_pct = None
        fans_section = summary.get("Fans")
        if isinstance(fans_section, dict):
            fan_pct = report._num(fans_section.get("Fans Speed"))
            if fan_pct is not None:
                fan_pct = int(fan_pct)

        record = report._finalise_record(
            ip, model, elapsed, gh_5s, gh_av, chains, fans,
            "epic", power_w=power_w,
            rate_value=rate_value, rate_unit=rate_unit)
        hostname = summary.get("Hostname")
        if isinstance(hostname, str) and hostname:
            record["hostname"] = hostname
        mining = summary.get("Mining")
        if isinstance(mining, dict):
            if isinstance(mining.get("Coin"), str):
                record["coin"] = mining["Coin"]
        if fan_pct is not None:
            record["fan_speed_pct"] = fan_pct
        accepted = report._num(session.get("Accepted"))
        rejected = report._num(session.get("Rejected"))
        if accepted is not None:
            record["accepted"] = accepted
        if rejected is not None:
            record["rejected"] = rejected
        hb_status = summary.get("HBStatus")
        if isinstance(hb_status, list) and hb_status:
            record["hb_status"] = hb_status
        stratum = summary.get("Stratum")
        configs = summary.get("StratumConfigs")
        pools = self._pools_normalised(stratum, configs)
        if pools is not None:
            record["pools"] = pools
        return record

    def _pools_normalised(self, stratum, configs) -> list[dict] | None:
        """The scan-record pool list from StratumConfigs
        (mapping §5): only the current pool while connected
        reads "Alive" — the API carries no per-pool liveness,
        so standby pools read "Dead" by this rule (D-E4).
        Passwords are never copied into the record."""
        if not isinstance(configs, list) or not configs:
            return None
        current = None
        connected = False
        if isinstance(stratum, dict):
            current = stratum.get("Current Pool")
            connected = bool(stratum.get("IsPoolConnected"))
        pools: list[dict] = []
        for entry in configs:
            if not isinstance(entry, dict):
                continue
            url = entry.get("pool")
            if not url:
                continue
            pools.append({
                "url": url,
                "worker": entry.get("login"),
                "status": ("Alive" if connected and url == current
                           else "Dead"),
            })
        return pools or None

    # -- actions (documented / dashboard-verified params only) -------------

    def reboot(self, delay: int = 0) -> dict:
        """Full device reboot; param is a uint delay in seconds,
        0 = instant (DOC + CODE)."""
        return self._post("/reboot", int(delay))

    def softreboot(self, delay: int = 0) -> dict:
        """Restart the mining program only (DOC + CODE)."""
        return self._post("/softreboot", int(delay))

    def stop_mining(self) -> dict:
        """Stop the mining program: /miner param "stop" — the
        only value the dashboard ever sends (CODE, mapping
        §4). There is no verified "start" value (U-E3)."""
        return self._post("/miner", "stop")

    def identify(self, enable: bool = True) -> dict:
        """Toggle the locate LED (DOC + CODE)."""
        return self._post("/identify", bool(enable))

    def set_fan_speed(self, speed: int) -> dict:
        """Manual fan speed 1–100. The dashboard sends a NUMBER
        (FanTab state); the doc says a string — the shipped
        client wins (divergence D-E2, mapping §4)."""
        if not 1 <= int(speed) <= 100:
            raise EpicError(
                f"fan speed must be 1-100, got {speed!r}")
        return self._post("/fanspeed", int(speed))

    def set_mode(self, preset: str, power_target=None) -> dict:
        """Set a performance preset from /capabilities (DOC +
        CODE): param is {preset, power_target} with a power
        target, else the preset string alone."""
        if not isinstance(preset, str) or not preset:
            raise EpicError("set_mode needs a preset name")
        param = ({"preset": preset, "power_target": int(power_target)}
                 if power_target is not None else preset)
        return self._post("/mode", param)

    def set_coin(self, coin: str, configs: list[dict],
                 unique_id: bool = False) -> dict:
        """Set the mining config (DOC + CODE): param carries
        coin + stratum_configs + the dashboard's extra
        pool_url/login of slot 0 (D-E1). ``configs`` are
        {pool, login, password} dicts, max 3."""
        if not isinstance(coin, str) or not coin:
            raise EpicError("set_coin needs a coin name")
        if not configs or len(configs) > 3:
            raise EpicError("set_coin needs 1-3 pool configs")
        norm = []
        for entry in configs:
            if not isinstance(entry, dict) or not entry.get("pool"):
                raise EpicError(
                    "set_coin configs need at least a pool URL")
            norm.append({
                "pool": str(entry["pool"]),
                "login": str(entry.get("login") or ""),
                "password": str(entry.get("password") or ""),
            })
        param = {
            "coin": coin,
            "stratum_configs": norm,
            "pool_url": norm[0]["pool"],
            "login": norm[0]["login"],
            "unique_id": bool(unique_id),
        }
        return self._post("/coin", param)

    def set_password(self, new_password: str) -> dict:
        """Set a new miner password; param is the new password,
        "password" the old one (DOC + CODE)."""
        if not isinstance(new_password, str) or not new_password:
            raise EpicError("set_password needs a new password")
        return self._post("/password", new_password)

    def set_power(self, watts: int) -> dict:
        """Manual target power in watts (DOC only — the
        dashboard never sends /power; mapping §4)."""
        if int(watts) < 0:
            raise EpicError(
                f"target power must be >= 0, got {watts!r}")
        return self._post("/power", int(watts))

    def set_shutdown_temp(self, temp_c: int) -> dict:
        """Shutdown temperature threshold in °C (DOC + CODE;
        doc default 85 °C)."""
        return self._post("/shutdowntemp", int(temp_c))

    def tune(self, clock_mhz, voltage_mv) -> dict:
        """Change clock + voltage (CODE): param is
        {"clks": "<MHz>", "voltage": "<mV>"} as strings
        (mapping §4). The miner caps at 1000 MHz / 15 V."""
        return self._post("/tune", {
            "clks": str(int(clock_mhz)),
            "voltage": str(int(voltage_mv)),
        })
