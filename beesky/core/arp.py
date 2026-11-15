"""MAC addresses from the local ARP table (v0.35) — the one data
source for the grid's MAC column that needs no miner cooperation.

A scan already talks to every miner over TCP, so by the time the
fetch stage runs the host's ARP cache holds the miner's MAC for
every IP it probed. Reading the table is a best-effort enrichment
only: it never raises, never fails a scan, and an IP with no ARP
entry simply keeps no ``mac`` on its record (the column shows
"—", as before). No adapter ever emits a MAC — this is the only
source, and it is the host's own cache, not the miner.

Parsers cover the three shapes the table takes:
  * Windows ``arp -a``: ``192.168.1.5  aa-bb-cc-dd-ee-ff  dynamic``
  * Linux ``ip neigh``: ``192.168.1.5 dev eth0 lladdr aa:bb:... REACHABLE``
  * BSD/macOS ``arp -an``: ``? (192.168.1.5) at aa:bb:... on en0 ...``

MACs normalise to upper-case colon form (``AA:BB:CC:DD:EE:FF``),
the same form the v0.34 IP-Report parser uses. Broadcast
(``ff:ff:ff:ff:ff:ff``) and incomplete entries are ignored.
"""

from __future__ import annotations

import re
import subprocess
import sys

_MAC_RE = re.compile(
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})"
    r".*?"
    r"(?<![0-9a-fA-F:-])"
    r"(?P<mac>[0-9a-fA-F]{1,2}(?:[:-][0-9a-fA-F]{1,2}){5})"
    r"(?![0-9a-fA-F:-])"
)
_IP_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

_BROADCAST = "FF:FF:FF:FF:FF:FF"


def normalise_mac(raw: str) -> str | None:
    """One MAC in any common form to ``AA:BB:CC:DD:EE:FF``; None when invalid."""
    if not isinstance(raw, str):
        return None
    parts = re.split(r"[:-]", raw.strip())
    if len(parts) != 6 or any(not 1 <= len(p) <= 2 for p in parts):
        return None
    try:
        octets = [int(p, 16) for p in parts]
    except ValueError:
        return None
    mac = ":".join(f"{o:02X}" for o in octets)
    return None if mac == _BROADCAST else mac


def parse_arp_table(text: str) -> dict[str, str]:
    """IP -> MAC from one ARP-table dump; malformed lines are skipped.

    A line contributes only when it carries BOTH a valid IPv4
    address and a valid MAC; the MAC may sit anywhere after the
    IP on the line (all three table shapes). Later lines win for
    a repeated IP.
    """
    table: dict[str, str] = {}
    if not isinstance(text, str):
        return table
    for line in text.splitlines():
        match = _MAC_RE.search(line)
        if not match:
            continue
        mac = normalise_mac(match.group("mac"))
        if mac is None:
            continue
        table[match.group("ip")] = mac
    return table


def _run_table_command(cmd: list[str]) -> dict[str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}
    return parse_arp_table(proc.stdout.decode("utf-8", errors="replace"))


def read_arp_table() -> dict[str, str]:
    """This host's ARP cache as IP -> MAC. Never raises; {} on any failure."""
    if sys.platform == "win32":
        return _run_table_command(["arp", "-a"])
    table = _run_table_command(["ip", "neigh"])
    if table:
        return table
    return _run_table_command(["arp", "-an"])
