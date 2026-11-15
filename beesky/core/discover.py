"""Network discovery of miners.

Discovery recipe (same shape as mature fleet tools): for every host in the
target, walk the adapter chain in a fixed order —

  1. socket APIs on TCP 4028: the MicroBT Whatsminer dialect
     ({"cmd": ...} envelopes + the Fan Speed In/Out fingerprint)
     first, then cgminer RPC (Bitmain & most forks; richest data) —
     with a Canaan Avalon refinement on the cgminer claim (the
     STATS "MM ID" module fingerprint; v0.30, see
     docs/vendor-coverage-mapping.md) and a LuxOS refinement
     (the ``version`` Description starts "LUXminer"; v0.33.0,
     see docs/vendor-docs-mapping.md §2), Auradine and
     SealMiner refinements (the ``version`` reply carries
     "gcminer"/"fluxos" resp. "bdminer", case-insensitive;
     v0.38.0, see docs/vendor-docs2-mapping.md §1–§2),
     then the ePIC HTTP
     JSON probe (GET /summary, Hostname+Session+HBs gate;
     v0.37.0, see docs/epic-mapping.md §2) — an Epic miner
     answers the two earlier probes with non-parseable
     replies, so it falls through to the HTTP probe cleanly
  2. VNish/HashCore dashd HTTP API on :80 (GET /api/v1/summary signature)
  3. Bitmain stock web CGI on :80 (digest auth, /cgi-bin/get_miner_status.cgi)
  4. IceRiver web API on :80 (console-title gate, then the
     userpanel shape gate; v0.36.0, docs/vendor-oss-mapping.md §2)

— and keep the first adapter that answers like a miner. Probing is threaded
with bounded workers and short timeouts so a /24 scans in seconds.

Multi-credential scans (v0.23): fleets run several machine lines with
different web logins, so the authenticated steps (dashd /unlock, stock
digest) accept a list of credential sets — each tagged with a machine
family — and try them family-first (see ordered_creds). The winning
set's label is carried on the candidate into the record (cred_label).
Family tags (v0.30): the HashCore vendor set ported in
docs/vendor-coverage-mapping.md §6 — detection exists for whatsminer,
avalon, luxos (v0.33.0) and braiins + iceriver (v0.36.0,
docs/vendor-oss-mapping.md); epic (v0.37.0, docs/epic-mapping.md);
auradine + sealminer (v0.38.0, docs/vendor-docs2-mapping.md);
jasminer is still a tag-only family
(its contract is a named gap in
docs/vendor-oss-mapping.md §4); pit-bit has neither
a tag nor an adapter (G-PB1 in
docs/vendor-docs2-mapping.md §3).
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .auradine import is_auradine_version
from .bitmain import BitmainClient
from .braiins import is_braiins_version
from .cgminer import CgminerClient
from .dashd import DashdClient, DashdError
from .epic import EpicClient, is_epic_summary
from .iceriver import (DEFAULT_PASSWORD as ICERIVER_DEFAULT_PASSWORD,
                       IceRiverClient, IceRiverError, panel_model)
from .luxos import is_luxos_version
from .sealminer import is_sealminer_version
from .whatsminer import WhatsminerClient, is_whatsminer_summary

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
    source: str | None = None  # "cgminer" | "vnish" | "stock" |
    #                            "whatsminer" | "avalon" | "luxos" |
    #                            "braiins" | "iceriver" | "epic"
    http_open: bool = False
    cgminer_open: bool = False
    cgminer_ok: bool = False  # answered a real `summary` command
    model: str | None = None
    summary: dict = field(default_factory=dict)
    status_data: dict = field(default_factory=dict)  # stock probe payload cache
    stats_data: dict = field(default_factory=dict)  # cgminer-family stats
    # cache (v0.30: the probe's Avalon-refinement fetch, reused by
    # the fetch stage so a scan pays for the stats call once)
    http_port: int = HTTP_PORT
    cgminer_port: int = CGMINER_PORT
    # Multi-credential results (v0.23): which saved set authenticated,
    # so the record can say so and the fetch stage can reuse it.
    cred_label: str | None = None   # winning set's label (None = default/RPC)
    dashd_token: str | None = None  # JWT minted by the winning dashd login
    dashd_api_key: str | None = None  # x-api-key of the winning vnish set
    iceriver_password: str | None = None  # winning IceRiver web password
    # (v0.36.0: the panel probe tries iceriver-tagged sets, then the
    # factory default; the fetch stage reuses the winner)
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


CRED_TYPES = ("any", "stock", "vnish", "whatsminer", "avalon",
              "iceriver", "jasminer", "braiins", "luxos", "epic",
              "auradine", "sealminer")


def cred_type(entry: dict) -> str:
    """A credential set's machine-type tag, normalised (v0.23).

    The family tags are CRED_TYPES (v0.30: the HashCore vendor set —
    docs/vendor-coverage-mapping.md §6); a missing or unknown tag
    means "any" (back-compat with untyped sets).
    """
    tag = entry.get("type")
    return tag if tag in CRED_TYPES else "any"


def _avalon_fingerprint(stats: dict, summary: dict) -> bool:
    """Canaan Avalon fingerprint on a cgminer claim (v0.30).

    HashCore parses Avalon STATS from cgminer STATS JSON with a
    dedicated factory (docs/vendor-coverage-mapping.md §2); the
    distinguishing marks in the payload are the module keys
    "MM ID<n>" (Avalon hash-module entries — stock Antminer STATS
    carries none) or a Type naming the Avalon line. Positive-only:
    no mark, no reclassification.
    """
    if not isinstance(stats, dict):
        stats = {}
    entries = stats.get("stats_entries")
    dicts = [e for e in entries if isinstance(e, dict)] \
        if isinstance(entries, list) else []
    dicts.append(stats)
    for entry in dicts:
        for key in entry:
            if str(key).startswith("MM ID"):
                return True
        if str(entry.get("Type") or "").startswith("Avalon"):
            return True
    return str((summary or {}).get("Type") or "").startswith("Avalon")


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

    # 1) Socket APIs on 4028, whenever the port is open.
    if cand.cgminer_open:
        # 1a) MicroBT Whatsminer dialect (v0.30): a modern Whatsminer
        # does not answer the cgminer envelope at all, and a cgminer
        # device answers this dialect with a STATUS-E error — the
        # fan-pair fingerprint can therefore never mis-claim a
        # cgminer miner (docs/vendor-coverage-mapping.md §1.2).
        try:
            wm_item = WhatsminerClient(
                ip, port=cgminer_port, timeout=timeout).summary_item()
        except Exception:  # noqa: BLE001 — a probe must never raise
            wm_item = {}
        if is_whatsminer_summary(wm_item):
            cand.source = "whatsminer"
            cand.summary = wm_item
            cand.cgminer_ok = True
            cand.model = wm_item.get("Type") or wm_item.get("Model")
            return cand

        # 1b) cgminer RPC — richest data for the cgminer family.
        try:
            client = CgminerClient(ip, port=cgminer_port, timeout=timeout)
            cand.summary = client.summary()
            cand.cgminer_ok = bool(cand.summary)
        except Exception:
            cand.cgminer_ok = False
        if cand.cgminer_ok:
            cand.source = "cgminer"
            cand.model = cand.summary.get("Type") or cand.summary.get("Model")
            # Canaan Avalon refinement (v0.30): Avalon is a cgminer
            # device with its own STATS flavour — one stats fetch
            # (cached for the fetch stage) checks the fingerprint.
            try:
                cand.stats_data = client.stats()
            except Exception:
                cand.stats_data = {}
            if _avalon_fingerprint(cand.stats_data, cand.summary):
                cand.source = "avalon"
            else:
                # LuxOS refinement (v0.33.0, docs/vendor-docs-mapping.md
                # §2.4): a cgminer-claim device whose `version`
                # Description starts "LUXminer" is a LuxOS miner.
                # One extra call, positive-only — stock answers
                # `cgminer …` / `bmminer …` and never matches.
                try:
                    version_resp = client.command("version")
                except Exception:
                    version_resp = {}
                if is_luxos_version(version_resp):
                    cand.source = "luxos"
                elif is_braiins_version(version_resp):
                    # Braiins refinement (v0.36.0,
                    # docs/vendor-oss-mapping.md §1.2): the same
                    # `version` reply carrying "bosminer"/"boser"
                    # (the STATUS Description build string) is a
                    # Braiins OS miner. Same positive-only rule —
                    # no other family carries either substring.
                    cand.source = "braiins"
                elif is_auradine_version(version_resp):
                    # Auradine refinement (v0.38.0,
                    # docs/vendor-docs2-mapping.md §1.2): the
                    # `version` reply carrying "gcminer"/"fluxos"
                    # (GCMiner / FluxOS) is a Teraflux miner.
                    # Case-insensitive — the libraries' own
                    # fixtures carry the markers mixed-case
                    # (D-AU1). "cgminer" is not "gcminer".
                    cand.source = "auradine"
                elif is_sealminer_version(version_resp):
                    # SealMiner refinement (v0.38.0,
                    # docs/vendor-docs2-mapping.md §2.2): the
                    # `version` reply carrying "bdminer"
                    # (BDMiner) is a Bitdeer SealMiner.
                    # Case-insensitive (D-SE1).
                    cand.source = "sealminer"
            return cand

        # 1c) ePIC HTTP JSON (v0.37.0, docs/epic-mapping.md §2):
        # GET :4028/summary, claim on the structural gate
        # (Hostname + Session/"Average MHs" + HBs). An Epic miner
        # answers the two probes above with non-parseable
        # replies, so reaching here is expected for it — and
        # no cgminer-family device can pass the gate, because
        # none of them serves HTTP JSON on 4028.
        try:
            epic_summary = EpicClient(
                ip, port=cgminer_port, timeout=timeout).summary()
        except Exception:  # noqa: BLE001 — a probe must never raise
            epic_summary = {}
        if is_epic_summary(epic_summary):
            cand.source = "epic"
            cand.summary = epic_summary
            cand.cgminer_ok = True
            # The model comes from /capabilities, which the fetch
            # stage reads — the probe claims on the summary alone.
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

        # IceRiver (v0.36.0, docs/vendor-oss-mapping.md §2.4):
        # the console-title gate (one GET — cheap, and it keeps
        # the two POSTs off every router/admin page in the range),
        # then the panel-shape gate. Passwords are tried in family
        # order (iceriver-tagged sets first), then the factory
        # default 12345678; the winner rides the candidate into
        # the fetch stage. The shape gate is decisive — the title
        # alone never claims a host.
        ice = IceRiverClient(ip, port=http_port,
                             timeout=fetch_timeout)
        if ice.has_console_title():
            passwords: list[str] = []
            if explicit_creds:
                # Saved sets only: the implicit single entry (creds
                # is None) carries the stock legacy pair root/root,
                # which is never an IceRiver password — trying it
                # first would "win" on any device whose panel needs
                # no login, and record the wrong password.
                for entry in ordered_creds(cred_list, "iceriver"):
                    pwd = entry.get("password")
                    if pwd and pwd not in passwords:
                        passwords.append(pwd)
            if ICERIVER_DEFAULT_PASSWORD not in passwords:
                passwords.append(ICERIVER_DEFAULT_PASSWORD)
            for pwd in passwords:
                ice.password = pwd
                try:
                    panel = ice.userpanel()
                except IceRiverError:
                    continue
                cand.source = "iceriver"
                cand.iceriver_password = pwd
                cand.model = panel_model(panel)
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
