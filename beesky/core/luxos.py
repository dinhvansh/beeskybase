"""LuxOS (LUXminer) adapter — TCP 4028 cgminer-compatible API.

Source: Luxor's own Firmware API docs
(docs/vendor-docs-mapping.md §2 — docs.luxor.tech, plus Luxor's
``luxos`` PyPI package as corroboration):

  * the API "follows the same pattern as the CGMiner API, that
    is, a raw TCP (not HTTP) connection which accepts commands
    in text or json format" — request ``{"command": "<name>"}``
    with an optional ``"parameter"`` string, reply in the cgminer
    envelope, connection closed after the reply. Port 4028;
    "always favor the TCP API" (an HTTP wrapper on 8080 exists
    and is not used here);
  * reads need NO session; writes need a session minted by
    ``logon`` (no password — sessions are coordination, NOT
    security, per the docs), passed as the first parameter,
    dropped with ``logoff``. Sessions expire after one minute
    (refreshed on use) and at most one exists at a time, so a
    failed logon means wait and retry — BeeSky never sends the
    forceful ``kill`` command;
  * detection: ``version`` answers with a STATUS Description
    starting ``"LUXminer"`` (Luxor's own CLI prints exactly
    ``LUXminer 2024.5.1.155432-f2badc0f``). Stock cgminer
    answers ``cgminer …`` / ``bmminer …`` and VNish does not
    answer this envelope at all, so the prefix cannot
    mis-claim any family BeeSky already detects.

Reads ride the shared CgminerClient and the shared record
builder (``summary`` / ``stats`` / ``pools`` in cgminer
vocabulary); the per-board temps and chip counts come from
STATS via the shared rules. Caveat (mapping §2.5): whether a
real LuxOS STATS carries ``chain_acs*`` at all is
hardware-unconfirmed — without them the record degrades to
temps-only, exactly like Avalon, and says so.
"""

from __future__ import annotations

from . import report
from .cgminer import CgminerClient, CgminerError

DEFAULT_PORT = 4028


class LuxosError(Exception):
    """Raised when a LuxOS miner cannot be reached or refuses."""


def is_luxos_version(resp: dict) -> bool:
    """Detection fingerprint (mapping §2.4): a ``version`` reply
    whose STATUS Description starts with "LUXminer". Positive-only
    — anything else is not a claim."""
    status = resp.get("STATUS")
    if isinstance(status, list) and status \
            and isinstance(status[0], dict):
        return str(status[0].get("Description") or "").startswith("LUXminer")
    return False


def _status_ok(resp: dict) -> tuple[bool, str]:
    """(accepted?, message) from a LuxOS STATUS section."""
    status = resp.get("STATUS")
    if isinstance(status, list) and status \
            and isinstance(status[0], dict):
        head = status[0]
        if head.get("STATUS") == "S":
            return True, str(head.get("Msg") or "ok")
        return False, str(head.get("Msg") or
                          f"STATUS {head.get('STATUS')}")
    return False, "no STATUS section in reply"


class LuxosClient:
    """Client for one LuxOS miner's TCP API (port 4028)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT,
                 timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._cg = CgminerClient(host, port=port, timeout=timeout)

    # -- reads (no session needed) --------------------------------------

    def version(self) -> dict:
        """The full ``version`` reply (detection reads this)."""
        try:
            return self._cg.command("version")
        except CgminerError as exc:
            raise LuxosError(str(exc)) from exc

    def is_luxos(self) -> bool:
        """True when this host answers like a LuxOS miner."""
        try:
            return is_luxos_version(self.version())
        except LuxosError:
            return False

    def fetch_record(self, ip: str | None = None) -> dict:
        """Normalise this miner into a shared status record.

        The cgminer-compatible read path: summary + stats through
        the shared builder (source "luxos"), pools enrichment in
        the v0.28 shape. Any failure is a LuxosError — the fetch
        stages turn it into an error record.
        """
        ip = ip or self.host
        try:
            summary = self._cg.summary()
            stats = self._cg.stats()
        except CgminerError as exc:
            raise LuxosError(str(exc)) from exc
        record = report.build_record(ip, summary, stats, source="luxos")
        pools = self._cg.pools_normalised()
        if pools is not None:
            record["pools"] = pools
        return record

    # -- sessions (writes only) ------------------------------------------

    def logon(self) -> str:
        """Mint a session; returns its SessionID (mapping §2.3).

        Raises LuxosError when no session could be created — the
        caller waits and retries; BeeSky never force-kills
        another session.
        """
        try:
            resp = self._cg.command("logon")
        except CgminerError as exc:
            raise LuxosError(f"logon failed: {exc}") from exc
        ok, msg = _status_ok(resp)
        session = resp.get("SESSION")
        session_id = None
        if isinstance(session, list) and session \
                and isinstance(session[0], dict):
            session_id = session[0].get("SessionID")
        if not ok or not session_id:
            raise LuxosError(f"logon failed: {msg}")
        return str(session_id)

    def logoff(self, session_id: str) -> None:
        """Drop a session; best-effort, never raises."""
        try:
            self._cg.command("logoff", session_id)
        except Exception:  # noqa: BLE001 — logoff is cleanup
            pass

    # -- actions -----------------------------------------------------------

    def rebootdevice(self) -> dict:
        """Reboot the device (Luxor's own CLI: ``--cmd rebootdevice``).

        Sent parameter-less, per the CLI's usage; whether a
        session is required is UNKNOWN in the docs read
        (mapping §2.6) — a refusal surfaces verbatim.
        """
        try:
            resp = self._cg.command("rebootdevice")
        except CgminerError as exc:
            raise LuxosError(f"rebootdevice failed: {exc}") from exc
        ok, msg = _status_ok(resp)
        if not ok:
            raise LuxosError(f"rebootdevice refused: {msg}")
        return resp

    def curtail(self, action: str) -> dict:
        """``curtail`` sleep/wakeup (mapping §2.6).

        ``sleep`` powers the hashboards + PSU off; ``wakeup``
        ramps them back. The session flow is logon -> curtail ->
        logoff (logoff always runs). Only the safe default wakeup
        form is sent — no ``mode=unsafe`` (the docs warn it
        stresses chips). Note the docs' persistence rule: a
        sleeping rig can ONLY be woken by ``wakeup`` — the state
        survives a reboot.
        """
        if action not in ("sleep", "wakeup"):
            raise LuxosError(f"unknown curtail action: {action!r}")
        session_id = self.logon()
        try:
            try:
                resp = self._cg.command(
                    "curtail", f"{session_id},{action}")
            except CgminerError as exc:
                raise LuxosError(f"curtail {action} failed: {exc}") from exc
        finally:
            self.logoff(session_id)
        ok, msg = _status_ok(resp)
        if not ok:
            raise LuxosError(f"curtail {action} refused: {msg}")
        return resp
