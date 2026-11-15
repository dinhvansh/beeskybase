"""VNish / HashCore dashd HTTP API adapter ("xminer-api").

Implemented against the firmware's own OpenAPI document
(``usr/share/dashd/ui/docs/api-doc.json`` in the VNish rootfs), base URL
``/api/v1`` on HTTP :80. The endpoints used here:

  GET /api/v1/summary  -> {"miner": AntmMinerStats | null}
        miner.miner_type, miner.hr_realtime / hr_average (TH/s scale),
        miner.power_consumption (required int32 field in the doc — the
        miner's wall draw in watts; becomes record["power_w"], v0.9),
        miner.miner_status.miner_state_time (seconds in "mining" state),
        miner.chains[] = AntmBoard {id, chip_temp{max}, pcb_temp{max},
        chip_statuses{red, orange, grey}, status{state}},
        miner.cooling.fans[] = {id, rpm}
  GET /api/v1/boards   -> [AntmBoardChips] — per-chip detail:
        {id, status{state}, chips[] = AntmChip {id, hr, grade, temp, ...},
         sensors[]}
  GET /api/v1/info     -> InfoJson {miner (pretty name), model, serial, ...}
  GET /api/v1/model    -> MinerModelInfo {full_name,
        chain{chips_per_chain, num_chains, ...}}

Auth (per the doc): the read endpoints above carry NO security requirement
(/summary also explicitly allows anonymous access — its security list is
``[{}, {bearerAuth}, {apikeyAuth}]``); write endpoints require a bearer JWT
(from POST /unlock) or an ``x-api-key`` header. This adapter is read-only and
sends the credentials only when the caller supplies them.

Per-chip data — what dashd does and does not expose:
  * /boards DOES expose every chip (id, hashrate, grade grey/orange/red,
    temperature), so dead-chip *positions* are recoverable: a chip counts as
    dead here when its grade is "red" (grey = normal, orange = degraded but
    hashing). This matches AntmBoard.chip_statuses, whose counts are exactly
    {red, orange, grey} — red is the failure bucket.
  * GAP: /summary chains alone give only the red/orange/grey *counts*, never
    positions, and no explicit chips-total field. The total comes from
    /model (chain.chips_per_chain, a nominal factory figure) or from the
    /boards chip list length. If /boards fails, positions are unknown and
    the record's MISSING_CHIPS problem notes "counts only".
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from . import report
from .multipart import build_multipart_body

API_BASE = "/api/v1"

# Miners are LAN devices: always connect directly. Honouring http_proxy-style
# environment variables would route bench traffic through some egress proxy
# and fail (this bit us in testing with 127.0.0.2+ hosts outside no_proxy).
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
DEFAULT_PORT = 80


class DashdError(Exception):
    """Raised when a dashd host cannot be reached or does not answer sanely.

    ``status`` carries the HTTP status when the failure was an HTTP
    response (e.g. 401 from an auth-gated dashd) so callers can tell
    "locked dashd" apart from "not a dashd host at all" (v0.23).
    """

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class DashdClient:
    """Read-only client for one miner's dashd (xminer) HTTP API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 3.0,
                 api_key: str | None = None, token: str | None = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.api_key = api_key
        self.token = token

    # -- transport ---------------------------------------------------------
    def _headers(self) -> dict:
        headers = {"Accept": "application/json", "User-Agent": "BeeSky"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, payload=None,
                 headers: dict | None = None):
        """One HTTP call; returns the parsed JSON body ({} when empty)."""
        url = f"http://{self.host}:{self.port}{API_BASE}{path}"
        data = None
        hdrs = self._headers()
        if headers:
            hdrs.update(headers)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        request = urllib.request.Request(url, headers=hdrs, data=data,
                                         method=method)
        try:
            with _OPENER.open(request, timeout=self.timeout) as resp:
                body = resp.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                parsed = json.loads(exc.read().decode("utf-8", "replace"))
                if isinstance(parsed, dict) and parsed.get("err"):
                    detail = f" ({parsed['err']})"
            except Exception:  # noqa: BLE001 — body is best-effort context
                pass
            raise DashdError(f"{method} {path} -> HTTP {exc.code}{detail}",
                             status=exc.code) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise DashdError(f"cannot reach {url} ({exc})") from exc
        if not body.strip():
            return {}
        try:
            return json.loads(body.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise DashdError(f"{method} {path} -> non-JSON reply") from exc

    def get_json(self, path: str):
        """GET one API path and return the parsed JSON body."""
        return self._request("GET", path)

    def unlock(self, password: str) -> str:
        """Mint a bearer JWT via POST /unlock (doc: body {"pw": ...}).

        Stores the token on this client so later calls carry it.
        """
        data = self._request("POST", "/unlock", {"pw": password},
                             headers={})
        token = data.get("token") if isinstance(data, dict) else None
        if not token:
            raise DashdError("POST /unlock -> reply without a token")
        self.token = str(token)
        return self.token

    def post_json(self, path: str, payload=None, password: str | None = None):
        """POST one API path (write endpoints need auth — see module doc).

        With neither a token nor an API key configured, a supplied
        *password* is first exchanged for a JWT via /unlock, exactly as
        the firmware's own UI does.
        """
        if not self.token and not self.api_key and password:
            try:
                self.unlock(password)
            except DashdError:
                pass  # the POST below will surface the real error (401)
        return self._request("POST", path, payload)

    def post_multipart(self, path: str, field: str, filename: str,
                       data: bytes, extra_fields: dict | None = None,
                       password: str | None = None):
        """Multipart-upload one file (firmware update); return parsed JSON.

        Implements the doc's ``POST /api/v1/firmware/update`` shape:
        multipart/form-data with a ``file`` part (binary, required) plus
        optional plain fields such as ``keep_settings``. Auth is the
        doc's bearer JWT / ``x-api-key`` pair — with only a *password* a
        JWT is minted via /unlock first, exactly like post_json.
        """
        if not self.token and not self.api_key and password:
            try:
                self.unlock(password)
            except DashdError:
                pass  # the POST below will surface the real error (401)
        fields = [(field, filename, data, "application/octet-stream")]
        for key, value in (extra_fields or {}).items():
            fields.append((key, None, str(value).encode("utf-8"), None))
        body, content_type = build_multipart_body(fields)
        url = f"http://{self.host}:{self.port}{API_BASE}{path}"
        headers = self._headers()
        headers["Content-Type"] = content_type
        request = urllib.request.Request(url, headers=headers, data=body,
                                         method="POST")
        try:
            with _OPENER.open(request, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                parsed = json.loads(exc.read().decode("utf-8", "replace"))
                if isinstance(parsed, dict) and parsed.get("err"):
                    detail = f" ({parsed['err']})"
            except Exception:  # noqa: BLE001 — body is best-effort context
                pass
            raise DashdError(f"POST {path} -> HTTP {exc.code}{detail}",
                             status=exc.code) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise DashdError(f"cannot reach {url} ({exc})") from exc
        if not raw.strip():
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}  # the 200 status was the answer; body is decoration
        return parsed if isinstance(parsed, dict) else {}

    # -- endpoints -----------------------------------------------------------
    def summary(self) -> dict:
        data = self.get_json("/summary")
        if not isinstance(data, dict):
            raise DashdError("summary reply is not an object")
        return data

    def boards(self) -> list:
        data = self.get_json("/boards")
        if not isinstance(data, list):
            raise DashdError("boards reply is not a list")
        return data

    def info(self) -> dict:
        data = self.get_json("/info")
        return data if isinstance(data, dict) else {}

    def model_info(self) -> dict:
        data = self.get_json("/model")
        return data if isinstance(data, dict) else {}

    # -- detection -----------------------------------------------------------
    def probe(self) -> dict | None:
        """Return the summary dict if this host speaks dashd, else None.

        Signature: HTTP 200 on /api/v1/summary with a JSON object that has a
        "miner" key (AntmMinerStats or null) — stock Bitmain CGI hosts 404
        this path, generic web servers do not produce this shape.
        """
        summary, _status = self.probe_detail()
        return summary

    def probe_detail(self) -> tuple[dict | None, int | None]:
        """Probe like :meth:`probe`, but also report the HTTP status when
        the summary call failed — 401 means an auth-gated dashd (v0.23
        multi-credential discovery keys the "locked dashd" case off it).
        Returns (summary_or_None, failure_status_or_None)."""
        try:
            data = self.summary()
        except DashdError as exc:
            return None, exc.status
        return (data if "miner" in data else None), None

    # -- record building -------------------------------------------------------
    def fetch_record(self, ip: str | None = None) -> dict:
        """Fetch summary (+ boards/info/model) and build a status record."""
        ip = ip or self.host
        summary = self.summary()
        miner = summary.get("miner") or {}

        try:
            info = self.info()
        except DashdError:
            info = {}
        try:
            model_info = self.model_info()
        except DashdError:
            model_info = {}
        try:
            boards = self.boards()
        except DashdError:
            boards = None  # fall back to summary counts (positions unknown)

        model = (info.get("miner") or miner.get("miner_type")
                 or model_info.get("full_name") or "Unknown")

        nominal_chips = None
        chain_info = model_info.get("chain")
        if isinstance(chain_info, dict):
            nominal_chips = chain_info.get("chips_per_chain")

        boards_by_id = {}
        if boards:
            for entry in boards:
                if isinstance(entry, dict) and isinstance(entry.get("id"), int):
                    boards_by_id[entry["id"]] = entry

        chains: list[dict] = []
        for board in miner.get("chains") or []:
            if not isinstance(board, dict):
                continue
            board_id = board.get("id", len(chains))
            temp = _temp_max(board.get("chip_temp")) or _temp_max(board.get("pcb_temp"))

            entry = boards_by_id.get(board_id)
            if entry is not None and isinstance(entry.get("chips"), list):
                chips = entry["chips"]
                dead = [int(c["id"]) + 1 for c in chips
                        if isinstance(c, dict) and c.get("grade") == "red"
                        and isinstance(c.get("id"), int)]
                total = len(chips)
                alive = total - len(dead)
                if temp is None:
                    chip_temps = [c.get("temp") for c in chips
                                  if isinstance(c, dict)
                                  and isinstance(c.get("temp"), (int, float))]
                    temp = max(chip_temps) if chip_temps else None
            else:
                # Summary-only fallback: counts, no positions (see module doc).
                statuses = board.get("chip_statuses") or {}
                red = int(statuses.get("red") or 0)
                orange = int(statuses.get("orange") or 0)
                grey = int(statuses.get("grey") or 0)
                total = grey + orange + red
                if total == 0 and nominal_chips:
                    total = int(nominal_chips)
                alive = total - red
                dead = []
            chains.append({
                "index": int(board_id) + 1,  # dashd board ids are 0-based
                "chips_total": total,
                "chips_alive": alive,
                "dead_positions": dead,
                "temp_c": temp,
            })

        cooling = miner.get("cooling") or {}
        fans = [int(f["rpm"]) for f in cooling.get("fans") or []
                if isinstance(f, dict) and isinstance(f.get("rpm"), (int, float))]

        state = miner.get("miner_status") or {}
        elapsed = state.get("miner_state_time") or 0

        record = report.build_record_from_boards(
            ip,
            model=model,
            elapsed_s=int(elapsed),
            ths_realtime=_as_float(miner.get("hr_realtime")),
            ths_average=_as_float(miner.get("hr_average")),
            chains=chains,
            fans_rpm=fans,
            source="vnish",
            power_w=_as_float(miner.get("power_consumption")),
        )
        # Pool enrichment (v0.28): the summary THIS fetch already
        # downloaded carries the PoolStats list — the record gains
        # it at zero extra I/O (docs/presets-ipreport-mapping.md
        # §4). Values pass through verbatim; only the key is
        # normalised (dashd "user" -> the record's "worker").
        raw_pools = miner.get("pools")
        if isinstance(raw_pools, list):
            record["pools"] = [{
                "url": p.get("url"),
                "worker": p.get("user"),
                "status": p.get("status"),
            } for p in raw_pools if isinstance(p, dict)]
        return record


def _temp_max(temp_range) -> float | None:
    if isinstance(temp_range, dict):
        val = temp_range.get("max")
        if isinstance(val, (int, float)):
            return float(val)
    return None


def _as_float(value):
    return float(value) if isinstance(value, (int, float)) else None
