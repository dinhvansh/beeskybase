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
  * whatsminer (v0.30) — NOT SUPPORTED: privileged calls ride the
    MicroBT token session and the token computation is not in the
    dissected contract (docs/vendor-coverage-mapping.md G-W1).

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

from .bitmain import BitmainClient, BitmainError
from .cgminer import CgminerClient, CgminerError
from .dashd import DashdClient, DashdError

COMMAND_TYPES = ("reboot", "switch_pool",
                 "pause_mining", "resume_mining", "restart_mining",
                 "find_miner", "throttle",
                 "reset_autotune_all", "reset_autotune_current",
                 "configure_api_key", "set_preset", "change_password")

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
                # Whatsminer privileged calls ride its token
                # session; the token computation is not in the
                # dissected contract (mapping G-W1) — honest gap,
                # never a pretend attempt.
                return False, (f"reboot is {NOT_SUPPORTED} "
                               f"(source: 'whatsminer')")
            return False, f"reboot: unknown miner source {source!r}"
        if command_type == "switch_pool":
            if source == "vnish":
                return _switch_pool_dashd(ip, payload, cfg)
            return False, (f"switch_pool is {NOT_SUPPORTED} "
                           f"(source: {source or 'unknown'})")
        handler = _DASHD_ONLY.get(command_type)
        if handler is not None:
            if source == "vnish":
                return handler(ip, payload, cfg)
            return False, (f"{command_type} is {NOT_SUPPORTED} "
                           f"(source: {source or 'unknown'})")
        return False, f"unknown command type {command_type!r}"
    except Exception as exc:  # noqa: BLE001 — executors must never raise
        return False, f"{command_type} executor error: {exc}"
