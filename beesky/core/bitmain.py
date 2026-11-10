"""Bitmain stock-firmware HTTP CGI adapter (digest auth).

Stock Antminer firmware serves its web UI on HTTP :80 behind **HTTP digest
auth** (factory default ``root`` / ``root``) and exposes JSON status CGIs.
Per the HashCore Toolkit research (``research/hashcore/MAP.md``), fleet tools
talk to stock firmware through the cgminer RPC *and* the stock web surface
(``*-status.php`` pages, ``/admin/status/cgminerstatus``, digest-auth
session); the toolkit binary's own string table lists the modern JSON CGIs
used here:

  GET /cgi-bin/get_miner_status.cgi  — miner status JSON (primary)
  GET /cgi-bin/miner_stats.cgi       — fallback status source on some builds
  GET /cgi-bin/get_system_info.cgi   — {"DATA": {"minertype": ..., ...}}

The status payload mirrors the cgminer API shape (``SUMMARY`` / ``STATS``
sections with ``chain_acsN`` strings, ``tempN``, ``fanN``) — sometimes
wrapped in a ``{"DATA": {...}}`` envelope, sometimes flat with the chain
data nested one level down. The parser below unwraps and merges whatever
layout shows up, then hands cgminer-shaped summary/stats dicts to the same
normaliser the RPC adapter uses, so problem rules and tickets are shared.

Digest auth is implemented manually on hashlib (RFC 7616, MD5, qop=auth
with legacy no-qop fallback) — the stdlib has no digest client helper.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import re
import secrets
import urllib.error
import urllib.request

from . import report
from .multipart import build_multipart_body

DEFAULT_PORT = 80

# Miners are LAN devices: always connect directly. Honouring http_proxy-style
# environment variables would route bench traffic through some egress proxy
# and fail (this bit us in testing with 127.0.0.2+ hosts outside no_proxy).
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
STATUS_PATHS = ("/cgi-bin/get_miner_status.cgi", "/cgi-bin/miner_stats.cgi")
SYSINFO_PATH = "/cgi-bin/get_system_info.cgi"


class BitmainError(Exception):
    """Raised when a stock-firmware host cannot be read."""


# --------------------------------------------------------------------------
# HTTP digest auth (RFC 7616, MD5)
# --------------------------------------------------------------------------

def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _parse_challenge(header: str) -> dict:
    """Parse a WWW-Authenticate: Digest ... header into a dict."""
    params: dict = {}
    for match in re.finditer(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header or ""):
        params[match.group(1).lower()] = (
            match.group(2) if match.group(2) is not None else match.group(3))
    return params


class DigestAuth:
    """Stateful digest-auth helper: learns the challenge, signs requests."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.challenge: dict | None = None
        self._nc = 0

    def learn(self, header: str) -> None:
        params = _parse_challenge(header)
        if "nonce" in params:
            self.challenge = params

    def header(self, method: str, uri: str) -> str | None:
        ch = self.challenge
        if not ch or "nonce" not in ch:
            return None
        realm = ch.get("realm", "")
        nonce = ch["nonce"]
        qop_offered = [q.strip() for q in ch.get("qop", "").split(",") if q.strip()]
        qop = "auth" if "auth" in qop_offered else None
        ha1 = _md5(f"{self.username}:{realm}:{self.password}")
        ha2 = _md5(f"{method}:{uri}")
        self._nc += 1
        nc = f"{self._nc:08x}"
        cnonce = secrets.token_hex(8)
        if qop:
            response = _md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}")
        else:
            response = _md5(f"{ha1}:{nonce}:{ha2}")
        parts = [
            f'username="{self.username}"',
            f'realm="{realm}"',
            f'nonce="{nonce}"',
            f'uri="{uri}"',
            f'response="{response}"',
        ]
        if qop:
            parts += [f'qop={qop}', f'nc={nc}', f'cnonce="{cnonce}"']
        if ch.get("opaque"):
            parts.append(f'opaque="{ch["opaque"]}"')
        if ch.get("algorithm"):
            parts.append(f'algorithm={ch["algorithm"]}')
        return "Digest " + ", ".join(parts)


# --------------------------------------------------------------------------
# payload normalisation: stock CGI JSON -> cgminer-shaped summary/stats
# --------------------------------------------------------------------------

def _unwrap(data):
    """Peel the {"DATA": {...}} envelope stock CGIs like to add."""
    if isinstance(data, dict) and isinstance(data.get("DATA"), dict):
        return data["DATA"]
    return data


def _walk_dicts(node, depth=0):
    """Yield every dict in a JSON tree (breadth-first, depth-limited)."""
    if isinstance(node, dict):
        yield node
        if depth < 3:
            for value in node.values():
                yield from _walk_dicts(value, depth + 1)
    elif isinstance(node, list) and depth < 3:
        for item in node:
            yield from _walk_dicts(item, depth + 1)


def _to_cgminer_shape(data) -> tuple[dict, dict]:
    """Extract a (summary, stats) pair in cgminer shape from a CGI reply."""
    data = _unwrap(data)
    if not isinstance(data, dict):
        return {}, {}

    # Best case: the reply already carries cgminer sections.
    if isinstance(data.get("SUMMARY"), list) or isinstance(data.get("STATS"), list):
        return _first(data.get("SUMMARY")), data

    # Otherwise merge every dict that carries recognisable miner keys.
    summary: dict = {}
    stats: dict = {}
    for node in _walk_dicts(data):
        for key, value in node.items():
            key = str(key)
            if re.fullmatch(r"chain_acs\d+", key) or \
                    re.fullmatch(r"temp\d+(_\d+)?", key) or \
                    re.fullmatch(r"fan\d+", key) or \
                    key in ("chain_rate_ideal", "chain_rate_real"):
                stats.setdefault(key, value)
            elif key in ("Elapsed", "GHS 5s", "GHS av", "MHS av", "Type", "Model"):
                summary.setdefault(key, value)
                stats.setdefault(key, value)
    return summary, stats


def _first(section) -> dict:
    if isinstance(section, list) and section and isinstance(section[0], dict):
        return section[0]
    if isinstance(section, dict):
        return section
    return {}


def _looks_like_miner_status(data) -> bool:
    summary, stats = _to_cgminer_shape(data)
    merged = report._merged_stats(stats) if isinstance(stats, dict) else {}
    haystack = merged if merged else stats
    return any(re.fullmatch(r"chain_acs\d+", str(k)) for k in haystack) \
        or "GHS av" in summary or "Type" in summary


# --------------------------------------------------------------------------
# client
# --------------------------------------------------------------------------

class BitmainClient:
    """Read-only client for one stock-firmware miner's web CGI API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 3.0,
                 username: str = "root", password: str = "root"):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.auth = DigestAuth(username, password)

    def get_json(self, path: str):
        """GET one CGI path with digest auth; return parsed JSON."""
        url = f"http://{self.host}:{self.port}{path}"
        status, headers, body = self._raw_get(url, path, signed=False)
        if status == 401:
            challenge = headers.get("WWW-Authenticate", "")
            if "digest" not in challenge.lower():
                raise BitmainError(f"GET {path} -> HTTP 401 (no digest challenge)")
            self.auth.learn(challenge)
            status, headers, body = self._raw_get(url, path, signed=True)
        if status != 200:
            raise BitmainError(f"GET {path} -> HTTP {status}")
        try:
            return json.loads(body.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise BitmainError(f"GET {path} -> non-JSON reply") from exc

    def _raw_send(self, method: str, url: str, uri: str, body=None,
                  extra_headers: dict | None = None, signed: bool = False):
        headers = {"User-Agent": "BeeSky"}
        if extra_headers:
            headers.update(extra_headers)
        if signed:
            auth_header = self.auth.header(method, uri)
            if auth_header:
                headers["Authorization"] = auth_header
        request = urllib.request.Request(url, headers=headers, data=body,
                                         method=method)
        try:
            with _OPENER.open(request, timeout=self.timeout) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read() if exc.fp else b""
        except (urllib.error.URLError, OSError) as exc:
            raise BitmainError(f"cannot reach {url} ({exc})") from exc

    def _authed_send(self, method: str, path: str, body=None,
                     extra_headers: dict | None = None):
        """Digest-auth send: sign at once when the challenge is already
        known (the usual case — a status GET preceded us), otherwise learn
        it from the 401 and retry signed, like get_json does."""
        url = f"http://{self.host}:{self.port}{path}"
        status, headers, resp_body = self._raw_send(
            method, url, path, body, extra_headers,
            signed=self.auth.challenge is not None)
        if status == 401:
            challenge = headers.get("WWW-Authenticate", "")
            if "digest" not in challenge.lower():
                raise BitmainError(
                    f"{method} {path} -> HTTP 401 (no digest challenge)")
            self.auth.learn(challenge)
            status, headers, resp_body = self._raw_send(
                method, url, path, body, extra_headers, signed=True)
        return status, headers, resp_body

    def get_text(self, path: str) -> str:
        """GET one path with digest auth; return the raw body as text.

        For the plain-text CGIs (``/cgi-bin/miner_type.cgi``,
        ``/cgi-bin/patch_success.cgi``) whose replies are not JSON.
        """
        status, _headers, body = self._authed_send("GET", path)
        if status != 200:
            raise BitmainError(f"GET {path} -> HTTP {status}")
        return body.decode("utf-8", errors="replace")

    def post_multipart(self, path: str, field: str, filename: str,
                       data: bytes, extra_fields: dict | None = None,
                       boundary: str | None = None):
        """Multipart-upload one file with digest auth; return (status, body).

        Used for ``/cgi-bin/upgrade.cgi`` — the stock firmware-install
        endpoint (and the .bmu uploads of the unlock sequence). The file
        field name on the stock upgrade form is ``file``.
        """
        fields = [(field, filename, data, "application/octet-stream")]
        for key, value in (extra_fields or {}).items():
            fields.append((key, None, str(value).encode("utf-8"), None))
        body, content_type = build_multipart_body(fields, boundary=boundary)
        status, _headers, resp_body = self._authed_send(
            "POST", path, body, {"Content-Type": content_type})
        return status, resp_body

    def get_status_code(self, path: str) -> int:
        """GET one path with digest auth; return just the HTTP status.

        For action CGIs such as /cgi-bin/reboot.cgi whose reply body is
        HTML (or dropped mid-flight as the control board goes down) —
        the status line is the whole answer.
        """
        url = f"http://{self.host}:{self.port}{path}"
        status, headers = self._raw_status(url, path, signed=False)
        if status == 401:
            challenge = headers.get("WWW-Authenticate", "")
            if "digest" not in challenge.lower():
                return status
            self.auth.learn(challenge)
            status, _headers = self._raw_status(url, path, signed=True)
        return status

    def _raw_status(self, url: str, uri: str, signed: bool):
        headers = {"User-Agent": "BeeSky"}
        if signed:
            auth_header = self.auth.header("GET", uri)
            if auth_header:
                headers["Authorization"] = auth_header
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with _OPENER.open(request, timeout=self.timeout) as resp:
                try:
                    resp.read()
                except (OSError, http.client.HTTPException):
                    pass  # body is irrelevant; the board may already be down
                return resp.status, resp.headers
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers
        except (urllib.error.URLError, OSError) as exc:
            raise BitmainError(f"cannot reach {url} ({exc})") from exc

    def _raw_get(self, url: str, uri: str, signed: bool):
        headers = {"Accept": "application/json", "User-Agent": "BeeSky"}
        if signed:
            auth_header = self.auth.header("GET", uri)
            if auth_header:
                headers["Authorization"] = auth_header
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with _OPENER.open(request, timeout=self.timeout) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read() if exc.fp else b""
        except (urllib.error.URLError, OSError) as exc:
            raise BitmainError(f"cannot reach {url} ({exc})") from exc

    # -- endpoints -----------------------------------------------------------
    def miner_status(self) -> dict:
        """Fetch the miner status payload (tries the known CGI paths)."""
        errors: list[str] = []
        for path in STATUS_PATHS:
            try:
                data = self.get_json(path)
            except BitmainError as exc:
                errors.append(str(exc))
                continue
            if isinstance(data, dict) and data:
                return data
            errors.append(f"GET {path} -> empty reply")
        raise BitmainError("; ".join(errors))

    def system_info(self) -> dict:
        data = _unwrap(self.get_json(SYSINFO_PATH))
        return data if isinstance(data, dict) else {}

    # -- detection -------------------------------------------------------------
    def probe(self) -> dict | None:
        """Return the status payload if this host is a stock miner, else None."""
        try:
            data = self.miner_status()
        except BitmainError:
            return None
        return data if _looks_like_miner_status(data) else None

    # -- record building ---------------------------------------------------------
    def fetch_record(self, ip: str | None = None,
                     status_data: dict | None = None) -> dict:
        """Fetch status (+ system info for the model) and build a record."""
        ip = ip or self.host
        data = status_data if status_data is not None else self.miner_status()
        summary, stats = _to_cgminer_shape(data)
        if not summary.get("Type") and not summary.get("Model"):
            try:
                info = self.system_info()
            except BitmainError:
                info = {}
            model = (info.get("minertype") or info.get("miner_type")
                     or info.get("Type"))
            if model:
                summary["Type"] = model
        return report.build_record(ip, summary, stats, source="stock")
