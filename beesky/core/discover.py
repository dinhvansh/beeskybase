"""Network discovery of miners.

Discovery recipe (same shape as mature fleet tools): for every host in the
target, walk the adapter chain in a fixed order —

  1. cgminer RPC on TCP 4028 (Bitmain & most forks; richest data)
  2. VNish/HashCore dashd HTTP API on :80 (GET /api/v1/summary signature)
  3. Bitmain stock web CGI on :80 (digest auth, /cgi-bin/get_miner_status.cgi)

— and keep the first adapter that answers like a miner. Probing is threaded
with bounded workers and short timeouts so a /24 scans in seconds.
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .bitmain import BitmainClient
from .cgminer import CgminerClient
from .dashd import DashdClient

HTTP_PORT = 80
CGMINER_PORT = 4028
MAX_HOSTS = 4096  # refuse absurd ranges; a repair bench never needs more
DEFAULT_WORKERS = 64


@dataclass
class Candidate:
    """One host that looks like a miner, with the adapter that claimed it."""

    ip: str
    source: str | None = None  # "cgminer" | "vnish" | "stock"
    http_open: bool = False
    cgminer_open: bool = False
    cgminer_ok: bool = False  # answered a real `summary` command
    model: str | None = None
    summary: dict = field(default_factory=dict)
    status_data: dict = field(default_factory=dict)  # stock probe payload cache
    http_port: int = HTTP_PORT
    cgminer_port: int = CGMINER_PORT


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


def probe_host(ip: str, timeout: float = 1.5, http_port: int = HTTP_PORT,
               cgminer_port: int = CGMINER_PORT, username: str = "root",
               password: str = "root", api_key: str | None = None,
               token: str | None = None) -> Candidate | None:
    """Probe one host through the adapter chain; return a Candidate or None."""
    cand = Candidate(ip=ip, http_port=http_port, cgminer_port=cgminer_port)
    cand.http_open = _port_open(ip, http_port, timeout)
    cand.cgminer_open = _port_open(ip, cgminer_port, timeout)

    # 1) cgminer RPC — richest data, try first whenever the port is open.
    if cand.cgminer_open:
        try:
            cand.summary = CgminerClient(
                ip, port=cgminer_port, timeout=timeout).summary()
            cand.cgminer_ok = bool(cand.summary)
        except Exception:
            cand.cgminer_ok = False
        if cand.cgminer_ok:
            cand.source = "cgminer"
            cand.model = cand.summary.get("Type") or cand.summary.get("Model")
            return cand

    # 2) + 3) HTTP adapters need the web port.
    if cand.http_open:
        fetch_timeout = max(timeout, 2.0)
        dashd = DashdClient(ip, port=http_port, timeout=fetch_timeout,
                            api_key=api_key, token=token)
        dashd_summary = dashd.probe()
        if dashd_summary is not None:
            cand.source = "vnish"
            miner = dashd_summary.get("miner") or {}
            cand.model = miner.get("miner_type")
            cand.summary = dashd_summary
            return cand

        bitmain = BitmainClient(ip, port=http_port, timeout=fetch_timeout,
                                username=username, password=password)
        status_data = bitmain.probe()
        if status_data is not None:
            cand.source = "stock"
            cand.status_data = status_data
            return cand

    # v0.1 fallback: both ports open but the RPC API would not talk (some
    # firmware restricts it) — still surface the host; the fetch stage will
    # produce a FETCH_ERROR record rather than silently dropping it.
    if cand.cgminer_open and cand.http_open:
        cand.source = "cgminer"
        return cand
    return None


def discover(
    spec: str, timeout: float = 1.5, workers: int = DEFAULT_WORKERS,
    http_port: int = HTTP_PORT, cgminer_port: int = CGMINER_PORT,
    username: str = "root", password: str = "root",
    api_key: str | None = None, token: str | None = None,
) -> list[Candidate]:
    """Scan a target spec and return live miner candidates, IP-sorted."""
    ips = parse_targets(spec)
    workers = max(1, min(workers, len(ips)))
    probe_args = dict(timeout=timeout, http_port=http_port,
                      cgminer_port=cgminer_port, username=username,
                      password=password, api_key=api_key, token=token)
    found: list[Candidate] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for cand in pool.map(lambda ip: probe_host(ip, **probe_args), ips):
            if cand is not None:
                found.append(cand)
    found.sort(key=lambda c: int(ipaddress.ip_address(c.ip)))
    return found
