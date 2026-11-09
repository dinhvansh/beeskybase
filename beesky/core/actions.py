"""Remote action executors — run one command against one miner (v0.6).

A *command* is issued by the viewer on the cloud, claimed by the farm
agent, and executed here against the miner on the farm LAN. Every
executor returns ``(ok, message)`` and **never raises**: a refused or
unreachable action is an honest failure result, not a crash — and a
success is only reported when the miner's own API actually accepted
the request.

Per-source reality (checked against the firmwares' own documents):

``reboot``
  * cgminer — the privileged RPC command ``restart``. Most Antminer
    APIs are provisioned read-only (no ``W:`` grant in ``api-allow``)
    and refuse it with ``STATUS E`` / "Access denied"; that refusal is
    surfaced verbatim as the failure message.
  * dashd (VNish/HashCore) — ``POST /api/v1/system/reboot`` from the
    firmware's OpenAPI doc (``api-doc.json``). Write endpoints need a
    bearer JWT or an ``x-api-key`` header; with only a password the
    executor mints a JWT via ``POST /api/v1/unlock`` (``{"pw": ...}``)
    first.
  * stock Bitmain — ``GET /cgi-bin/reboot.cgi`` behind the usual
    digest auth.

``switch_pool``
  * dashd ONLY, via two documented mechanisms:
      - payload ``{"pool_id": N}`` → ``POST /api/v1/mining/switch-pool``
        activates the already-configured pool slot N;
      - payload ``{"url": ..., "user": ..., "password": ...}`` →
        ``GET /api/v1/settings`` + ``POST /api/v1/settings`` (the
        documented settings write) rewrites pool slot ``pool_id``
        (default 0), then ``/mining/switch-pool`` activates it.
        Reading the settings needs an ``x-api-key`` — per the doc,
        ``GET /settings`` is apikeyAuth-only.
  * cgminer / stock — not supported yet; the executor returns the
    honest failure instead of pretending.

Adding a command type = one handler function + one registry entry.
"""

from __future__ import annotations

from .bitmain import BitmainClient, BitmainError
from .cgminer import CgminerClient, CgminerError
from .dashd import DashdClient, DashdError

COMMAND_TYPES = ("reboot", "switch_pool")

NOT_SUPPORTED = "not supported for this source yet"


def _creds(creds: dict | None) -> dict:
    base = {"user": "root", "password": "root", "api_key": None,
            "token": None, "http_port": 80, "cgminer_port": 4028,
            "timeout": 3.0}
    if creds:
        base.update({k: v for k, v in creds.items() if v is not None})
    return base


# ---------------------------------------------------------------------------
# reboot
# ---------------------------------------------------------------------------

def _reboot_cgminer(ip: str, creds: dict) -> tuple[bool, str]:
    client = CgminerClient(ip, port=int(creds["cgminer_port"]),
                           timeout=float(creds["timeout"]))
    try:
        reply = client.command("restart")
    except CgminerError as exc:
        return False, f"cgminer restart RPC failed: {exc}"
    status = (reply.get("STATUS") or [{}])[0]
    if status.get("STATUS") == "S":
        return True, "cgminer accepted the privileged 'restart' command"
    msg = status.get("Msg") or f"STATUS {status.get('STATUS')}"
    return False, ("cgminer refused 'restart' (its API is usually "
                   f"provisioned read-only): {msg}")


def _dashd_client(ip: str, creds: dict) -> DashdClient:
    return DashdClient(ip, port=int(creds["http_port"]),
                       timeout=float(creds["timeout"]),
                       api_key=creds.get("api_key"),
                       token=creds.get("token"))


def _reboot_dashd(ip: str, creds: dict) -> tuple[bool, str]:
    client = _dashd_client(ip, creds)
    try:
        reply = client.post_json("/system/reboot",
                                 password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd reboot failed: {exc}"
    after = reply.get("after") if isinstance(reply, dict) else None
    if isinstance(after, (int, float)):
        return True, f"dashd accepted reboot (system reboots in {after:g}s)"
    return True, "dashd accepted reboot (POST /system/reboot -> 200)"


def _reboot_stock(ip: str, creds: dict) -> tuple[bool, str]:
    client = BitmainClient(ip, port=int(creds["http_port"]),
                           timeout=float(creds["timeout"]),
                           username=creds.get("user") or "root",
                           password=creds.get("password") or "root")
    try:
        code = client.get_status_code("/cgi-bin/reboot.cgi")
    except BitmainError as exc:
        return False, f"stock reboot failed: {exc}"
    if code == 200:
        return True, "stock firmware accepted reboot (GET /cgi-bin/reboot.cgi -> 200)"
    return False, f"stock reboot refused: GET /cgi-bin/reboot.cgi -> HTTP {code}"


# ---------------------------------------------------------------------------
# switch_pool
# ---------------------------------------------------------------------------

def _switch_pool_dashd(ip: str, payload: dict, creds: dict) -> tuple[bool, str]:
    client = _dashd_client(ip, creds)
    password = creds.get("password")
    raw_id = payload.get("pool_id", 0)
    try:
        pool_id = int(raw_id)
    except (TypeError, ValueError):
        return False, f"switch_pool: pool_id must be an integer, got {raw_id!r}"
    if pool_id < 0:
        return False, f"switch_pool: pool_id must be >= 0, got {pool_id}"

    url = payload.get("url")
    user = payload.get("user")
    if not url and not user:
        # Activate an already-configured pool slot (documented endpoint).
        try:
            client.post_json("/mining/switch-pool", {"pool_id": pool_id},
                             password=password)
        except DashdError as exc:
            return False, f"dashd switch-pool failed: {exc}"
        return True, f"dashd switched the active pool to slot {pool_id}"

    if not url or not user:
        return False, "switch_pool: payload needs both 'url' and 'user'"
    # Rewrite a pool slot via the documented settings write, then activate.
    if not client.api_key:
        return False, ("switch_pool with a new url/user needs to read the "
                       "current settings first, and dashd's GET /settings "
                       "accepts only an x-api-key — the agent has none "
                       "configured (add --api-key)")
    try:
        view = client.get_json("/settings")
    except DashdError as exc:
        return False, f"dashd GET /settings failed: {exc}"
    if not isinstance(view, dict):
        return False, "dashd GET /settings returned a non-object reply"
    # ViewConfig -> InputConfig: pass the documented sections back,
    # changing only miner.pools[pool_id].
    config = {k: view[k] for k in
              ("miner", "network", "password", "regional", "ui") if k in view}
    miner = dict(config.get("miner") or {})
    pools = list(miner.get("pools") or [])
    while len(pools) <= pool_id:
        pools.append(None)
    old = pools[pool_id] if isinstance(pools[pool_id], dict) else {}
    new_pool = {
        "url": str(url),
        "user": str(user),
        "pass": str(payload.get("password", payload.get("pass",
                                                        old.get("pass", "")))),
        "use_tls": bool(payload.get("use_tls", old.get("use_tls", False))),
    }
    pools[pool_id] = new_pool
    miner["pools"] = pools
    config["miner"] = miner
    try:
        client.post_json("/settings", config, password=password)
    except DashdError as exc:
        return False, f"dashd POST /settings failed: {exc}"
    try:
        client.post_json("/mining/switch-pool", {"pool_id": pool_id},
                         password=password)
    except DashdError as exc:
        return False, (f"pool slot {pool_id} was saved via POST /settings "
                       f"but activating it failed: {exc}")
    return True, (f"dashd pool slot {pool_id} set to {url} (user {user}) "
                  "via /settings and activated via /mining/switch-pool")


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

def execute(ip: str, source: str | None, command_type: str,
            payload: dict | None = None,
            creds: dict | None = None) -> tuple[bool, str]:
    """Run one command; returns (ok, human-readable result). Never raises."""
    cfg = _creds(creds)
    payload = payload or {}
    try:
        if command_type == "reboot":
            if source == "cgminer":
                return _reboot_cgminer(ip, cfg)
            if source == "vnish":
                return _reboot_dashd(ip, cfg)
            if source == "stock":
                return _reboot_stock(ip, cfg)
            return False, f"reboot: unknown miner source {source!r}"
        if command_type == "switch_pool":
            if source == "vnish":
                return _switch_pool_dashd(ip, payload, cfg)
            return False, (f"switch_pool is {NOT_SUPPORTED} "
                           f"(source: {source or 'unknown'})")
        return False, f"unknown command type {command_type!r}"
    except Exception as exc:  # noqa: BLE001 — executors must never raise
        return False, f"{command_type} executor error: {exc}"
