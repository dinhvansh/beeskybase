"""IceRiver adapter — HTTP web API on port 80.

Source: docs/vendor-oss-mapping.md §2 — CORROBORATED:

  * pyasic (``pyasic/miners/backends/iceriver.py``,
    ``pyasic/web/iceriver.py``, ``pyasic/miners/factory.py``): a
    complete backend — ``POST /user/loginpost`` (post=6, admin /
    12345678) then ``POST /user/userpanel`` (post=4) returns the
    whole status JSON; factory detection is the console title
    ``<TITLE>用户界面</TITLE>``;
  * a real captured packet (HackMD, KS0 Ultra owner, 2024-06-30):
    the same endpoint and parameter, with the full JSON published
    — ``softver1``, ``rtpow``/``unit``, ``boards`` (chipnum/intmp/
    outtmp), ``pools``, ``fans``, ``mac``, ``runtime``;
  * user manuals corroborate the default credentials.

Response-shape divergence (mapping U-I1): the captured packet is
``{"error": 0, "data": {...}}`` (top-level ``data``) while pyasic's
backend reads ``["userpanel"]["data"]``. BeeSky accepts BOTH
shapes. The panel carries no wattage field (G-I2) and no reboot
endpoint; pool-setting exists (``/user/machineconfig``) but its
``?``-separated query form is trusted by one source only, so no
writes except the documented locate (find_miner).
"""

from __future__ import annotations

import http.client
import json
import urllib.parse

from . import report

DEFAULT_PORT = 80
DEFAULT_PASSWORD = "12345678"
DEFAULT_USERNAME = "admin"

# The IceRiver console's HTML title (pyasic's factory rule).
CONSOLE_TITLE = "<TITLE>用户界面</TITLE>"

_UNIT_TO_RATE = {"K": "kH/s", "M": "MH/s", "G": "GH/s", "T": "TH/s",
                 "P": "PH/s"}


class IceRiverError(Exception):
    """Raised when an IceRiver miner cannot be reached or refuses."""


def _data_of(payload: dict) -> dict | None:
    """The panel's data object, accepting both evidenced shapes:
    ``{"userpanel": {"data": ...}}`` (pyasic's backend) and
    ``{"error": 0, "data": ...}`` (the captured KS0 Ultra packet)."""
    if not isinstance(payload, dict):
        return None
    userpanel = payload.get("userpanel")
    if isinstance(userpanel, dict) and isinstance(
            userpanel.get("data"), dict):
        return userpanel["data"]
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def panel_model(payload: dict) -> str:
    """The model token for a userpanel payload (mapping §2.3)."""
    data = _data_of(payload) or {}
    return parse_model(data.get("softver1") or "")


def is_iceriver_panel(payload: dict) -> bool:
    """Shape gate (mapping §2.4): a userpanel reply with error == 0
    and a data object carrying ``softver1``. Positive-only — no
    Antminer-family web UI answers this endpoint with this shape."""
    if not isinstance(payload, dict):
        return False
    if payload.get("error") not in (0, "0", None):
        return False
    data = _data_of(payload)
    return isinstance(data, dict) and isinstance(
        data.get("softver1"), str) and bool(data["softver1"])


def parse_model(softver1: str) -> str:
    """Model token from the firmware version string (pyasic's rule
    in factory.get_miner_model_iceriver): split on "_"; a trailing
    "miner" token means the model is the token before it, otherwise
    strip "miner" from the last token. Upper-cased.

    "ICM168_3_2_14_ks0ultra_miner" -> "KS0ULTRA".
    """
    parts = str(softver1 or "").split("_")
    if not parts:
        return "IceRiver"
    if parts[-1] == "miner":
        token = parts[-2] if len(parts) >= 2 else parts[-1]
    else:
        token = parts[-1].replace("miner", "")
    token = (token or "iceriver").upper()
    return token


def parse_runtime(runtime: str) -> int | None:
    """\"DD:HH:MM:SS\" -> seconds (pyasic _get_uptime)."""
    try:
        days, hours, minutes, seconds = str(runtime).split(":")
        return (int(days) * 86400 + int(hours) * 3600
                + int(minutes) * 60 + int(seconds))
    except (ValueError, AttributeError):
        return None


def _rate_from(rtpow, unit: str) -> tuple[float | None, str | None,
                                          float | None]:
    """(native value, native unit, GH/s value) for a "359G"-style
    reading with the panel's unit letter. The response's own unit
    is the native unit (v0.20 discipline)."""
    if rtpow is None:
        return None, None, None
    text = str(rtpow).strip()
    digits = text.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    try:
        value = float(digits)
    except ValueError:
        return None, None, None
    letter = (str(unit or "").strip().upper() or
              text[len(digits):].strip().upper() or "G")
    rate_unit = _UNIT_TO_RATE.get(letter)
    if rate_unit is None:
        return None, None, None
    scale_to_gh = {"K": 1e-6, "M": 1e-3, "G": 1.0, "T": 1e3,
                   "P": 1e6}[letter]
    return value, rate_unit, value * scale_to_gh


class IceRiverClient:
    """Client for one IceRiver miner's web API (port 80)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 password: str = DEFAULT_PASSWORD,
                 username: str = DEFAULT_USERNAME,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.timeout = timeout
        self._cookie: str | None = None

    # -- transport ---------------------------------------------------------

    def _post(self, path: str, params: dict) -> dict:
        """POST with query-string params (pyasic's send_command
        form); returns the parsed JSON body. Login cookies, when
        the miner sets any, ride on later calls."""
        query = urllib.parse.urlencode(params)
        target = f"{path}?{query}" if query else path
        headers: dict[str, str] = {}
        if self._cookie:
            headers["Cookie"] = self._cookie
        try:
            conn = http.client.HTTPConnection(
                self.host, self.port, timeout=self.timeout)
            try:
                conn.request("POST", target, body=None, headers=headers)
                resp = conn.getresponse()
                raw = resp.read()
                cookie = resp.getheader("Set-Cookie")
                if cookie:
                    self._cookie = cookie.split(";", 1)[0].strip()
                if resp.status != 200:
                    raise IceRiverError(
                        f"POST {path} -> HTTP {resp.status}")
            finally:
                conn.close()
        except IceRiverError:
            raise
        except OSError as exc:
            raise IceRiverError(
                f"cannot reach {self.host}:{self.port} ({exc})") from exc
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise IceRiverError(
                f"unparseable reply from {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise IceRiverError(f"unexpected reply shape from {path}")
        return payload

    def _get_text(self, path: str) -> str:
        """Raw GET body (the console-title probe)."""
        try:
            conn = http.client.HTTPConnection(
                self.host, self.port, timeout=self.timeout)
            try:
                conn.request("GET", path)
                resp = conn.getresponse()
                raw = resp.read()
                if resp.status != 200:
                    return ""
            finally:
                conn.close()
        except OSError:
            return ""
        return raw.decode("utf-8", errors="replace")

    # -- detection ----------------------------------------------------------

    def has_console_title(self) -> bool:
        """Cheap gate (mapping §2.4): the root page carries the
        IceRiver console title. Never raises — a probe helper."""
        try:
            return CONSOLE_TITLE in self._get_text("/")
        except Exception:  # noqa: BLE001 — probes never raise
            return False

    def login(self) -> bool:
        """Best-effort login (pyasic's form). The API needs no
        token (HackMD), so a failed login never fails the fetch —
        it only means no session cookie rides along. Success is
        an explicit error == 0 in the reply, not merely HTTP 200."""
        try:
            payload = self._post("/user/loginpost",
                                 {"post": "6", "user": self.username,
                                  "pwd": self.password})
        except IceRiverError:
            return False
        return payload.get("error") in (0, "0")

    def userpanel(self) -> dict:
        """The full status payload (login first, best-effort)."""
        self.login()
        payload = self._post("/user/userpanel", {"post": "4"})
        if not is_iceriver_panel(payload):
            raise IceRiverError(
                "userpanel reply is not an IceRiver status payload")
        return payload

    def is_iceriver(self) -> bool:
        """True when this host answers like an IceRiver miner."""
        if not self.has_console_title():
            return False
        try:
            self.userpanel()
        except IceRiverError:
            return False
        return True

    # -- reads ---------------------------------------------------------------

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        Rate truth (mapping §2.3): ``rtpow`` + ``unit`` are the
        device's own scale — KS models report "359G" (GH/s), AL3
        reports T. Boards carry chip counts and intmp/outtmp from
        the panel; power is NOT reported (G-I2). Pool passwords
        in the payload are never copied into the record.
        """
        ip = ip or self.host
        payload = self.userpanel()
        data = _data_of(payload) or {}

        model = parse_model(data.get("softver1") or "")
        elapsed = parse_runtime(data.get("runtime") or "") or 0
        rt_value, rt_unit, rt_gh = _rate_from(
            data.get("rtpow"), data.get("unit"))
        _av_value, _av_unit, av_gh = _rate_from(
            data.get("avgpow"), data.get("unit"))

        chains: list[dict] = []
        boards = data.get("boards")
        if isinstance(boards, list):
            for entry in boards:
                if not isinstance(entry, dict):
                    continue
                try:
                    idx = int(float(entry.get("no", 0)))
                    total = int(float(entry.get("chipnum", 0)))
                except (TypeError, ValueError):
                    continue
                alive = total if entry.get("state") else 0
                temp = report._num(entry.get("intmp"))
                chains.append({
                    "index": idx,
                    "chips_total": total,
                    "chips_alive": alive,
                    "dead_positions": [],
                    "temp_c": temp,
                })

        fans: list[int] = []
        raw_fans = data.get("fans")
        if isinstance(raw_fans, list):
            for value in raw_fans:
                rpm = report._num(value)
                if rpm is not None:
                    fans.append(int(rpm))

        record = report._finalise_record(
            ip, model, elapsed, rt_gh, av_gh, chains, fans,
            "iceriver", power_w=None,
            rate_value=rt_value, rate_unit=rt_unit)
        mac = data.get("mac")
        if isinstance(mac, str) and mac:
            record["mac"] = mac.upper()
        pools = self._pools_normalised(data)
        if pools is not None:
            record["pools"] = pools
        return record

    def _pools_normalised(self, data: dict) -> list[dict] | None:
        """The scan-record pool list from the panel's pools array
        (mapping §2.3). ``pass`` is deliberately dropped."""
        raw = data.get("pools")
        if not isinstance(raw, list):
            return None
        pools: list[dict] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            addr = entry.get("addr")
            if not addr:
                continue
            pools.append({
                "url": addr,
                "worker": entry.get("user"),
                "status": "Alive" if entry.get("state") == 1
                          or entry.get("state") == 1.0 else "Dead",
                "accepted": entry.get("accepted"),
                "rejected": entry.get("rejected"),
                "active": entry.get("connect") == 1
                          or entry.get("connect") == 1.0,
            })
        return pools or None

    # -- actions (documented only) ------------------------------------------

    def locate(self, enable: bool) -> dict:
        """Fault-light locate (pyasic ``IceRiverWebAPI.locate``):
        POST userpanel post=5 locate=1/0. Success is error == 0."""
        self.login()
        payload = self._post("/user/userpanel",
                             {"post": "5",
                              "locate": "1" if enable else "0"})
        if payload.get("error") not in (0, "0", None):
            raise IceRiverError(
                f"locate refused: error={payload.get('error')!r}")
        return payload
