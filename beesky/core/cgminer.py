"""cgminer RPC client (TCP 4028).

The cgminer API is a tiny JSON-over-TCP protocol used by Bitmain Antminers
and most cgminer/bmminer forks:

    request : {"command": "summary"}\n
    reply   : {"STATUS": [...], "SUMMARY": [{...}], "id": 1}\x00

Quirks handled here:
  * replies end with a trailing NUL byte (sometimes several);
  * firmware variants occasionally emit non-strict JSON (trailing commas,
    junk after the object), so parsing falls back to progressively more
    lenient strategies instead of failing outright.
"""

from __future__ import annotations

import json
import re
import socket

DEFAULT_PORT = 4028


class CgminerError(Exception):
    """Raised when a miner cannot be reached or its reply cannot be parsed."""


def _loads_lenient(raw: bytes) -> dict:
    """Parse a cgminer reply into a dict, tolerating firmware quirks."""
    text = raw.decode("utf-8", errors="replace").replace("\x00", "").strip()
    if not text:
        raise CgminerError("empty reply from miner API")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Common defect: trailing commas before } or ].
    cleaned = re.sub(r",(\s*[}\]])", r"\1", text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Last resort: parse the first complete JSON object and ignore any junk
    # appended after it.
    try:
        obj, _end = json.JSONDecoder().raw_decode(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    raise CgminerError(f"unparseable reply from miner API: {text[:120]!r}")


def _first_section(resp: dict, name: str) -> dict:
    """Return the first entry of a cgminer response section as a dict."""
    section = resp.get(name)
    if isinstance(section, list) and section and isinstance(section[0], dict):
        return section[0]
    if isinstance(section, dict):
        return section
    return {}


class CgminerClient:
    """Minimal client for one miner's cgminer RPC API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def command(self, name: str, parameter: str | None = None) -> dict:
        """Send one command and return the full parsed reply dict."""
        payload: dict = {"command": name}
        if parameter is not None:
            payload["parameter"] = parameter
        request = (json.dumps(payload) + "\n").encode("ascii")
        chunks: list[bytes] = []
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(request)
                try:
                    sock.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                while True:
                    try:
                        chunk = sock.recv(65536)
                    except socket.timeout:
                        # Some firmwares keep the socket open after replying;
                        # if we already have data, treat the reply as complete.
                        if chunks:
                            break
                        raise CgminerError(f"timeout waiting for '{name}' reply") from None
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if b"\x00" in chunk:
                        break
        except CgminerError:
            raise
        except OSError as exc:
            raise CgminerError(f"cannot reach {self.host}:{self.port} ({exc})") from exc
        return _loads_lenient(b"".join(chunks))

    def summary(self) -> dict:
        """Return the SUMMARY section as a flat dict."""
        return _first_section(self.command("summary"), "SUMMARY")

    def stats(self) -> dict:
        """Return STATS merged into one flat dict.

        Antminer replies carry two STATS entries (miner info + chain data);
        merging them in order gives one dict with Type, chain_acs*, temp*,
        fan* ... keys. The untouched entries stay under "stats_entries".
        """
        resp = self.command("stats")
        entries = resp.get("STATS")
        if not isinstance(entries, list):
            return _first_section(resp, "STATS")
        merged: dict = {}
        for entry in entries:
            if isinstance(entry, dict):
                merged.update(entry)
        merged["stats_entries"] = entries
        return merged

    def pools(self) -> dict:
        """Return the full pools reply dict (POOLS list inside)."""
        return self.command("pools")
