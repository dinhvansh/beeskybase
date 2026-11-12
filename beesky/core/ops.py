"""Operations task runner — one bulk device action, streamed (v0.26).

The local counterpart of the cloud agent's remote actions (v0.6):
where the agent executes cloud-issued commands against the farm LAN,
this runner executes ONE operator-issued task from the desktop app
against a selected set of miners, reporting per-device progress as it
goes. The port follows the HashCore Toolkit's Operations model —
see docs/operations-mapping.md for the dissection and the graded
action inventory. Only actions with a REAL primitive in this
codebase exist here; the rest are named gaps in that doc, on purpose.

Job (a JSON file — secrets never ride the command line; credential
sets are referenced by file path exactly like scan's --creds-file):

    {"type": "reboot" | "rescan" | "switch_pool" | <v0.29 tail>,
     "targets": ["192.168.2.101", ...],
     "payload": {...},            # switch_pool only: the legacy
                                  # single-slot {pool_id, url, user,
                                  # password} OR (v0.28) the preset/
                                  # clone form {"pools": [{url, user,
                                  # password?}, ...]} — 1..3 slots,
                                  # executed in order as pool_id
                                  # 0..2; worker strings may carry
                                  # {pattern} tokens (core.patterns),
                                  # expanded per device against the
                                  # target list + the enriched record
     "group": "Trại chính",        # optional: creds layer 1 (v0.24)
     "creds_file": "sets.json",   # optional: creds layer 2 (v0.23)
     "groups_file": "groups.json",# optional store override
     "workers": 4,                # parallel devices, hard cap 8
     "stagger_s": 0.0,            # pause between device starts
     "timeout": 3.0,              # per-device timeout, seconds
     "http_port": 80, "cgminer_port": 4028}

Credential resolution mirrors `scan --group/--creds-file` exactly:
the group's own sets lead, the creds-file (global) sets follow
(core.groups.effective_creds), and discover.ordered_creds applies
the family tiers per miner. With neither layer the probe falls back
to the legacy single root/root pair, as a plain scan does.

Per device the runner PROBES first (probe_host with the merged
sets): the probe identifies the family (``source``) and the winning
credential set, which is then translated into the single creds dict
core.actions.execute consumes — the same dict the cloud agent
passes. A device that does not answer is an honest per-device
failure ("not answering — action not executed"), never a guess.

Events (the CLI prints them as NDJSON; run_job takes any callable):

    {"event": "start", "type": ..., "total": N}
    {"event": "result", "done": k, "total": N, "ip": ...,
     "ok": bool, "message": str}      # rescan adds "record": {...}
    {"event": "summary", "type": ..., "total": N, "completed": k,
     "ok": x, "failed": y, "cancelled": z,
     "status": "success" | "hasErrors" | "error" | "cancelled",
     "elapsed_s": float}

Cancellation is cooperative: when the cancel event is set (the CLI
wires SIGTERM/SIGINT to it), devices not yet started are counted as
cancelled and in-flight devices finish within their timeout. On
Windows the app kills the sidecar outright — no summary is emitted
then, and the app accounts the remainder as cancelled itself (the
mapping doc names this mechanism divergence).
"""

from __future__ import annotations

import datetime
import ipaddress
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import actions, inspect as inspect_mod, patterns, report
from .auradine import AuradineClient, AuradineError
from .bitmain import BitmainClient, BitmainError
from .braiins import BraiinsClient, BraiinsError
from .cgminer import CgminerClient, CgminerError
from .dashd import DashdClient, DashdError
from .discover import CRED_TYPES, ordered_creds, probe_host
from .epic import EpicClient, EpicError
from .groups import GroupStore, effective_creds
from .iceriver import (DEFAULT_PASSWORD as ICERIVER_DEFAULT_PASSWORD,
                       IceRiverClient, IceRiverError)
from .sealminer import SealMinerClient, SealMinerError
from .whatsminer import WhatsminerClient, WhatsminerError

TASK_TYPES = ("rescan", "reboot", "switch_pool",
              # v0.29 VNish tail (docs/vnish-ops-mapping.md): the
              # dashd handlers live in core.actions; diagnostic_report
              # is runner-level (it writes files, like rescan it is
              # not an actions.execute command).
              "pause_mining", "resume_mining", "restart_mining",
              "find_miner", "throttle",
              "reset_autotune_all", "reset_autotune_current",
              "configure_api_key", "set_preset", "change_password",
              # v0.37.0 ePIC-only controls (docs/epic-mapping.md §4):
              # the dashboard-verified params the generic vocabulary
              # has no name for.
              "set_power_target", "set_shutdown_temp",
              "set_fan_speed", "tune",
              # v0.38.0 SealMiner-only control
              # (docs/vendor-docs2-mapping.md §2.4): the RPC
              # ascset workmode form.
              "set_mining_mode",
              "diagnostic_report")

MAX_TARGETS = 1024
MAX_WORKERS = 8


class JobError(ValueError):
    """A malformed job — the CLI turns it into exit 2 before any I/O."""


# ---------------------------------------------------------------------------
# credential files (the v0.23 schema; rules mirrored from cli.py —
# core cannot import the CLI layer, so the normaliser lives here too
# and mock_ops_test pins both to the same behaviour)
# ---------------------------------------------------------------------------

def _normalise_creds(data: list, source: str) -> list[dict]:
    creds: list[dict] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise JobError(f"{source}: entry {idx} must be an object")
        user = item.get("user")
        secret = item.get("password")
        api_key = item.get("api_key")
        has_login = isinstance(user, str) and isinstance(secret, str)
        has_key = isinstance(api_key, str) and bool(api_key)
        if not has_login and not has_key:
            raise JobError(
                f"{source}: entry {idx} needs string "
                "\"user\" + \"password\", or an \"api_key\"")
        label = item.get("label")
        raw_type = item.get("type")
        creds.append({
            "label": str(label) if label else (
                user if has_login else "api_key"),
            "user": user if isinstance(user, str) else "",
            "password": secret if isinstance(secret, str) else "",
            "api_key": api_key if has_key else None,
            "type": raw_type if raw_type in CRED_TYPES else "any",
        })
    return creds


def _load_creds_file(path: str) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JobError(f"cannot read creds file {path}: {exc}") from exc
    if not isinstance(data, list):
        raise JobError(
            f"creds file {path}: top level must be a JSON list of "
            "{\"label\", \"user\", \"password\", \"type\"} objects")
    return _normalise_creds(data, f"creds file {path}")


# ---------------------------------------------------------------------------
# job validation — everything is checked BEFORE the first device I/O,
# so a typo'd job fails loud and touches nothing (scan's exit-2 rule)
# ---------------------------------------------------------------------------

def validate_job(raw) -> dict:
    """Normalise a raw job document; JobError on anything malformed."""
    if not isinstance(raw, dict):
        raise JobError("job must be a JSON object")
    task_type = raw.get("type")
    if task_type not in TASK_TYPES:
        raise JobError(
            f"job \"type\" must be one of {list(TASK_TYPES)}, "
            f"got {task_type!r}")

    targets_raw = raw.get("targets")
    if not isinstance(targets_raw, list) or not targets_raw:
        raise JobError("job \"targets\" must be a non-empty list of IPs")
    if len(targets_raw) > MAX_TARGETS:
        raise JobError(
            f"job \"targets\" has {len(targets_raw)} entries; "
            f"the cap is {MAX_TARGETS}")
    targets: list[str] = []
    seen: set[str] = set()
    for idx, item in enumerate(targets_raw):
        if not isinstance(item, str):
            raise JobError(f"job targets entry {idx} must be a string IP")
        try:
            ip = str(ipaddress.IPv4Address(item.strip()))
        except ValueError:
            raise JobError(
                f"job targets entry {idx} is not an IPv4 address: "
                f"{item!r}") from None
        if ip not in seen:
            seen.add(ip)
            targets.append(ip)

    payload = raw.get("payload") or {}
    if not isinstance(payload, dict):
        raise JobError("job \"payload\" must be an object")
    if task_type == "switch_pool":
        if "pools" in payload:
            # The v0.28 preset/clone form — validated fully here
            # so a malformed preset touches nothing (the exit-2
            # rule). Mutually exclusive with the single-slot form.
            if any(k in payload for k in ("pool_id", "url", "user")):
                raise JobError(
                    "switch_pool payload: \"pools\" cannot be "
                    "combined with the single-slot \"pool_id\" / "
                    "\"url\" / \"user\" form")
            slots = payload["pools"]
            if not isinstance(slots, list) or not 1 <= len(slots) <= 3:
                raise JobError(
                    "switch_pool payload \"pools\" must be a list "
                    "of 1 to 3 slots")
            normalised: list[dict] = []
            for i, slot in enumerate(slots):
                if not isinstance(slot, dict):
                    raise JobError(
                        f"switch_pool pools slot {i} must be an "
                        "object")
                url, user = slot.get("url"), slot.get("user")
                if not isinstance(url, str) or not url \
                        or not isinstance(user, str) or not user:
                    raise JobError(
                        f"switch_pool pools slot {i} needs "
                        "non-empty \"url\" and \"user\"")
                entry = {"url": url, "user": user}
                pw = slot.get("password")
                if pw is not None:
                    if not isinstance(pw, str):
                        raise JobError(
                            f"switch_pool pools slot {i} "
                            "\"password\" must be a string")
                    if pw:
                        entry["password"] = pw
                normalised.append(entry)
            payload = {**payload, "pools": normalised}
        if "pool_id" in payload:
            try:
                pool_id = int(payload["pool_id"])
            except (TypeError, ValueError):
                raise JobError(
                    "switch_pool payload \"pool_id\" must be an "
                    f"integer, got {payload['pool_id']!r}") from None
            if pool_id < 0:
                raise JobError(
                    f"switch_pool payload \"pool_id\" must be >= 0, "
                    f"got {pool_id}")
            payload = {**payload, "pool_id": pool_id}
        url, user = payload.get("url"), payload.get("user")
        if bool(url) != bool(user):
            raise JobError(
                "switch_pool payload needs both \"url\" and \"user\" "
                "(or neither, to activate an existing slot)")

    # v0.29 payload contracts — validated here, before any I/O, so
    # a malformed tail job touches nothing (the exit-2 rule). The
    # ranges are the api-doc's own (docs/vnish-ops-mapping.md §2).
    if task_type == "throttle":
        percent = payload.get("percent")
        if isinstance(percent, bool) or not isinstance(percent, int):
            raise JobError(
                "throttle payload \"percent\" must be an integer, "
                f"got {percent!r}")
        if not 20 <= percent <= 100:
            raise JobError(
                "throttle payload \"percent\" must be within the "
                f"documented 20..100 range, got {percent}")
    if task_type in ("reset_autotune_all", "reset_autotune_current"):
        restart = payload.get("restart", True)
        if not isinstance(restart, bool):
            raise JobError(
                f"{task_type} payload \"restart\" must be a boolean")
        payload = {**payload, "restart": restart}
    if task_type == "configure_api_key":
        operation = payload.get("operation", "add")
        if operation not in ("add", "remove"):
            raise JobError(
                "configure_api_key payload \"operation\" must be "
                f"\"add\" or \"remove\", got {operation!r}")
        key = payload.get("key")
        if not isinstance(key, str) or len(key) != 32:
            raise JobError(
                "configure_api_key payload \"key\" must be a "
                "string of exactly 32 characters (the api-doc "
                "schema)")
        description = payload.get("description")
        if description is not None and not isinstance(description, str):
            raise JobError(
                "configure_api_key payload \"description\" must "
                "be a string")
        payload = {**payload, "operation": operation}
    if task_type == "set_preset":
        preset = payload.get("preset")
        if not isinstance(preset, str) or not preset.strip():
            raise JobError(
                "set_preset payload \"preset\" must be a non-empty "
                "string")
    if task_type == "change_password":
        new_password = payload.get("new_password")
        if not isinstance(new_password, str) or not new_password:
            raise JobError(
                "change_password payload \"new_password\" must be "
                "a non-empty string")
    if task_type == "diagnostic_report":
        report_dir = payload.get("report_dir")
        if not isinstance(report_dir, str) or not report_dir.strip():
            raise JobError(
                "diagnostic_report payload \"report_dir\" must be "
                "a non-empty directory path")
        reason = payload.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise JobError(
                "diagnostic_report payload \"reason\" must be a "
                "string")

    group = raw.get("group")
    if group is not None and not isinstance(group, str):
        raise JobError("job \"group\" must be a string")
    creds_file = raw.get("creds_file")
    if creds_file is not None and not isinstance(creds_file, str):
        raise JobError("job \"creds_file\" must be a string path")
    groups_file = raw.get("groups_file")
    if groups_file is not None and not isinstance(groups_file, str):
        raise JobError("job \"groups_file\" must be a string path")

    def _num(key, default, lo, hi):
        value = raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise JobError(f"job \"{key}\" must be a number")
        return max(lo, min(hi, float(value)))

    workers = raw.get("workers", 4)
    if isinstance(workers, bool) or not isinstance(workers, int):
        raise JobError("job \"workers\" must be an integer")
    workers = max(1, min(MAX_WORKERS, workers))

    return {
        "type": task_type,
        "targets": targets,
        "payload": payload,
        "group": group,
        "creds_file": creds_file,
        "groups_file": groups_file,
        "workers": workers,
        "stagger_s": _num("stagger_s", 0.0, 0.0, 3600.0),
        "timeout": _num("timeout", 3.0, 0.2, 120.0),
        "http_port": int(_num("http_port", 80, 1, 65535)),
        "cgminer_port": int(_num("cgminer_port", 4028, 1, 65535)),
    }


def load_job(path: str) -> dict:
    """Read + validate a job file; JobError on any problem."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JobError(f"cannot read job file {path}: {exc}") from exc
    return validate_job(raw)


def resolve_creds(job: dict) -> list[dict] | None:
    """The merged credential-set list for a job (v0.24 layering).

    Group sets first, then the global creds-file sets; None when
    neither layer exists (the probe then uses its legacy defaults).
    An unknown group or an unreadable file is a JobError — raised
    before any device is touched.
    """
    group_sets = None
    if job.get("group"):
        store = GroupStore(job.get("groups_file"))
        try:
            group = store.find(job["group"])
        except ValueError as exc:
            raise JobError(str(exc)) from exc
        if group is None:
            raise JobError(
                f"group not found: {job['group']!r} (store: {store.path})")
        if group["creds"]:
            group_sets = _normalise_creds(
                group["creds"], f"group {job['group']!r} creds")
    global_sets = None
    if job.get("creds_file"):
        global_sets = _load_creds_file(job["creds_file"])
    return effective_creds(group_sets, global_sets)


# ---------------------------------------------------------------------------
# per-device execution
# ---------------------------------------------------------------------------

def _action_creds(cand, merged: list[dict] | None,
                  job: dict) -> dict:
    """Translate a probe outcome into actions.execute's creds dict.

    The winning set rides the candidate: stock keeps its user/password
    pair; a vnish win is either the api key or the JWT the probe
    minted. When the probe needed NO auth (anonymous dashd reads) but
    sets exist, the first family-ordered set is the configured method
    for that vendor — the write attempt uses it, and a wrong one
    fails honestly per device, exactly like a mis-tagged scan set.
    """
    base = {"http_port": job["http_port"],
            "cgminer_port": job["cgminer_port"],
            "timeout": job["timeout"]}
    if cand.source == "stock":
        return {**base, "user": cand.username, "password": cand.password}
    if cand.source == "vnish":
        out = None
        fallback_pw = None
        if cand.dashd_api_key:
            out = {**base, "api_key": cand.dashd_api_key}
        elif cand.dashd_token:
            out = {**base, "token": cand.dashd_token}
        elif merged:
            for entry in ordered_creds(merged, "vnish"):
                if entry.get("api_key"):
                    out = {**base, "api_key": entry["api_key"]}
                    break
                if entry.get("password"):
                    out = {**base, "user": entry["user"],
                           "password": entry["password"]}
                    fallback_pw = entry["password"]
                    break
        if out is None:
            out = base
        if job["type"] == "change_password":
            # The handler needs the CURRENT password (the doc's
            # PasswordChange.current). It is known exactly when a
            # password is what the write will authenticate with:
            # the anonymous-win fallback set above, or — for a
            # locked dashd the probe unlocked — the winning set,
            # found in the merged list by the candidate's label.
            # "" is the explicit UNKNOWN (an api-key win, or no
            # sets at all): the handler turns it into the honest
            # failure instead of guessing the factory default,
            # which actions._creds would otherwise silently fill.
            known = fallback_pw or ""
            if not known and cand.dashd_token and merged:
                for entry in merged:
                    if entry.get("label") == cand.cred_label \
                            and entry.get("password"):
                        known = entry["password"]
                        break
            out = {**out, "password": known}
        return out
    if cand.source == "epic":
        # ePIC writes authenticate with a plain password
        # (mapping §4, D-E5): the first epic-tagged set's, else
        # "" — the handler falls back to the documented factory
        # default "letmein" (never the merged "root" filler).
        out = base
        if merged:
            for entry in ordered_creds(merged, "epic"):
                if entry.get("password"):
                    out = {**base, "password": entry["password"]}
                    break
        if "password" not in out:
            out = {**base, "password": ""}
        return out
    if cand.source in ("whatsminer", "luxos", "auradine", "sealminer"):
        # Anonymous reads, authenticated writes: the first
        # family-ordered set's password is the write method (the
        # whatsminer handler falls back to the factory default
        # "admin" when there is none — see actions._wm_password;
        # the auradine handler falls back to "admin/admin" and
        # the sealminer handler to "seal/seal" the same way;
        # "" here is the explicit "no set" marker, never the
        # merged "root" filler).
        out = base
        if merged:
            for entry in ordered_creds(merged, cand.source):
                if entry.get("password"):
                    out = {**base, "password": entry["password"]}
                    break
        if "password" not in out:
            out = {**base, "password": ""}
        return out
    return base


def _fetch_record(cand, timeout: float) -> dict:
    """Full health record for one candidate (the cli fetch stage,
    mirrored: the candidate carries the auth the probe won)."""
    ip = cand.ip
    fetch_timeout = max(timeout, 2.0)
    if cand.source == "whatsminer":
        client = WhatsminerClient(ip, port=cand.cgminer_port,
                                  timeout=fetch_timeout)
        try:
            record = client.fetch_record(ip)
        except WhatsminerError as exc:
            record = report.error_record(ip, str(exc),
                                         source="whatsminer")
    elif cand.source == "braiins":
        client = BraiinsClient(ip, port=cand.cgminer_port,
                               timeout=fetch_timeout)
        try:
            record = client.fetch_record(ip)
        except BraiinsError as exc:
            record = report.error_record(ip, str(exc),
                                         source="braiins")
    elif cand.source == "iceriver":
        client = IceRiverClient(
            ip, port=cand.http_port, timeout=fetch_timeout,
            password=cand.iceriver_password or ICERIVER_DEFAULT_PASSWORD)
        try:
            record = client.fetch_record(ip)
        except IceRiverError as exc:
            record = report.error_record(ip, str(exc),
                                         source="iceriver")
    elif cand.source == "epic":
        # ePIC HTTP JSON API on 4028 (v0.37.0) — GET reads need
        # no password.
        client = EpicClient(ip, port=cand.cgminer_port,
                            timeout=fetch_timeout)
        try:
            record = client.fetch_record(ip)
        except EpicError as exc:
            record = report.error_record(ip, str(exc),
                                         source="epic")
    elif cand.source == "auradine":
        # Auradine RPC 4028 + web :8080 (v0.38.0) — reads need
        # no auth.
        client = AuradineClient(ip, port=cand.cgminer_port,
                                timeout=fetch_timeout)
        try:
            record = client.fetch_record(ip)
        except AuradineError as exc:
            record = report.error_record(ip, str(exc),
                                         source="auradine")
    elif cand.source == "sealminer":
        # SealMiner RPC 4028 + web CGI :80 (v0.38.0) — the web
        # CGI lives on the HTTP port (the cli fetch's twin).
        client = SealMinerClient(ip, port=cand.cgminer_port,
                                 web_port=cand.http_port,
                                 timeout=fetch_timeout)
        try:
            record = client.fetch_record(ip)
        except SealMinerError as exc:
            record = report.error_record(ip, str(exc),
                                         source="sealminer")
    elif cand.source == "vnish":
        client = DashdClient(ip, port=cand.http_port, timeout=fetch_timeout,
                             api_key=cand.dashd_api_key,
                             token=cand.dashd_token)
        try:
            record = client.fetch_record(ip)
        except DashdError as exc:
            record = report.error_record(ip, str(exc), source="vnish")
    elif cand.source == "stock":
        client = BitmainClient(ip, port=cand.http_port, timeout=fetch_timeout,
                               username=cand.username,
                               password=cand.password)
        try:
            record = client.fetch_record(
                ip, status_data=cand.status_data or None)
        except BitmainError as exc:
            record = report.error_record(ip, str(exc), source="stock")
    else:
        # cgminer family ("avalon" is the same wire, refined by
        # the probe; "luxos" the same wire with the LUXminer
        # version refinement, v0.33.0; the stats cache rides the
        # candidate, v0.30).
        source = cand.source if cand.source in ("avalon", "luxos") \
            else "cgminer"
        client = CgminerClient(ip, port=cand.cgminer_port,
                               timeout=fetch_timeout)
        try:
            summary = client.summary()
            stats = cand.stats_data or client.stats()
        except CgminerError as exc:
            record = report.error_record(ip, str(exc), source=source)
        else:
            record = report.build_record(ip, summary, stats,
                                         source=source)
            # Pool enrichment (v0.28) — the cli fetch's twin
            # (docs/presets-ipreport-mapping.md §4).
            pools = client.pools_normalised()
            if pools is not None:
                record["pools"] = pools
    if cand.cred_label and not any(
            p.get("code") == "FETCH_ERROR" for p in record["problems"]):
        record["cred_label"] = cand.cred_label
    return record


def _expand_user(template: str, ip: str, index: int, cand,
                 job: dict) -> tuple[bool, str]:
    """Expand one worker template for one device (v0.28).

    Returns (True, expanded) or (False, failure-message). The
    current-pool tokens ({account} / {pool-host} / …) read the
    device's enriched record — fetched here through the same
    candidate the probe produced; a device whose pools cannot
    be read fails those tokens honestly (patterns.PatternError
    names the missing data). {index} is the device's 0-based
    position in the job's target list — the {n} counter keys
    off the LIST, so parallel workers cannot scramble it.
    """
    if "{" not in template:
        return True, template
    current_user = current_url = None
    if patterns.needs_current_pool(template):
        try:
            record = _fetch_record(cand, job["timeout"])
        except Exception:  # noqa: BLE001 — expansion reports it below
            record = {}
        pools = record.get("pools") or []
        if pools:
            current_user = pools[0].get("worker")
            current_url = pools[0].get("url")
    ctx = patterns.PatternContext(ip=ip, index=index,
                                  current_user=current_user,
                                  current_url=current_url)
    try:
        return True, patterns.expand_worker(template, ctx)
    except patterns.PatternError as exc:
        return False, f"pool pattern: {exc}"


def _switch_pool_one(ip: str, index: int, cand, job: dict,
                     creds: dict) -> tuple[bool, str]:
    """switch_pool for one device — both payload forms (v0.28).

    Legacy single-slot payloads run exactly as v0.26 did (plus
    pattern expansion of the user field). The pools form (pool
    presets + clone) executes one single-slot write per slot,
    IN ORDER, stopping at the first failure — a half-applied
    preset that kept going would be worse than a stopped one;
    the message reports each executed slot's outcome.
    """
    payload = job["payload"] or {}
    slots = payload.get("pools")
    if slots is None:
        single = dict(payload)
        if single.get("user"):
            ok, expanded = _expand_user(single["user"], ip, index,
                                        cand, job)
            if not ok:
                return False, expanded
            single["user"] = expanded
        return actions.execute(ip, cand.source, "switch_pool",
                               single or None, creds)
    messages: list[str] = []
    for slot_idx, slot in enumerate(slots):
        ok, expanded = _expand_user(slot["user"], ip, index, cand,
                                    job)
        if not ok:
            return False, expanded
        slot_payload = {"pool_id": slot_idx, "url": slot["url"],
                        "user": expanded}
        if slot.get("password"):
            slot_payload["password"] = slot["password"]
        ok, message = actions.execute(ip, cand.source, "switch_pool",
                                      slot_payload, creds)
        messages.append(f"pool {slot_idx + 1}: {message}")
        if not ok:
            return False, "; ".join(messages)
    return True, "; ".join(messages)


def _diagnostic_one(ip: str, cand, job: dict,
                    merged: list[dict] | None):
    """diagnostic_report for one device (v0.29) — a BeeSky VARIANT
    (docs/vnish-ops-mapping.md §2.12): there is no dashd
    diagnostics endpoint and HashCore's bundle contents are
    unobservable, so the bundle is BeeSky's own composition — the
    health record + the inspect document, both from the existing
    clients — written as one JSON file per device into the job's
    report_dir. A device whose record is a FETCH_ERROR fails
    honestly and produces no file (a bundle about nothing is not
    a report).
    """
    payload = job["payload"] or {}
    record = _fetch_record(cand, job["timeout"])
    if any(p.get("code") == "FETCH_ERROR" for p in record["problems"]):
        detail = record["problems"][0].get("detail") or "fetch failed"
        return False, f"diagnostic report: {detail}", None
    doc = inspect_mod.inspect_device(
        ip, timeout=job["timeout"], http_port=job["http_port"],
        cgminer_port=job["cgminer_port"], creds=merged)
    bundle = {
        "kind": "beesky-diagnostic-report",
        "variant": "beesky (not a HashCore port — see "
                   "docs/vnish-ops-mapping.md §2.12)",
        "ip": ip,
        "source": cand.source,
        "at": datetime.datetime.now(datetime.timezone.utc)
              .isoformat(timespec="seconds"),
        "reason": payload.get("reason") or None,
        "record": record,
        "inspect": doc,
    }
    out_dir = Path(payload["report_dir"])
    out_path = out_dir / f"{ip}-diagnostic.json"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(bundle, indent=2, ensure_ascii=False),
            encoding="utf-8")
    except OSError as exc:
        return False, f"diagnostic report: cannot write " \
                      f"{out_path}: {exc}", None
    return True, f"diagnostic report saved: {out_path.name}", None


def _run_one(ip: str, index: int, job: dict,
             merged: list[dict] | None):
    """One device: probe, then act. Returns (ok, message, record?).

    The probe is guarded: a device answering with malformed HTTP
    can raise outside the adapters' own error types (e.g.
    http.client.BadStatusLine), and a task runner must turn that
    into THIS device's failure — never let one sick device kill
    the whole run (actions.execute already never raises).
    """
    try:
        cand = probe_host(ip, timeout=job["timeout"],
                          http_port=job["http_port"],
                          cgminer_port=job["cgminer_port"],
                          creds=merged)
    except Exception as exc:  # noqa: BLE001 — per-device honesty
        return False, f"probe of {ip} failed: {exc}", None
    if cand is None or not cand.source:
        return False, ("miner is not answering and its source could "
                       "not be probed — action not executed"), None
    if job["type"] == "rescan":
        record = _fetch_record(cand, job["timeout"])
        if any(p.get("code") == "FETCH_ERROR" for p in record["problems"]):
            detail = record["problems"][0].get("detail") or "fetch failed"
            return False, f"rescan: {detail}", record
        return True, f"rescanned ({cand.source})", record
    if job["type"] == "diagnostic_report":
        return _diagnostic_one(ip, cand, job, merged)
    creds = _action_creds(cand, merged, job)
    if job["type"] == "switch_pool":
        ok, message = _switch_pool_one(ip, index, cand, job, creds)
        return ok, message, None
    ok, message = actions.execute(ip, cand.source, job["type"],
                                  job["payload"] or None, creds)
    return ok, message, None


# ---------------------------------------------------------------------------
# the runner
# ---------------------------------------------------------------------------

def run_job(job: dict, emit, cancel: threading.Event | None = None) -> dict:
    """Execute one validated job, emitting events; returns the summary.

    *emit* receives each event dict (the start line, one result per
    COMPLETED device, the final summary). Devices never started
    because *cancel* was set are counted in the summary's
    ``cancelled`` — they get no result event, so consumers account
    them from the summary (the app does exactly that after a kill).
    """
    merged = resolve_creds(job)
    emit_lock = threading.Lock()
    raw_emit = emit

    def emit(event: dict) -> None:  # noqa: F811 — serialised wrapper
        with emit_lock:
            raw_emit(event)

    targets = job["targets"]
    total = len(targets)
    workers = max(1, min(job["workers"], total))
    started = time.monotonic()
    emit({"event": "start", "type": job["type"], "total": total})

    results: dict[str, dict] = {}
    lock = threading.Lock()
    done_count = 0
    # The stagger gate (mapping §4.5): device ACTIONS start at least
    # stagger_s apart — executions may overlap, onsets don't pile up.
    gate = {"next_at": 0.0}

    def work(item: tuple[int, str]) -> None:
        index, ip = item
        nonlocal done_count
        if cancel is not None and cancel.is_set():
            return
        if job["stagger_s"]:
            with lock:
                now = time.monotonic()
                wait = max(0.0, gate["next_at"] - now)
                gate["next_at"] = max(now, gate["next_at"]) \
                    + job["stagger_s"]
            if wait:
                time.sleep(wait)
            if cancel is not None and cancel.is_set():
                return
        ok, message, record = _run_one(ip, index, job, merged)
        with lock:
            done_count += 1
            entry = {"event": "result", "done": done_count, "total": total,
                     "ip": ip, "ok": ok, "message": message}
            if record is not None:
                entry["record"] = record
            results[ip] = entry
        emit(entry)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work, enumerate(targets)))

    completed = len(results)
    ok_n = sum(1 for e in results.values() if e["ok"])
    failed = completed - ok_n
    cancelled = total - completed
    if cancelled and cancel is not None and cancel.is_set():
        status = "cancelled"
    elif failed == 0:
        status = "success"
    elif ok_n == 0:
        status = "error"
    else:
        status = "hasErrors"
    summary = {"event": "summary", "type": job["type"], "total": total,
               "completed": completed, "ok": ok_n, "failed": failed,
               "cancelled": cancelled, "status": status,
               "elapsed_s": round(time.monotonic() - started, 3)}
    emit(summary)
    return summary
