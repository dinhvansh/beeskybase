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
  * avalon (v0.30) — the same cgminer ``restart`` RPC; Avalon is the
    cgminer wire with a Canaan claim (docs/vendor-coverage-mapping.md
    §2).
  * dashd (VNish/HashCore) — ``POST /api/v1/system/reboot`` from the
    firmware's OpenAPI doc (``api-doc.json``). Write endpoints need a
    bearer JWT or an ``x-api-key`` header; with only a password the
    executor mints a JWT via ``POST /api/v1/unlock`` (``{"pw": ...}``)
    first.
  * stock Bitmain — ``GET /cgi-bin/reboot.cgi`` behind the usual
    digest auth.
  * whatsminer (v0.33.0 — G-W1 CLOSED, docs/vendor-docs-mapping.md
    §1): privileged calls ride the MicroBT token session minted by
    ``{"cmd": "get_token"}``; the token computation is the manuals'
    md5crypt scheme (``key`` then ``sign``), verified against the
    manuals' worked example. ``reboot`` sends ``{"token", "cmd":
    "reboot"}`` (control-board reboot, §3.8); the password is the
    winning whatsminer set's, else the factory default "admin".
  * luxos (v0.33.0, docs/vendor-docs-mapping.md §2): ``reboot``
    sends the parameter-less ``rebootdevice`` command (Luxor's own
    CLI usage); no session is documented for it.

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
  * whatsminer (v0.33.0, mapping §1.5): ``update_pools`` (§3.1)
    rewrites the pool lines and switches immediately — there is
    NO activate-a-slot form in the manual, so the payload MUST
    carry url+user (pool_id selects which of pool1/2/3 the new
    values land in; the other slots are re-sent unchanged — see
    the mapping's hardware caveat).
  * cgminer / stock — not supported yet; the executor returns the
    honest failure instead of pretending.

``restart_mining`` / ``pause_mining`` / ``resume_mining`` /
``find_miner`` — beyond dashd (v0.29 tail):
  * whatsminer (v0.33.0, mapping §1.5): ``restart_btminer``
    (§3.2, mining-process restart), ``power_off`` / ``power_on``
    (§3.3/§3.4, hashboard power), ``set_led`` with
    ``param: "auto"`` (§3.5, find-miner) — all token-authenticated.
  * luxos (v0.33.0, mapping §2.6): pause/resume are ``curtail``
    ``sleep`` / ``wakeup`` behind a logon/logoff session. A
    sleeping LuxOS rig can ONLY be woken by ``wakeup`` — the
    state survives a reboot — and the pause message says so.
    LuxOS has no ``restart_mining`` / ``find_miner`` in this
    build (no documented equivalent wired).

The v0.29 VNish tail (docs/vnish-ops-mapping.md — every contract
below is the api-doc's own; presentation follows HashCore's task
list). All dashd-only — other families get the honest
``NOT_SUPPORTED`` failure, never a pretend success:

``pause_mining`` / ``resume_mining`` / ``restart_mining``
  Bodyless ``POST /mining/pause`` / ``/resume`` / ``/restart``.
  ``restart_mining`` is the mining-process restart HashCore lists
  separately from Reboot (v0.26 had merged them for lack of this
  code path; the device reboot stays ``reboot``).

``find_miner``
  Bodyless ``POST /locate-miner`` (the doc's non-deprecated
  endpoint; ``/find-miner`` is marked deprecated). No on/off or
  duration parameter exists in the contract — the reply's
  ``is_enabled`` state is reported verbatim.

``throttle``
  ``POST /mining/throttle`` with ``{"percent": N}`` (doc range
  20–100 — HashCore's "Power level"). The reply's
  SaveConfigResult restart/reboot flags surface in the message.

``reset_autotune_all`` / ``reset_autotune_current``
  ``POST /autotune/reset-all {"restart": bool}``; for "current",
  ``GET /perf-summary`` (no auth in the doc) names the current
  preset, then ``POST /autotune/reset {"presets": [name],
  "restart": bool}``.

``configure_api_key``
  ``POST /apikeys {"key", "description"}`` (add; the reply's
  inserted/updated/nochanges status surfaces) or
  ``POST /apikeys/delete {"key"}`` (remove). Keys are exactly
  32 characters per the doc's schema.

``set_preset``
  The settings read-modify-write the switch_pool url-form already
  proves: ``GET /settings`` (x-api-key only) → set
  ``miner.overclock.preset`` → ``POST /settings``.

``change_password``
  ``POST /settings {"password": {"current": ..., "pw": ...}}``
  (the doc's PasswordChange section). ``current`` is the password
  the winning credential set authenticated with; an api-key-only
  win cannot run it and says so.

Adding a command type = one handler function + one registry entry.
"""

from __future__ import annotations

from .auradine import DEFAULT_PASSWORD as AURADINE_DEFAULT_PASSWORD
from .auradine import DEFAULT_USERNAME as AURADINE_DEFAULT_USERNAME
from .auradine import AuradineClient, AuradineError
from .bitmain import BitmainClient, BitmainError
from .braiins import BraiinsClient, BraiinsError
from .cgminer import CgminerClient, CgminerError
from .dashd import DashdClient, DashdError
from .epic import DEFAULT_PASSWORD as EPIC_DEFAULT_PASSWORD
from .epic import EpicClient, EpicError
from .iceriver import (DEFAULT_PASSWORD as ICERIVER_DEFAULT_PASSWORD,
                       IceRiverClient, IceRiverError)
from .luxos import LuxosClient, LuxosError
from .sealminer import DEFAULT_PASSWORD as SEALMINER_DEFAULT_PASSWORD
from .sealminer import DEFAULT_USERNAME as SEALMINER_DEFAULT_USERNAME
from .sealminer import MINING_MODES as SEALMINER_MINING_MODES
from .sealminer import SealMinerClient, SealMinerError
from .whatsminer import (DEFAULT_PASSWORD as WM_DEFAULT_PASSWORD,
                         WhatsminerClient, WhatsminerError)

COMMAND_TYPES = ("reboot", "switch_pool",
                 "pause_mining", "resume_mining", "restart_mining",
                 "find_miner", "throttle",
                 "reset_autotune_all", "reset_autotune_current",
                 "configure_api_key", "set_preset", "change_password",
                 # v0.37.0 ePIC-only controls (docs/epic-mapping.md §4)
                 "set_power_target", "set_shutdown_temp",
                 "set_fan_speed", "tune",
                 # v0.38.0 SealMiner-only control
                 # (docs/vendor-docs2-mapping.md §2.4): the RPC
                 # ascset workmode form.
                 "set_mining_mode")

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


def _wm_password(raw_creds: dict | None) -> tuple[str, bool]:
    """The password a Whatsminer token is computed from.

    The winning whatsminer-tagged set's password when one was
    supplied; otherwise the manuals' factory default "admin"
    (mapping §1.5). The second value says the default was used,
    so the message can tell the operator to save a set when
    their fleet changed the admin password. NOTE: this reads the
    RAW creds dict, not the merged cfg — the merge fills
    "root" when nothing was supplied, and "root" is never a
    Whatsminer password.
    """
    password = (raw_creds or {}).get("password") or ""
    if password:
        return password, False
    return WM_DEFAULT_PASSWORD, True


def _reboot_whatsminer(ip: str, cfg: dict,
                       raw_creds: dict | None) -> tuple[bool, str]:
    password, used_default = _wm_password(raw_creds)
    client = WhatsminerClient(ip, port=int(cfg["cgminer_port"]),
                              timeout=float(cfg["timeout"]))
    try:
        client.reboot_board(password)
    except WhatsminerError as exc:
        return False, f"whatsminer reboot failed: {exc}"
    note = (" (default admin password — save a whatsminer "
            "credential set if this fleet changed it)"
            if used_default else "")
    return True, ("whatsminer accepted reboot "
                  "({\"cmd\": \"reboot\"} -> Code 131)" + note)


def _reboot_luxos(ip: str, cfg: dict) -> tuple[bool, str]:
    client = LuxosClient(ip, port=int(cfg["cgminer_port"]),
                         timeout=float(cfg["timeout"]))
    try:
        client.rebootdevice()
    except LuxosError as exc:
        return False, f"luxos reboot failed: {exc}"
    return True, "luxos accepted reboot (rebootdevice -> STATUS S)"


# ---------------------------------------------------------------------------
# ePIC family actions (v0.37.0, docs/epic-mapping.md §4)
# ---------------------------------------------------------------------------

def _epic_password(raw_creds: dict | None) -> tuple[str, bool]:
    """The password an ePIC write authenticates with.

    The winning epic-tagged set's password when one was supplied;
    otherwise the README's factory default "letmein" (mapping
    §4, D-E5 — documented for ALL miners, not a guess). The
    second value says the default was used, so the message can
    tell the operator to save a set when their fleet changed
    the password. NOTE: this reads the RAW creds dict, not the
    merged cfg — the merge fills "root" when nothing was
    supplied, and "root" is never an ePIC password.
    """
    password = (raw_creds or {}).get("password") or ""
    if password:
        return password, False
    return EPIC_DEFAULT_PASSWORD, True


def _epic_client(ip: str, cfg: dict,
                 raw_creds: dict | None) -> EpicClient:
    password, _used = _epic_password(raw_creds)
    return EpicClient(ip, port=int(cfg["cgminer_port"]),
                      password=password,
                      timeout=float(cfg["timeout"]))


def _epic_simple(ip: str, cfg: dict, raw_creds: dict | None,
                 method: str, label: str,
                 *args) -> tuple[bool, str]:
    """One ePIC POST call, honest result."""
    password, used_default = _epic_password(raw_creds)
    client = _epic_client(ip, cfg, raw_creds)
    try:
        getattr(client, method)(*args)
    except EpicError as exc:
        return False, f"epic {label} failed: {exc}"
    note = (" (default letmein password — save an epic "
            "credential set if this fleet changed it)"
            if used_default else "")
    return True, f"epic accepted {label}" + note


def _reboot_epic(ip: str, cfg: dict,
                 raw_creds: dict | None) -> tuple[bool, str]:
    return _epic_simple(ip, cfg, raw_creds, "reboot",
                        "reboot (/reboot, delay 0)")


def _switch_pool_epic(ip: str, payload: dict, cfg: dict,
                      raw_creds: dict | None) -> tuple[bool, str]:
    """Rewrite pool slot pool_id via POST /coin (mapping §4).

    The dashboard-faithful body: the current /summary is read
    first (coin + existing configs + unique_id), slot pool_id
    is replaced, the rest re-sent unchanged. A bare pool_id
    has no meaning here — the payload must carry the new pool.
    """
    url = payload.get("url")
    user = payload.get("user")
    if not url or not user:
        return False, ("switch_pool on epic needs 'url' and "
                       "'user' in the payload — /coin always "
                       "rewrites the pool configs, there is no "
                       "activate-a-configured-slot form")
    try:
        pool_id = int(payload.get("pool_id", 0))
    except (TypeError, ValueError):
        return False, (f"switch_pool: pool_id must be an integer, "
                       f"got {payload.get('pool_id')!r}")
    if pool_id not in (0, 1, 2):
        return False, (f"switch_pool: epic has 3 pool slots, "
                       f"pool_id must be 0-2, got {pool_id}")
    client = _epic_client(ip, cfg, raw_creds)
    try:
        summary = client.summary()
    except EpicError as exc:
        return False, f"epic switch_pool failed: {exc}"
    mining = summary.get("Mining") or {}
    coin = mining.get("Coin") if isinstance(mining, dict) else None
    if not isinstance(coin, str) or not coin:
        return False, ("epic switch_pool failed: the miner's "
                       "current coin is unknown (no Mining.Coin "
                       "in /summary)")
    configs = summary.get("StratumConfigs")
    norm = []
    if isinstance(configs, list):
        for entry in configs:
            if isinstance(entry, dict) and entry.get("pool"):
                norm.append({
                    "pool": str(entry.get("pool")),
                    "login": str(entry.get("login") or ""),
                    "password": str(entry.get("password") or ""),
                })
    while len(norm) <= pool_id:
        norm.append({"pool": "", "login": "", "password": ""})
    norm[pool_id] = {"pool": str(url), "login": str(user),
                     "password": str(payload.get("password", ""))}
    misc = summary.get("Misc") or {}
    unique_id = bool(misc.get("Append Unique Id To Worker")) \
        if isinstance(misc, dict) else False
    try:
        client.set_coin(coin, norm, unique_id=unique_id)
    except EpicError as exc:
        return False, f"epic switch_pool failed: {exc}"
    _password, used_default = _epic_password(raw_creds)
    note = (" (default letmein password — save an epic "
            "credential set if this fleet changed it)"
            if used_default else "")
    return True, (f"epic pool slot {pool_id} set to {url} "
                  f"(coin {coin})" + note)


def _set_preset_epic(ip: str, payload: dict, cfg: dict,
                     raw_creds: dict | None) -> tuple[bool, str]:
    """POST /mode (mapping §4): preset from /capabilities,
    optional power_target in watts."""
    preset = payload.get("preset")
    if not isinstance(preset, str) or not preset:
        return False, "set_preset on epic needs 'preset' in the payload"
    power = payload.get("power_target", payload.get("power"))
    try:
        power_int = int(power) if power is not None else None
    except (TypeError, ValueError):
        return False, (f"set_preset: power_target must be an integer, "
                       f"got {power!r}")
    return _epic_simple(ip, cfg, raw_creds, "set_mode",
                        f"set_preset ({preset}"
                        f"{f' @ {power_int}W' if power_int else ''})",
                        preset, power_int)


def _change_password_epic(ip: str, payload: dict, cfg: dict,
                          raw_creds: dict | None) -> tuple[bool, str]:
    """POST /password (mapping §4): param is the new password,
    "password" the old one — the old one is the winning set's
    (or the documented default), exactly like the dashd
    handler's current-password rule."""
    new_password = payload.get("new_password")
    if not isinstance(new_password, str) or not new_password:
        return False, ("change_password: payload needs a "
                       "non-empty 'new_password'")
    return _epic_simple(ip, cfg, raw_creds, "set_password",
                        "change_password (/password)",
                        new_password)


# ---------------------------------------------------------------------------
# whatsminer / luxos family actions (v0.33.0)
# ---------------------------------------------------------------------------

def _wm_simple(ip: str, cfg: dict, raw_creds: dict | None,
               method: str, label: str) -> tuple[bool, str]:
    """One token-authenticated Whatsminer call, honest result."""
    password, used_default = _wm_password(raw_creds)
    client = WhatsminerClient(ip, port=int(cfg["cgminer_port"]),
                              timeout=float(cfg["timeout"]))
    try:
        getattr(client, method)(password)
    except WhatsminerError as exc:
        return False, f"whatsminer {label} failed: {exc}"
    note = (" (default admin password — save a whatsminer "
            "credential set if this fleet changed it)"
            if used_default else "")
    return True, f"whatsminer accepted {label}" + note


def _switch_pool_whatsminer(ip: str, payload: dict, cfg: dict,
                            raw_creds: dict | None) -> tuple[bool, str]:
    # update_pools always rewrites the pool lines (mapping §1.5):
    # a bare pool_id has no meaning here — the payload must carry
    # the new pool. pool_id selects the slot (default 0).
    url = payload.get("url")
    user = payload.get("user")
    if not url or not user:
        return False, ("switch_pool on whatsminer needs 'url' and "
                       "'user' in the payload — the manual's "
                       "update_pools always rewrites the pool lines, "
                       "there is no activate-a-configured-slot form")
    try:
        pool_id = int(payload.get("pool_id", 0))
    except (TypeError, ValueError):
        return False, (f"switch_pool: pool_id must be an integer, "
                       f"got {payload.get('pool_id')!r}")
    if pool_id not in (0, 1, 2):
        return False, (f"switch_pool: whatsminer has 3 pool slots, "
                       f"pool_id must be 0-2, got {pool_id}")
    password, used_default = _wm_password(raw_creds)
    client = WhatsminerClient(ip, port=int(cfg["cgminer_port"]),
                              timeout=float(cfg["timeout"]))
    pools = [{"url": "", "worker": "", "password": ""} for _ in range(3)]
    pools[pool_id] = {"url": str(url), "worker": str(user),
                      "password": str(payload.get("password", ""))}
    try:
        client.update_pools(password, pools)
    except WhatsminerError as exc:
        return False, f"whatsminer switch_pool failed: {exc}"
    note = (" (default admin password — save a whatsminer "
            "credential set if this fleet changed it)"
            if used_default else "")
    return True, (f"whatsminer pool slot {pool_id} set to {url} "
                  f"(user {user}) via update_pools" + note)


def _curtail_luxos(ip: str, cfg: dict, action: str,
                   label: str) -> tuple[bool, str]:
    client = LuxosClient(ip, port=int(cfg["cgminer_port"]),
                         timeout=float(cfg["timeout"]))
    try:
        client.curtail(action)
    except LuxosError as exc:
        return False, f"luxos {label} failed: {exc}"
    tail = ""
    if action == "sleep":
        tail = (" (a sleeping LuxOS rig wakes ONLY via resume_mining "
                "— the curtailment state survives a reboot)")
    return True, f"luxos accepted {label} (curtail {action})" + tail


# ---------------------------------------------------------------------------
# braiins / iceriver family actions (v0.36.0)
# ---------------------------------------------------------------------------

def _braiins_simple(ip: str, cfg: dict, method: str,
                    label: str) -> tuple[bool, str]:
    """One Braiins 4028 call (pause/resume — mapping §1.4)."""
    client = BraiinsClient(ip, port=int(cfg["cgminer_port"]),
                           timeout=float(cfg["timeout"]))
    try:
        getattr(client, method)()
    except BraiinsError as exc:
        return False, f"braiins {label} failed: {exc}"
    return True, f"braiins accepted {label}"


def _find_miner_iceriver(ip: str, cfg: dict,
                         raw_creds: dict | None) -> tuple[bool, str]:
    """IceRiver locate (pyasic's locate(True) — mapping §2.5).

    The password is the winning iceriver-tagged set's when one was
    supplied, else the factory default — the same rule as the
    probe (discover.py); the API needs no token, so a wrong
    password costs nothing but a failed login attempt.
    """
    password = None
    if raw_creds:
        password = raw_creds.get("password")
    client = IceRiverClient(
        ip, port=int(cfg["http_port"]), timeout=float(cfg["timeout"]),
        password=password or ICERIVER_DEFAULT_PASSWORD)
    try:
        client.locate(True)
    except IceRiverError as exc:
        return False, f"iceriver find_miner failed: {exc}"
    return True, "iceriver accepted find_miner (locate on)"


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
# VNish ops tail (v0.29) — dashd-only handlers; contracts and the
# shipped/gap reasoning live in docs/vnish-ops-mapping.md
# ---------------------------------------------------------------------------

def _save_flags_note(reply) -> str:
    """SaveConfigResult's restart/reboot flags, as a message tail."""
    if not isinstance(reply, dict):
        return ""
    notes = []
    if reply.get("restart_required"):
        notes.append("the device says a mining restart is required "
                     "to apply it")
    if reply.get("reboot_required"):
        notes.append("the device says a reboot is required to apply it")
    return (" (" + "; ".join(notes) + ")") if notes else ""


def _bodyless_dashd(ip: str, creds: dict, path: str,
                    what: str) -> tuple[bool, str]:
    client = _dashd_client(ip, creds)
    try:
        client.post_json(path, password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd {what} failed: {exc}"
    return True, f"dashd accepted {what} (POST {path} -> 200)"


def _find_miner_dashd(ip: str, payload: dict,
                      creds: dict) -> tuple[bool, str]:
    client = _dashd_client(ip, creds)
    try:
        reply = client.post_json("/locate-miner",
                                 password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd find-miner failed: {exc}"
    state = reply.get("is_enabled") if isinstance(reply, dict) else None
    if state is True:
        return True, "dashd locate-miner is ON (the device reports " \
                     "is_enabled=true)"
    if state is False:
        return True, "dashd locate-miner is OFF (the device reports " \
                     "is_enabled=false)"
    return True, "dashd accepted locate-miner (POST /locate-miner " \
                 "-> 200, no state in the reply)"


def _throttle_dashd(ip: str, payload: dict, creds: dict) -> tuple[bool, str]:
    percent = payload.get("percent")
    if isinstance(percent, bool) or not isinstance(percent, int):
        return False, f"throttle: percent must be an integer, " \
                      f"got {percent!r}"
    if not 20 <= percent <= 100:
        return False, f"throttle: percent must be within the " \
                      f"documented 20..100 range, got {percent}"
    client = _dashd_client(ip, creds)
    try:
        reply = client.post_json("/mining/throttle",
                                 {"percent": percent},
                                 password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd throttle failed: {exc}"
    return True, (f"dashd throttle set to {percent}%"
                  f"{_save_flags_note(reply)}")


def _reset_autotune_all_dashd(ip: str, payload: dict,
                              creds: dict) -> tuple[bool, str]:
    restart = bool(payload.get("restart", True))
    client = _dashd_client(ip, creds)
    try:
        client.post_json("/autotune/reset-all", {"restart": restart},
                         password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd autotune reset-all failed: {exc}"
    return True, ("dashd reset ALL autotune profiles "
                  f"(restart={str(restart).lower()})")


def _reset_autotune_current_dashd(ip: str, payload: dict,
                                  creds: dict) -> tuple[bool, str]:
    restart = bool(payload.get("restart", True))
    client = _dashd_client(ip, creds)
    try:
        perf = client.get_json("/perf-summary")
    except DashdError as exc:
        return False, f"dashd GET /perf-summary failed: {exc}"
    current = perf.get("current_preset") if isinstance(perf, dict) \
        else None
    name = current.get("name") if isinstance(current, dict) else None
    if not name:
        return False, ("dashd reports no current autotune preset "
                       "(GET /perf-summary) — nothing to reset")
    try:
        client.post_json("/autotune/reset",
                         {"presets": [str(name)], "restart": restart},
                         password=creds.get("password"))
    except DashdError as exc:
        return False, f"dashd autotune reset failed: {exc}"
    return True, (f"dashd reset the current autotune profile "
                  f"{name!r} (restart={str(restart).lower()})")


def _configure_api_key_dashd(ip: str, payload: dict,
                             creds: dict) -> tuple[bool, str]:
    operation = payload.get("operation", "add")
    if operation not in ("add", "remove"):
        return False, f"configure_api_key: operation must be " \
                      f"'add' or 'remove', got {operation!r}"
    key = payload.get("key")
    if not isinstance(key, str) or len(key) != 32:
        return False, ("configure_api_key: key must be a string of "
                       "exactly 32 characters (the api-doc schema)")
    client = _dashd_client(ip, creds)
    password = creds.get("password")
    if operation == "remove":
        try:
            client.post_json("/apikeys/delete", {"key": key},
                             password=password)
        except DashdError as exc:
            return False, f"dashd apikey delete failed: {exc}"
        return True, "dashd removed the API key (POST /apikeys/delete)"
    description = payload.get("description")
    body = {"key": key,
            "description": str(description) if description else ""}
    try:
        reply = client.post_json("/apikeys", body, password=password)
    except DashdError as exc:
        return False, f"dashd apikey add failed: {exc}"
    status = reply.get("status") if isinstance(reply, dict) else None
    note = f" — device reports {status!r}" if status else ""
    return True, f"dashd saved the API key (POST /apikeys){note}"


def _set_preset_dashd(ip: str, payload: dict,
                      creds: dict) -> tuple[bool, str]:
    preset = payload.get("preset")
    if not isinstance(preset, str) or not preset.strip():
        return False, "set_preset: payload needs a non-empty " \
                      "\"preset\" name"
    preset = preset.strip()
    client = _dashd_client(ip, creds)
    password = creds.get("password")
    # Same proven path as switch_pool's url form: reading the
    # settings is x-api-key-only per the api-doc.
    if not client.api_key:
        return False, ("set_preset needs to read the current "
                       "settings first, and dashd's GET /settings "
                       "accepts only an x-api-key — the agent has "
                       "none configured (add --api-key)")
    try:
        view = client.get_json("/settings")
    except DashdError as exc:
        return False, f"dashd GET /settings failed: {exc}"
    if not isinstance(view, dict):
        return False, "dashd GET /settings returned a non-object reply"
    config = {k: view[k] for k in
              ("miner", "network", "password", "regional", "ui")
              if k in view}
    miner = dict(config.get("miner") or {})
    overclock = dict(miner.get("overclock") or {})
    overclock["preset"] = preset
    miner["overclock"] = overclock
    config["miner"] = miner
    try:
        reply = client.post_json("/settings", config,
                                 password=password)
    except DashdError as exc:
        return False, f"dashd POST /settings failed: {exc}"
    return True, (f"dashd preset set to {preset!r} via /settings"
                  f"{_save_flags_note(reply)}")


def _change_password_dashd(ip: str, payload: dict,
                           creds: dict) -> tuple[bool, str]:
    new_password = payload.get("new_password")
    if not isinstance(new_password, str) or not new_password:
        return False, "change_password: payload needs a non-empty " \
                      "\"new_password\""
    current = creds.get("password")
    if not current:
        return False, ("change_password needs the CURRENT device "
                       "password (the api-doc's PasswordChange "
                       "\"current\" field) — the winning credential "
                       "set authenticated with an API key only")
    client = _dashd_client(ip, creds)
    body = {"password": {"current": current, "pw": new_password}}
    try:
        reply = client.post_json("/settings", body, password=current)
    except DashdError as exc:
        return False, f"dashd password change failed: {exc}"
    return True, ("dashd accepted the password change "
                  f"(POST /settings){_save_flags_note(reply)}")


_DASHD_ONLY = {
    "pause_mining": lambda ip, p, c: _bodyless_dashd(
        ip, c, "/mining/pause", "mining pause"),
    "resume_mining": lambda ip, p, c: _bodyless_dashd(
        ip, c, "/mining/resume", "mining resume"),
    "restart_mining": lambda ip, p, c: _bodyless_dashd(
        ip, c, "/mining/restart", "mining restart"),
    "find_miner": _find_miner_dashd,
    "throttle": _throttle_dashd,
    "reset_autotune_all": _reset_autotune_all_dashd,
    "reset_autotune_current": _reset_autotune_current_dashd,
    "configure_api_key": _configure_api_key_dashd,
    "set_preset": _set_preset_dashd,
    "change_password": _change_password_dashd,
}


def _epic_int(payload: dict, *keys: str) -> int | None:
    """First present payload value as int, or None (a missing
    value must fail honestly — never a silent 0)."""
    for key in keys:
        if key in payload and payload[key] is not None:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                return None
    return None


def _set_power_epic(ip: str, payload: dict, cfg: dict,
                    raw_creds: dict | None) -> tuple[bool, str]:
    watts = _epic_int(payload, "watts", "power_target")
    if watts is None:
        return False, ("set_power_target on epic needs 'watts' "
                       "(or 'power_target') in the payload")
    return _epic_simple(ip, cfg, raw_creds, "set_power",
                        "set_power_target (/power)", watts)


def _set_shutdown_epic(ip: str, payload: dict, cfg: dict,
                       raw_creds: dict | None) -> tuple[bool, str]:
    temp = _epic_int(payload, "temp_c", "shutdowntemp")
    if temp is None:
        return False, ("set_shutdown_temp on epic needs 'temp_c' "
                       "(or 'shutdowntemp') in the payload")
    return _epic_simple(ip, cfg, raw_creds, "set_shutdown_temp",
                        "set_shutdown_temp (/shutdowntemp)", temp)


def _set_fan_epic(ip: str, payload: dict, cfg: dict,
                  raw_creds: dict | None) -> tuple[bool, str]:
    speed = _epic_int(payload, "speed", "fan_speed")
    if speed is None:
        return False, ("set_fan_speed on epic needs 'speed' "
                       "(1-100) in the payload")
    return _epic_simple(ip, cfg, raw_creds, "set_fan_speed",
                        "set_fan_speed (/fanspeed)", speed)


def _tune_epic(ip: str, payload: dict, cfg: dict,
               raw_creds: dict | None) -> tuple[bool, str]:
    clock = _epic_int(payload, "clock_mhz", "clock")
    voltage = _epic_int(payload, "voltage_mv", "voltage")
    if clock is None or voltage is None:
        return False, ("tune on epic needs 'clock_mhz' and "
                       "'voltage_mv' in the payload")
    return _epic_simple(ip, cfg, raw_creds, "tune", "tune (/tune)",
                        clock, voltage)


# ---------------------------------------------------------------------------
# Auradine family actions (v0.38.0, docs/vendor-docs2-mapping.md §1.4)
# ---------------------------------------------------------------------------

def _auradine_auth(raw_creds: dict | None) -> tuple[str, str, bool]:
    """The (username, password, used_default) a web write
    authenticates with.

    The winning auradine-tagged set's pair when one was
    supplied; otherwise the factory default admin/admin
    (mapping §1.4 — documented for the fleet, not a guess).
    NOTE: this reads the RAW creds dict, not the merged cfg
    — the merge fills "root" when nothing was supplied, and
    "root" is never an Auradine login.
    """
    raw = raw_creds or {}
    password = raw.get("password") or ""
    if password:
        return (raw.get("user") or AURADINE_DEFAULT_USERNAME,
                password, False)
    return AURADINE_DEFAULT_USERNAME, AURADINE_DEFAULT_PASSWORD, True


def _auradine_client(ip: str, cfg: dict,
                     raw_creds: dict | None) -> AuradineClient:
    username, password, _used = _auradine_auth(raw_creds)
    return AuradineClient(ip, port=int(cfg["cgminer_port"]),
                          username=username, password=password,
                          timeout=float(cfg["timeout"]))


def _auradine_simple(ip: str, cfg: dict, raw_creds: dict | None,
                     method: str, label: str,
                     *args) -> tuple[bool, str]:
    """One Auradine web call, honest result."""
    _username, _password, used_default = _auradine_auth(raw_creds)
    client = _auradine_client(ip, cfg, raw_creds)
    try:
        getattr(client, method)(*args)
    except AuradineError as exc:
        return False, f"auradine {label} failed: {exc}"
    note = (" (default admin/admin credentials — save an auradine "
            "credential set if this fleet changed them)"
            if used_default else "")
    return True, f"auradine accepted {label}" + note


def _reboot_auradine(ip: str, cfg: dict,
                     raw_creds: dict | None) -> tuple[bool, str]:
    return _auradine_simple(ip, cfg, raw_creds, "reboot",
                            "reboot (web restart)")


def _auradine_current_pools(client: AuradineClient) -> list[dict]:
    """The current RPC pools as {url, user, password} dicts —
    the password is unknowable from RPC (cgminer does not
    return it), so an unchanged slot re-sends "" and the
    client turns it into "x" (asic-rs build rule, mapping
    §1.4). A failed pools read yields an empty list (the
    switch then writes the new pool alone)."""
    try:
        resp = client._cg.pools()
    except Exception:  # noqa: BLE001 — enrichment must not sink the task
        return []
    pools = []
    raw = resp.get("POOLS") if isinstance(resp, dict) else None
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict) and entry.get("URL"):
                pools.append({
                    "url": str(entry.get("URL")),
                    "user": str(entry.get("User") or ""),
                    "password": str(entry.get("Passwd") or ""),
                })
    return pools


def _switch_pool_auradine(ip: str, payload: dict, cfg: dict,
                          raw_creds: dict | None) -> tuple[bool, str]:
    """Rewrite pool slot pool_id via POST updatepools
    (mapping §1.4): the current RPC pools are read first,
    slot pool_id is replaced, the rest re-sent unchanged
    (empty URLs dropped, asic-rs's own parse rule)."""
    url = payload.get("url")
    user = payload.get("user")
    if not url or not user:
        return False, ("switch_pool on auradine needs 'url' and "
                       "'user' in the payload — updatepools always "
                       "rewrites the pool list, there is no "
                       "activate-a-configured-slot form")
    try:
        pool_id = int(payload.get("pool_id", 0))
    except (TypeError, ValueError):
        return False, (f"switch_pool: pool_id must be an integer, "
                       f"got {payload.get('pool_id')!r}")
    if pool_id < 0 or pool_id > 2:
        return False, (f"switch_pool: auradine has 3 pool slots, "
                       f"pool_id must be 0-2, got {pool_id}")
    client = _auradine_client(ip, cfg, raw_creds)
    norm = _auradine_current_pools(client)
    while len(norm) <= pool_id:
        norm.append({"url": "", "user": "", "password": ""})
    norm[pool_id] = {"url": str(url), "user": str(user),
                     "password": str(payload.get("password", ""))}
    norm = [entry for entry in norm if entry.get("url")]
    try:
        client.set_pools(norm)
    except AuradineError as exc:
        return False, f"auradine switch_pool failed: {exc}"
    _u, _p, used_default = _auradine_auth(raw_creds)
    note = (" (default admin/admin credentials — save an auradine "
            "credential set if this fleet changed them)"
            if used_default else "")
    return True, (f"auradine pool slot {pool_id} set to {url} "
                  f"(user {user}) via updatepools" + note)


def _set_power_auradine(ip: str, payload: dict, cfg: dict,
                        raw_creds: dict | None) -> tuple[bool, str]:
    watts = _epic_int(payload, "watts", "power_target")
    if watts is None:
        return False, ("set_power_target on auradine needs 'watts' "
                       "(or 'power_target') in the payload")
    return _auradine_simple(ip, cfg, raw_creds, "set_power_limit",
                            "set_power_target (web mode custom/power)",
                            watts)


# ---------------------------------------------------------------------------
# SealMiner family actions (v0.38.0, docs/vendor-docs2-mapping.md §2.4)
# ---------------------------------------------------------------------------

def _sealminer_auth(raw_creds: dict | None) -> tuple[str, str, bool]:
    """The (username, password, used_default) a web/RPC write
    authenticates with — the winning sealminer-tagged set's
    pair when supplied, else the factory default seal/seal
    (mapping §2.4, D-SE2). Reads the RAW creds dict (the
    merge fills "root", which is never a SealMiner login)."""
    raw = raw_creds or {}
    password = raw.get("password") or ""
    if password:
        return (raw.get("user") or SEALMINER_DEFAULT_USERNAME,
                password, False)
    return SEALMINER_DEFAULT_USERNAME, SEALMINER_DEFAULT_PASSWORD, True


def _sealminer_client(ip: str, cfg: dict,
                       raw_creds: dict | None) -> SealMinerClient:
    username, password, _used = _sealminer_auth(raw_creds)
    # The web CGI lives on the HTTP port (80 on a real miner);
    # cfg["http_port"] is the job's HTTP port, which the tests
    # override to the mock's port.
    return SealMinerClient(ip, port=int(cfg["cgminer_port"]),
                           web_port=int(cfg["http_port"]),
                           username=username, password=password,
                           timeout=float(cfg["timeout"]))


def _sealminer_simple(ip: str, cfg: dict, raw_creds: dict | None,
                      method: str, label: str,
                      *args) -> tuple[bool, str]:
    """One SealMiner call, honest result."""
    _username, _password, used_default = _sealminer_auth(raw_creds)
    client = _sealminer_client(ip, cfg, raw_creds)
    try:
        getattr(client, method)(*args)
    except SealMinerError as exc:
        return False, f"sealminer {label} failed: {exc}"
    note = (" (default seal/seal credentials — save a sealminer "
            "credential set if this fleet changed them)"
            if used_default else "")
    return True, f"sealminer accepted {label}" + note


def _reboot_sealminer(ip: str, cfg: dict,
                      raw_creds: dict | None) -> tuple[bool, str]:
    return _sealminer_simple(ip, cfg, raw_creds, "reboot",
                             "reboot (web reboot.php)")


def _resume_sealminer(ip: str, payload: dict, cfg: dict,
                      raw_creds: dict | None) -> tuple[bool, str]:
    """Resume: the client's own already-running guard (asic-rs
    Resume) is reported as a success without a restart."""
    client = _sealminer_client(ip, cfg, raw_creds)
    try:
        reply = client.resume()
    except SealMinerError as exc:
        return False, f"sealminer resume_mining failed: {exc}"
    if isinstance(reply, dict) and reply.get("already_running"):
        return True, ("sealminer already hashing (PM State Running "
                      "— no restart sent)")
    return True, "sealminer accepted resume_mining (RPC restart)"


def _sealminer_current_pools(client: SealMinerClient) -> list[dict]:
    """The current RPC pools as {url, user, password} dicts
    (same unknowable-password caveat as Auradine — the
    client sends "" for an unchanged slot)."""
    try:
        resp = client._cg.pools()
    except Exception:  # noqa: BLE001 — enrichment must not sink the task
        return []
    pools = []
    raw = resp.get("POOLS") if isinstance(resp, dict) else None
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict) and entry.get("URL"):
                pools.append({
                    "url": str(entry.get("URL")),
                    "user": str(entry.get("User") or ""),
                    "password": str(entry.get("Passwd") or ""),
                })
    return pools


def _switch_pool_sealminer(ip: str, payload: dict, cfg: dict,
                           raw_creds: dict | None) -> tuple[bool, str]:
    """Rewrite pool slot pool_id via RPC updatepools + web
    reboot (mapping §2.4): the current RPC pools are read
    first, slot pool_id is replaced, the rest re-sent
    unchanged. No evidenced slot cap — pool_id may address
    any existing slot or append one past the end."""
    url = payload.get("url")
    user = payload.get("user")
    if not url or not user:
        return False, ("switch_pool on sealminer needs 'url' and "
                       "'user' in the payload — updatepools always "
                       "rewrites the pool list, there is no "
                       "activate-a-configured-slot form")
    try:
        pool_id = int(payload.get("pool_id", 0))
    except (TypeError, ValueError):
        return False, (f"switch_pool: pool_id must be an integer, "
                       f"got {payload.get('pool_id')!r}")
    if pool_id < 0:
        return False, (f"switch_pool: pool_id must be >= 0, "
                       f"got {pool_id}")
    client = _sealminer_client(ip, cfg, raw_creds)
    norm = _sealminer_current_pools(client)
    if pool_id > len(norm):
        return False, (f"switch_pool: sealminer has {len(norm)} "
                       f"pool(s), pool_id {pool_id} is past the end "
                       f"(append is pool_id == {len(norm)})")
    while len(norm) <= pool_id:
        norm.append({"url": "", "user": "", "password": ""})
    norm[pool_id] = {"url": str(url), "user": str(user),
                     "password": str(payload.get("password", ""))}
    norm = [entry for entry in norm if entry.get("url")]
    try:
        client.set_pools(norm)
    except SealMinerError as exc:
        return False, f"sealminer switch_pool failed: {exc}"
    _u, _p, used_default = _sealminer_auth(raw_creds)
    note = (" (default seal/seal credentials — save a sealminer "
            "credential set if this fleet changed them)"
            if used_default else "")
    return True, (f"sealminer pool slot {pool_id} set to {url} "
                  f"(user {user}) via updatepools + reboot" + note)


def _set_power_sealminer(ip: str, payload: dict, cfg: dict,
                         raw_creds: dict | None) -> tuple[bool, str]:
    watts = _epic_int(payload, "watts", "power_target")
    if watts is None:
        return False, ("set_power_target on sealminer needs 'watts' "
                       "(or 'power_target') in the payload")
    return _sealminer_simple(ip, cfg, raw_creds, "set_power_limit",
                             "set_power_target (ascset powerlimit)",
                             watts)


def _set_mining_mode_sealminer(ip: str, payload: dict, cfg: dict,
                               raw_creds: dict | None) -> tuple[bool, str]:
    """Set the mining mode via RPC ascset workmode (mapping
    §2.4). low_power is A2-only (asic-rs set_tuning_config)
    — the model is read from devdetails first, and an
    unreadable model refuses low_power rather than guessing."""
    mode = payload.get("mode")
    if mode not in SEALMINER_MINING_MODES:
        return False, (f"set_mining_mode on sealminer needs 'mode' "
                       f"one of {list(SEALMINER_MINING_MODES)}, "
                       f"got {mode!r}")
    if mode == "low_power":
        client = _sealminer_client(ip, cfg, raw_creds)
        try:
            devdetails = client._cg.command("devdetails")
        except Exception as exc:  # noqa: BLE001 — gate must fail closed
            return False, (f"set_mining_mode low_power refused: "
                           f"cannot confirm this is an A2 ({exc})")
        model = None
        entries = devdetails.get("DEVDETAILS") \
            if isinstance(devdetails, dict) else None
        if isinstance(entries, list) and entries \
                and isinstance(entries[0], dict):
            model = entries[0].get("Model")
        if model != "A2":
            return False, ("Low-power mining mode is only supported "
                           f"on SealMiner A2 (this miner reports "
                           f"model {model!r})")
    return _sealminer_simple(ip, cfg, raw_creds, "set_mining_mode",
                             f"set_mining_mode (ascset workmode {mode})",
                             mode)


# Family actions beyond dashd (v0.33.0) — keyed (source, command);
# each handler is (ip, payload, cfg, raw_creds) -> (ok, message).
# Whatsminer handlers read the password from raw_creds (see
# _wm_password); LuxOS handlers need no password at all.
_FAMILY_ONLY = {
    ("whatsminer", "restart_mining"): lambda ip, p, c, r: _wm_simple(
        ip, c, r, "restart_btminer", "restart_mining (restart_btminer)"),
    ("whatsminer", "pause_mining"): lambda ip, p, c, r: _wm_simple(
        ip, c, r, "power_off", "pause_mining (power_off)"),
    ("whatsminer", "resume_mining"): lambda ip, p, c, r: _wm_simple(
        ip, c, r, "power_on", "resume_mining (power_on)"),
    ("whatsminer", "find_miner"): lambda ip, p, c, r: _wm_simple(
        ip, c, r, "set_led_auto", "find_miner (set_led auto)"),
    ("luxos", "pause_mining"): lambda ip, p, c, r: _curtail_luxos(
        ip, c, "sleep", "pause_mining (curtail sleep)"),
    ("luxos", "resume_mining"): lambda ip, p, c, r: _curtail_luxos(
        ip, c, "wakeup", "resume_mining (curtail wakeup)"),
    ("braiins", "pause_mining"): lambda ip, p, c, r: _braiins_simple(
        ip, c, "pause", "pause_mining (pause)"),
    ("braiins", "resume_mining"): lambda ip, p, c, r: _braiins_simple(
        ip, c, "resume", "resume_mining (resume)"),
    ("iceriver", "find_miner"): lambda ip, p, c, r: _find_miner_iceriver(
        ip, c, r),
    ("epic", "pause_mining"): lambda ip, p, c, r: _epic_simple(
        ip, c, r, "stop_mining", "pause_mining (/miner stop)"),
    ("epic", "restart_mining"): lambda ip, p, c, r: _epic_simple(
        ip, c, r, "softreboot", "restart_mining (/softreboot)"),
    ("epic", "find_miner"): lambda ip, p, c, r: _epic_simple(
        ip, c, r, "identify", "find_miner (/identify on)"),
    ("epic", "set_preset"): _set_preset_epic,
    ("epic", "change_password"): _change_password_epic,
    ("epic", "set_power_target"): _set_power_epic,
    ("epic", "set_shutdown_temp"): _set_shutdown_epic,
    ("epic", "set_fan_speed"): _set_fan_epic,
    ("epic", "tune"): _tune_epic,
    ("auradine", "pause_mining"): lambda ip, p, c, r: _auradine_simple(
        ip, c, r, "set_sleep", "pause_mining (web mode sleep on)",
        True),
    ("auradine", "resume_mining"): lambda ip, p, c, r: _auradine_simple(
        ip, c, r, "set_sleep", "resume_mining (web mode sleep off)",
        False),
    ("auradine", "restart_mining"): lambda ip, p, c, r: _auradine_simple(
        ip, c, r, "restart_mining",
        "restart_mining (web restart gcminer)"),
    ("auradine", "find_miner"): lambda ip, p, c, r: _auradine_simple(
        ip, c, r, "set_fault_light", "find_miner (web led code 3)",
        True),
    ("auradine", "set_power_target"): _set_power_auradine,
    ("sealminer", "pause_mining"): lambda ip, p, c, r: _sealminer_simple(
        ip, c, r, "pause", "pause_mining (ascset 0,suspend)"),
    ("sealminer", "resume_mining"): _resume_sealminer,
    ("sealminer", "find_miner"): lambda ip, p, c, r: _sealminer_simple(
        ip, c, r, "set_fault_light", "find_miner (web led_conf on)",
        True),
    ("sealminer", "set_power_target"): _set_power_sealminer,
    ("sealminer", "set_mining_mode"): _set_mining_mode_sealminer,
}


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
            if source in ("cgminer", "avalon"):
                # Avalon is the cgminer wire with a Canaan claim —
                # the privileged restart RPC is the family mechanism
                # (v0.30, docs/vendor-coverage-mapping.md §2).
                return _reboot_cgminer(ip, cfg)
            if source == "vnish":
                return _reboot_dashd(ip, cfg)
            if source == "stock":
                return _reboot_stock(ip, cfg)
            if source == "whatsminer":
                # G-W1 closed in v0.33.0: token-authenticated
                # {"cmd": "reboot"} (mapping §1.5).
                return _reboot_whatsminer(ip, cfg, creds)
            if source == "luxos":
                return _reboot_luxos(ip, cfg)
            if source == "epic":
                return _reboot_epic(ip, cfg, creds)
            if source == "auradine":
                # G-AU closed in v0.38.0: web POST restart
                # (mapping §1.4).
                return _reboot_auradine(ip, cfg, creds)
            if source == "sealminer":
                # Web GET reboot.php (mapping §2.4).
                return _reboot_sealminer(ip, cfg, creds)
            return False, f"reboot: unknown miner source {source!r}"
        if command_type == "switch_pool":
            if source == "vnish":
                return _switch_pool_dashd(ip, payload, cfg)
            if source == "whatsminer":
                return _switch_pool_whatsminer(ip, payload, cfg, creds)
            if source == "epic":
                return _switch_pool_epic(ip, payload, cfg, creds)
            if source == "auradine":
                return _switch_pool_auradine(ip, payload, cfg, creds)
            if source == "sealminer":
                return _switch_pool_sealminer(ip, payload, cfg, creds)
            return False, (f"switch_pool is {NOT_SUPPORTED} "
                           f"(source: {source or 'unknown'})")
        family = _FAMILY_ONLY.get((source, command_type))
        if family is not None:
            return family(ip, payload, cfg, creds)
        handler = _DASHD_ONLY.get(command_type)
        if handler is not None:
            if source == "vnish":
                return handler(ip, payload, cfg)
            return False, (f"{command_type} is {NOT_SUPPORTED} "
                           f"(source: {source or 'unknown'})")
        return False, f"unknown command type {command_type!r}"
    except Exception as exc:  # noqa: BLE001 — executors must never raise
        return False, f"{command_type} executor error: {exc}"

