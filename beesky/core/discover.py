"""Network discovery of miners.

Discovery recipe (same shape as mature fleet tools): for every host in the
target, probe HTTP :80 first, then the cgminer RPC port :4028. A host that
answers the cgminer API is a live miner candidate. Probing is threaded with
bounded workers and short timeouts so a /24 scans in seconds.
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .cgminer import CgminerClient

HTTP_PORT = 80
CGMINER_PORT = 4028
MAX_HOSTS = 4096  # refuse absurd ranges; a repair bench never needs more
DEFAULT_WORKERS = 64


@dataclass
class Candidate:
    """One host that looks like a miner."""

    ip: str
    http_open: bool = False
    cgminer_open: bool = False
    cgminer_ok: bool = False  # answered a real `summary` command
    model: str | None = None
    summary: dict = field(default_factory=dict)


def parse_targets(spec: str) -> list[str]:
    """Expand a target spec into a sorted list of IPv4 addresses.

    Accepted forms (comma-separated mixes allowed):
      * single IP        "192.168.1.50"
      * CIDR             "192.168.1.0/24"
      * inclusive range  "192.168.1.10-192.168.1.60"
    """
    hosts: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "/" in part:
            net = ipaddress.ip_network(part, strict=False)
            hosts.extend(str(ip) for ip in net.hosts() or [net.network_address])
        elif "-" in part:
            start_s, end_s = (p.strip() for p in part.split("-", 1))
            start = int(ipaddress.ip_address(start_s))
            end = int(ipaddress.ip_address(end_s))
            if end < start:
                raise ValueError(f"range end before start: {part!r}")
            hosts.extend(str(ipaddress.ip_address(i)) for i in range(start, end + 1))
        else:
            hosts.append(str(ipaddress.ip_address(part)))
    if not hosts:
        raise ValueError(f"no hosts in target spec: {spec!r}")
    if len(hosts) > MAX_HOSTS:
        raise ValueError(f"target too large: {len(hosts)} hosts (max {MAX_HOSTS})")
    # Deduplicate and sort numerically.
    return sorted(set(hosts), key=lambda s: int(ipaddress.ip_address(s)))


def _port_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_host(ip: str, timeout: float = 1.5) -> Candidate | None:
    """Probe one host; return a Candidate if it looks like a miner."""
    cand = Candidate(ip=ip)
    cand.http_open = _port_open(ip, HTTP_PORT, timeout)
    cand.cgminer_open = _port_open(ip, CGMINER_PORT, timeout)
    if cand.cgminer_open:
        try:
            cand.summary = CgminerClient(ip, timeout=timeout).summary()
            cand.cgminer_ok = bool(cand.summary)
            cand.model = cand.summary.get("Type") or cand.summary.get("Model")
        except Exception:
            cand.cgminer_ok = False
    # Live miner = answers the cgminer API, or at minimum shows both the web
    # UI port and the cgminer port (API may be restricted on some firmware).
    if cand.cgminer_ok or (cand.cgminer_open and cand.http_open):
        return cand
    return None


def discover(
    spec: str, timeout: float = 1.5, workers: int = DEFAULT_WORKERS
) -> list[Candidate]:
    """Scan a target spec and return live miner candidates, IP-sorted."""
    ips = parse_targets(spec)
    workers = max(1, min(workers, len(ips)))
    found: list[Candidate] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for cand in pool.map(lambda ip: probe_host(ip, timeout), ips):
            if cand is not None:
                found.append(cand)
    found.sort(key=lambda c: int(ipaddress.ip_address(c.ip)))
    return found
