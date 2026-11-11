"""MicroBT Whatsminer socket client (API v2 dialect, TCP 4028).

Ported from HashCore Toolkit's MicroBT support as dissected in
docs/vendor-coverage-mapping.md §1. The evidenced contract:

  * requests are JSON command envelopes ``{"cmd": "<name>"}`` —
    NOT the cgminer ``{"command": ...}`` envelope (a modern
    Whatsminer does not answer the cgminer envelope at all, and a
    cgminer device answers this dialect with a STATUS-E error, so
    the two dialects cannot mis-claim each other);
  * replies wrap their payload in a ``Msg`` envelope — a LIST for
    summary (its item is the cgminer-shaped summary dict) and for
    devs/pools, a dict for version/info;
  * the summary item speaks the cgminer field vocabulary (``MHS
    5s`` / ``MHS av``, ``Elapsed``, ``Accepted`` ...) plus the
    Whatsminer-distinctive ``Fan Speed In`` / ``Fan Speed Out``
    pair — the detection fingerprint, since the Antminer cgminer
    SUMMARY carries no fan fields at all;
  * privileged commands ride a token session minted by
    ``{"cmd": "get_token"}``, but HOW the token is computed from
    the password is not in the dissected contract — so this
    client is READ-ONLY by design: it never sends get_token, and
    actions for this family stay honest gaps (mapping G-W1).

Reads are anonymous, exactly like cgminer's.
"""

from __future__ import annotations

import json
import socket

from . import report
from .cgminer import _loads_lenient

DEFAULT_PORT = 4028


class WhatsminerError(Exception):
    """Raised when a Whatsminer cannot be reached or refuses a read."""


def _status_error(resp: dict) -> str | None:
    """The refusal message of a STATUS-E envelope, else None."""
    status = resp.get("STATUS")
    if isinstance(status, list) and status and isinstance(status[0], dict):
        head = status[0]
        if head.get("STATUS") == "E":
            return str(head.get("Msg") or "command refused")
    return None


def _msg(resp: dict):
    """The reply's Msg payload (list or dict), or None."""
    msg = resp.get("Msg")
    return msg if isinstance(msg, (list, dict)) else None


def is_whatsminer_summary(item) -> bool:
    """Detection fingerprint (mapping §1.2): a summary item that
    carries the Whatsminer fan pair. Nothing else in the dissected
    fleet puts fan speeds in a socket summary."""
    return isinstance(item, dict) and (
        "Fan Speed In" in item or "Fan Speed Out" in item)


class WhatsminerClient:
    """Minimal read-only client for one Whatsminer's socket API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def command(self, name: str) -> dict:
        """Send one ``{"cmd": name}`` and return the parsed reply."""
        request = (json.dumps({"cmd": name}) + "\n").encode("ascii")
        chunks: list[bytes] = []
        try:
            with socket.create_connection((self.host, self.port),
                                          timeout=self.timeout) as sock:
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
                        if chunks:
                            break
                        raise WhatsminerError(
                            f"timeout waiting for '{name}' reply") from None
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if b"\x00" in chunk:
                        break
        except WhatsminerError:
            raise
        except OSError as exc:
            raise WhatsminerError(
                f"cannot reach {self.host}:{self.port} ({exc})") from exc
        try:
            resp = _loads_lenient(b"".join(chunks))
        except Exception as exc:
            raise WhatsminerError(str(exc)) from exc
        err = _status_error(resp)
        if err is not None:
            raise WhatsminerError(f"{name} refused: {err}")
        return resp

    # -- reads ------------------------------------------------------------

    def summary_item(self) -> dict:
        """The summary item (first entry of the Msg list)."""
        resp = self.command("summary")
        msg = _msg(resp)
        if isinstance(msg, list):
            for entry in msg:
                if isinstance(entry, dict):
                    return entry
            return {}
        if isinstance(msg, dict):
            return msg
        # Tolerated fallback: a cgminer-shaped SUMMARY section.
        section = resp.get("SUMMARY")
        if isinstance(section, list) and section \
                and isinstance(section[0], dict):
            return section[0]
        return {}

    def devs(self) -> list[dict]:
        """Per-board entries from the `devs` read (possibly empty)."""
        resp = self.command("devs")
        msg = _msg(resp)
        if isinstance(msg, list):
            return [e for e in msg if isinstance(e, dict)]
        if isinstance(msg, dict):
            return [msg]
        return []

    def pools_list(self) -> list[dict]:
        """Pool entries from the `pools` read (possibly empty)."""
        resp = self.command("pools")
        msg = _msg(resp)
        if isinstance(msg, list):
            return [e for e in msg if isinstance(e, dict)]
        return []

    def pools_normalised(self) -> list[dict] | None:
        """Scan-record pool list, cgminer-enrichment shaped.

        [{url, worker, status}] verbatim; None on any failure —
        enrichment must cost the field, never the record (the
        v0.28 rule, same as CgminerClient.pools_normalised).
        """
        try:
            entries = self.pools_list()
        except Exception:  # noqa: BLE001 — enrichment contract
            return None
        if not entries:
            return None
        return [{
            "url": entry.get("URL"),
            "worker": entry.get("User"),
            "status": entry.get("Status"),
        } for entry in entries]

    def version_info(self) -> dict:
        """The version read's Msg dict ({} when it carries none)."""
        resp = self.command("version")
        msg = _msg(resp)
        return msg if isinstance(msg, dict) else {}

    # -- record -----------------------------------------------------------

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        Rate truth (mapping §1.5): the MHS pair is the device's own
        scale — ``ghs_*`` carries MHS/1000 and the native rate is
        displayed in TH/s (MHS/1e6), the display-scale convention
        report._native_rate applies to GHS fields. Per-chip data
        is NOT in the evidenced contract, so chains carry board
        temperatures only and chip counts stay 0/0 (G-W2); power
        is not read (G-W4).
        """
        ip = ip or self.host
        summary = self.summary_item()
        if not summary:
            raise WhatsminerError("summary read returned no item")

        model = summary.get("Type") or summary.get("Model")
        if not model:
            try:
                version = self.version_info()
            except WhatsminerError:
                version = {}
            model = version.get("Type") or version.get("Model") \
                or "WhatsMiner"
        elapsed = int(report._num(summary.get("Elapsed"), 0) or 0)

        mhs_5s = report._num(summary.get("MHS 5s"))
        mhs_av = report._num(summary.get("MHS av"))
        if mhs_5s is not None or mhs_av is not None:
            gh_5s = mhs_5s / 1000.0 if mhs_5s is not None else None
            gh_av = mhs_av / 1000.0 if mhs_av is not None else None
            mhs_main = mhs_5s if mhs_5s is not None else mhs_av
            rate_value = mhs_main / 1_000_000.0
            rate_unit = "TH/s"
        else:
            gh_5s = report._num(summary.get("GHS 5s"))
            gh_av = report._num(summary.get("GHS av"))
            rate_value, rate_unit = report._native_rate(summary, model)

        fans: list[int] = []
        for key in ("Fan Speed In", "Fan Speed Out"):
            rpm = report._num(summary.get(key))
            if rpm is not None:
                fans.append(int(rpm))

        chains: list[dict] = []
        try:
            boards = self.devs()
        except WhatsminerError:
            boards = []
        for idx, board in enumerate(boards, start=1):
            temp = report._num(board.get("Temperature"))
            chains.append({
                "index": idx,
                "chips_total": 0,
                "chips_alive": 0,
                "dead_positions": [],
                "temp_c": temp,
            })

        record = report._finalise_record(
            ip, str(model), elapsed, gh_5s, gh_av, chains, fans,
            "whatsminer", rate_value=rate_value, rate_unit=rate_unit)
        pools = self.pools_normalised()
        if pools is not None:
            record["pools"] = pools
        return record
