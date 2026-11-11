"""IP-Report listener — the hardware button on a miner broadcasts its
address, and BeeSky listens (v0.34.0, docs/ipreport-mapping.md).

Evidence (two independent open-source implementations, both read
2026-11-12):

* asic-rs (256foundation, the pyasic lineage), src/listener.rs:
  ``AntMinerListener`` binds ``UdpSocket::bind("0.0.0.0:14235")`` and
  treats the datagram's SENDER address as the miner
  (``factory.get_miner(addr.ip())``) — the payload is never parsed.
  ``WhatsMinerListener`` binds ``0.0.0.0:8888`` the same way.
* Find-My-Miner (OBitsPlease), IpReportListener.cs: ``DefaultPort =
  14235``; ``Parse(sender, data)`` decodes up to 200 bytes of ASCII
  text, extracts the first private IPv4 and the first MAC
  (colon- or dash-separated, normalised to upper-case colon form),
  ignores public IPs claimed in the payload, falls back to the
  sender address, and renders binary/oversized payloads safely.
  Only private-network senders are accepted.

The exact canonical Antminer payload bytes remain UNKNOWN (no real
capture in either source) — so, like both references, the parser
does NOT depend on a fixed format: regex extraction + sender
fallback accept any text form. Whatsminer 8888 is SINGLE-SOURCE
(asic-rs only) and is labelled as such wherever it surfaces.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import threading
import time
from dataclasses import dataclass, field

ANTMINER_PORT = 14235
WHATS_MINER_PORT = 8888
MAX_TEXT_LENGTH = 200  # Find-My-Miner's cap, adopted verbatim

_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b")


def is_private_ip(ip: str) -> bool:
    """True for RFC-1918 / link-local addresses (the only senders and
    the only payload claims worth trusting). Loopback is NOT private
    here — tests pass it explicitly via ``allow_loopback``."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.is_private and not addr.is_loopback


def is_acceptable_sender(ip: str, allow_loopback: bool = False) -> bool:
    """Mirror of Find-My-Miner's IsAcceptableSender: private-network
    hosts only (loopback only for tests)."""
    if allow_loopback:
        try:
            if ipaddress.ip_address(ip).is_loopback:
                return True
        except ValueError:
            return False
    return is_private_ip(ip)


def parse_report(sender: str, data: bytes,
                 received_at: float | None = None) -> dict:
    """Turn one untrusted datagram into a safe, displayable report.

    Returns {"received_at", "sender", "text", "ip", "mac",
    "family"} where "ip" is the first private IPv4 found in the
    payload (or None — the caller falls back to "sender") and "mac"
    is the first MAC found, normalised to upper-case colon form.
    Binary payloads (more than 30% unprintable bytes) render as a
    "(binary) <hex>" preview, never raw bytes. "family" is filled
    in by the listener from the receiving port, not here.
    """
    raw = data[:MAX_TEXT_LENGTH]
    unprintable = sum(1 for b in raw if b < 0x20 and b != 0x09 or b > 0x7E)
    if raw and unprintable * 10 > len(raw) * 3:
        text = "(binary) " + raw[:48].hex()
    else:
        text = "".join(
            chr(b) if 0x20 <= b <= 0x7E else " "
            for b in raw).strip()
    reported_ip = None
    for match in _IPV4_RE.finditer(text):
        candidate = match.group(0)
        if is_private_ip(candidate):
            reported_ip = candidate
            break
    mac_match = _MAC_RE.search(text)
    mac = (mac_match.group(0).replace("-", ":").upper()
           if mac_match else None)
    return {
        "received_at": received_at if received_at is not None
        else time.time(),
        "sender": sender,
        "text": text,
        "ip": reported_ip,
        "mac": mac,
        "family": None,
    }


@dataclass
class IpReportListener:
    """Passive UDP listener for miner IP-Report broadcasts.

    Binds 0.0.0.0 on the Antminer port (14235, CORROBORATED) and,
    unless disabled, the Whatsminer port (8888, SINGLE-SOURCE).
    Sends nothing. Each accepted datagram is parsed and handed to
    ``on_report`` as a dict (see parse_report) with "family" set to
    "antminer" / "whatsminer" by the receiving port. Public or
    otherwise unacceptable senders are dropped silently.
    """

    on_report: object = None  # callable(dict) -> None
    ports: tuple[int, ...] = (ANTMINER_PORT, WHATS_MINER_PORT)
    whatsminer_port: int = WHATS_MINER_PORT  # the port that tags
    # reports "whatsminer" (overridable for tests that cannot bind
    # the real 8888)
    allow_loopback: bool = False
    _sockets: list = field(default_factory=list, init=False, repr=False)
    _threads: list = field(default_factory=list, init=False, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event,
                                   init=False, repr=False)

    def _family(self, port: int) -> str:
        return "whatsminer" if port == self.whatsminer_port else "antminer"

    def handle_datagram(self, data: bytes, sender: str,
                        port: int) -> dict | None:
        """Accept-check + parse one received datagram (the socket
        loop calls this; tests call it directly — the sandbox
        forbids UDP sendto even on loopback, so the receive path is
        verified here, not over the wire). Returns the report dict
        (with "family" set) or None when the sender is unacceptable.
        """
        if not is_acceptable_sender(sender, self.allow_loopback):
            return None
        report = parse_report(sender, data)
        report["family"] = self._family(port)
        try:
            self.on_report(report)
        except Exception:  # noqa: BLE001 — a callback must never
            # kill the listener; the report is already dropped for
            # this consumer, the socket keeps listening.
            pass
        return report

    def _listen_one(self, port: int) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            # Port already taken (e.g. Bitmain's IP Reporter is
            # running) — that listener owns the reports; report the
            # failure to the caller instead of crashing the app.
            self._sockets.append(("failed", port))
            return
        sock.settimeout(0.2)
        self._sockets.append(sock)
        while not self._stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            self.handle_datagram(data, addr[0], port)

    def start(self) -> list[int]:
        """Bind + start listening on each configured port. Returns
        the ports that bound successfully (empty = nothing
        listening — the caller reports "Failed to start…")."""
        self._stop.clear()
        self._sockets = []
        self._threads = []
        for port in self.ports:
            thread = threading.Thread(target=self._listen_one,
                                      args=(port,), daemon=True)
            thread.start()
            self._threads.append(thread)
        # Give the bind a moment to settle, then report which
        # sockets actually bound (a "failed" marker means the port
        # was already taken).
        time.sleep(0.05)
        return self.bound_ports()

    def bound_ports(self) -> list[int]:
        """Ports currently bound (after start)."""
        out = []
        for sock in self._sockets:
            if isinstance(sock, tuple):
                continue
            try:
                out.append(sock.getsockname()[1])
            except OSError:
                continue
        return out

    def stop(self) -> None:
        """Stop listening and close the sockets."""
        self._stop.set()
        for sock in self._sockets:
            if isinstance(sock, tuple):
                continue
            try:
                sock.close()
            except OSError:
                pass
        for thread in self._threads:
            thread.join(timeout=1.0)
        self._sockets = []
        self._threads = []
