"""Network discovery of miners.

Discovery recipe (same shape as mature fleet tools): for every host in the
target, walk the adapter chain in a fixed order —

  1. cgminer RPC on TCP 4028 (Bitmain & most forks; richest data)
  2. VNish/HashCore dashd HTTP API on :80 (GET /api/v1/summary signature)
  3. Bitmain stock web CGI on :80 (digest auth, /cgi-bin/get_miner_status.cgi)

— and keep the first adapter that answers like a miner. Probing is threaded
with bounded workers and short timeouts so a /24 scans in seconds.

Multi-credential scans (v0.23): fleets run several machine lines with
different web logins, so the authenticated steps (dashd /unlock, stock
digest) accept a list of credential sets — each tagged "any" / "stock"
/ "vnish" — and try them family-first (see ordered_creds). The winning
set's label is carried on the candidate into the record (cred_label).
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .bitmain import BitmainClient
from .cgminer import CgminerClient
from .dashd import DashdClient, DashdError

HTTP_PORT = 80
CGMINER_PORT = 4028
MAX_HOSTS = 4096  # refuse absurd ranges; a repair bench never needs more
DEFAULT_WORKERS = 64

FALLBACK_TARGET = "192.168.1.0/24"
# UDP "connect" sends nothing; the address is only a routing oracle
# for getsockname(). Any unroutable/public address works.
_PROBE_PEER = ("8.8.8.8", 80)


def _primary_lan_ipv4() -> str | None:
    """This machine's primary LAN IPv4, or None when undetectable.

    The classic UDP-connect trick: opening a datagram socket and
    "connecting" it sends no packet — it only makes the kernel pick
    the outgoing interface, whose address getsockname() then reports.
    Loopback / link-local / unspecified results are not a LAN (an
    offline laptop reports its loopback or a 169.254 address), so
    they count as undetectable. Never raises.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(_PROBE_PEER)
            ip = sock.getsockname()[0]
        addr = ipaddress.ip_address(ip)
    except Exception:
        return None
    if addr.is_loopback or addr.is_link_local or addr.is_unspecified:
        return None
    return ip


def default_scan_target() -> str:
    """Pre-fill for scan-target fields: this machine's own /24.

    First-run UX (v0.19.6): the old hard-coded 192.168.1.0/24 default
    found zero miners on every other subnet and read as "the app
    can't scan". Detecting the laptop's own subnet makes the first
    scan just work; anything undetectable falls back to the historic
    default. The field stays editable — this is only a pre-fill.
    """
    ip = _primary_lan_ipv4()
    if ip is None:
        return FALLBACK_TARGET
    return str(ipaddress.ip_network(f"{ip}/24", strict=False))


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
    # Multi-credential results (v0.23): which saved set authenticated,
    # so the record can say so and the fetch stage can reuse it.
    cred_label: str | None = None   # winning set's label (None = default/RPC)
    dashd_token: str | None = None  # JWT minted by the winning dashd login
    dashd_api_key: str | None = None  # x-api-key of the winning vnish set
    username: str = "root"          # winning stock cred — fetch reuses it
    password: str = "root"


def parse_targets(spec: str) -> list[str]:
    """Expand a target spec into the union of its hosts' IPv4 addresses.

    The spec is a comma-separated list of items (multi-range scans,
    v0.19.6); each item is one of:
      * single IP        "192.168.1.50"
      * CIDR             "192.168.1.0/24"
      * inclusive range  "192.168.1.10-192.168.1.60"

    The union is de-duplicated preserving first-seen order (each item
    expands in ascending order, so a single item yields exactly the
    ascending list it always did; scan results are IP-sorted later
    regardless). One invalid item rejects the whole spec — a typo
    must not silently scan only part of the farm.
    """
    hosts: list[str] = []
    seen: set[str] = set()

    def add(ip: str) -> None:
        if ip not in seen:
            seen.add(ip)
            hosts.append(ip)

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "/" in part:
            net = ipaddress.ip_network(part, strict=False)
            for ip in net.hosts() or [net.network_address]:
                add(str(ip))
        elif "-" in part:
            start_s, end_s = (p.strip() for p in part.split("-", 1))
            start = int(ipaddress.ip_address(start_s))
            end = int(ipaddress.ip_address(end_s))
            if end < start:
                raise ValueError(f"range end before start: {part!r}")
            for i in range(start, end + 1):
                add(str(ipaddress.ip_address(i)))
        else:
            add(str(ipaddress.ip_address(part)))
    if not hosts:
        raise ValueError(f"no hosts in target spec: {spec!r}")
    if len(hosts) > MAX_HOSTS:
        raise ValueError(f"target too large: {len(hosts)} hosts (max {MAX_HOSTS})")
    return hosts


def _port_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


CRED_TYPES = ("any", "stock", "vnish")


def cred_type(entry: dict) -> str:
    """A credential set's machine-type tag, normalised (v0.23).

    Only "stock" / "vnish" are family tags; a missing or unknown tag
    means "any" (back-compat with untyped sets).
    """
    tag = entry.get("type")
    return tag if tag in ("stock", "vnish") else "any"


def ordered_creds(creds: list[dict], family: str) -> list[dict]:
    """Authentication try-order against one adapter family (v0.23).

    Sets tagged for *family* go first in saved order, then "any"
    sets, then all remaining sets in saved order: detection picks
    the likely login first, but a wrong tag never locks a machine
    out — every set is still tried before giving up.
    """
    return ([c for c in creds if cred_type(c) == family]
            + [c for c in creds if cred_type(c) == "any"]
            + [c for c in creds if cred_type(c) not in (family, "any")])


def probe_host(ip: str, timeout: float = 1.5, http_port: int = HTTP_PORT,
               cgminer_port: int = CGMINER_PORT, username: str = "root",
               password: str = "root", api_key: str | None = None,
               token: str | None = None,
               creds: list[dict] | None = None) -> Candidate | None:
    """Probe one host through the adapter chain; return a Candidate or None.

    *creds* (v0.23) is an explicit credential-set list — dicts with
    "label" / "user" / "password" / "type", e.g. loaded from a
    --creds-file. When given, authenticated adapters try the sets in
    family order (see ordered_creds) and the winner's label lands on
    the candidate. When None, behaviour is exactly the historic one:
    the single *username*/*password* pair (factory root/root) for
    stock digest auth and anonymous dashd reads.
    """
    cand = Candidate(ip=ip, http_port=http_port, cgminer_port=cgminer_port)
    cand.username = username
    cand.password = password
    if creds is None:
        cred_list = [{"label": None, "user": username,
                      "password": password, "type": "any"}]
        explicit_creds = False
    else:
        cred_list = creds
        explicit_creds = True
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
        dashd_summary, dashd_status = dashd.probe_detail()
        if dashd_summary is not None:
            cand.source = "vnish"
            miner = dashd_summary.get("miner") or {}
            cand.model = miner.get("miner_type")
            cand.summary = dashd_summary
            return cand

        # dashd login (v0.23): with an explicit creds list, a dashd
        # that refuses anonymous reads gets one /unlock attempt per
        # set — "vnish"-tagged sets first, then "any", then the rest.
        # The winner's JWT rides the candidate into the fetch stage.
        # (Skipped when an api-key/token was supplied: that IS the
        # dashd auth, already handled above.)
        if explicit_creds and not api_key and not token:
            for entry in ordered_creds(cred_list, "vnish"):
                entry_key = entry.get("api_key")
                if entry_key:
                    # API-key method (HashCore's vnish variant): the
                    # x-api-key header INSTEAD of a login — no /unlock.
                    client = DashdClient(ip, port=http_port,
                                         timeout=fetch_timeout,
                                         api_key=entry_key)
                    unlocked = client.probe()
                    if unlocked is not None:
                        cand.source = "vnish"
                        cand.cred_label = entry.get("label")
                        cand.dashd_api_key = entry_key
                        miner = unlocked.get("miner") or {}
                        cand.model = miner.get("miner_type")
                        cand.summary = unlocked
                        return cand
                    continue
                client = DashdClient(ip, port=http_port,
                                     timeout=fetch_timeout)
                try:
                    client.unlock(entry["password"])
                except DashdError:
                    continue
                unlocked = client.probe()
                if unlocked is not None:
                    cand.source = "vnish"
                    cand.cred_label = entry.get("label")
                    cand.dashd_token = client.token
                    miner = unlocked.get("miner") or {}
                    cand.model = miner.get("miner_type")
                    cand.summary = unlocked
                    return cand

        # Stock digest auth: try the sets in family order; the first
        # one the miner accepts claims it, and the fetch stage reuses
        # exactly that set.
        for entry in ordered_creds(cred_list, "stock"):
            bitmain = BitmainClient(ip, port=http_port,
                                    timeout=fetch_timeout,
                                    username=entry["user"],
                                    password=entry["password"])
            status_data = bitmain.probe()
            if status_data is not None:
                cand.source = "stock"
                cand.status_data = status_data
                cand.username = entry["user"]
                cand.password = entry["password"]
                cand.cred_label = entry.get("label")
                return cand

        # Locked dashd (v0.23, explicit creds only): anonymous
        # /summary answered 401 and no supplied login unlocked it —
        # still surface the host as a vnish candidate so the fetch
        # stage reports the auth error instead of the miner silently
        # vanishing from the scan. (After the stock step on purpose:
        # stock hosts 401 their CGI paths too, and a stock miner must
        # be claimed by stock, never by this fallback.)
        if explicit_creds and dashd_status == 401:
            cand.source = "vnish"
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
    creds: list[dict] | None = None,
) -> list[Candidate]:
    """Scan a target spec and return live miner candidates, IP-sorted."""
    ips = parse_targets(spec)
    workers = max(1, min(workers, len(ips)))
    probe_args = dict(timeout=timeout, http_port=http_port,
                      cgminer_port=cgminer_port, username=username,
                      password=password, api_key=api_key, token=token,
                      creds=creds)
    found: list[Candidate] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for cand in pool.map(lambda ip: probe_host(ip, **probe_args), ips):
            if cand is not None:
                found.append(cand)
    found.sort(key=lambda c: int(ipaddress.ip_address(c.ip)))
    return found
