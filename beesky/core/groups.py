"""Network groups (v0.24) — the HashCore Toolkit's home-screen concept.

A group is a named scan target with its own overrides:

    {"id": "…", "name": "Trại chính", "description": "Sảnh A — S19 Pro",
     "targets": "192.168.2.0/24",
     "creds": [ …v0.23 creds-file entries… ],
     "autoscan": {"enabled": false, "interval_min": 30},
     "last_scan": {"at": "…", "scanned": N, "found": N,
                   "ok": N, "check": N, "error": N} | null}

Groups persist in `beesky-groups.json` — the document is
{"version": 1, "groups": [...]} — located with the SAME strategy as
the v0.23 creds file: beside the executable first (the shipped
bundle folder), `%APPDATA%\\BeeSky\\` as the fallback when that
folder refuses writes. The full HashCore → BeeSky behaviour mapping,
with the deliberate divergences and the unknowns that were NOT
invented, lives in docs/network-groups-mapping.md.

Layering (the port of HashCore's global → per-group unlock-method
override onto BeeSky's v0.23 list model): a group scan merges the
group's credential sets BEFORE the global ones and lets the v0.23
ordering (`ordered_creds`) partition the merged list — its stable
tiers then yield exactly: group family → global family → group
"any" → global "any" → the rest, group-then-global. A group's set
wins ties, a failed group set never locks a machine out.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

from .discover import parse_targets

STORE_VERSION = 1
STORE_FILENAME = "beesky-groups.json"
DEFAULT_INTERVAL_MIN = 30


class GroupError(ValueError):
    """Operator-readable group/store failure.

    Subclasses ValueError so the CLI's existing scan validation
    path turns it into the same clean exit 2 as a malformed
    --creds-file or a bad target spec.
    """


# ---------------------------------------------------------------------------
# store location — the v0.23 creds-file strategy, mirrored
# ---------------------------------------------------------------------------

def _primary_dir() -> Path:
    """Beside the executable: the frozen bundle dir when shipped,
    the working directory for source runs (the cloud db default
    already lives there too)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def _fallback_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "BeeSky"
    return Path.home() / ".beesky"


def default_store_path() -> Path:
    """Resolve the default store file: an explicit
    BEESKY_GROUPS_FILE wins; then the primary file when it exists;
    then the fallback file when IT exists; otherwise the primary
    path (where the first save will create it)."""
    env = os.environ.get("BEESKY_GROUPS_FILE")
    if env:
        return Path(env)
    primary = _primary_dir() / STORE_FILENAME
    if primary.exists():
        return primary
    fallback = _fallback_dir() / STORE_FILENAME
    if fallback.exists():
        return fallback
    return primary


class GroupStore:
    """Load/save the groups document at one path.

    Loading is fail-loud (GroupError with an operator-readable
    message): a typo'd store must never silently scan the wrong
    ranges with the wrong logins — the creds file's philosophy.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else default_store_path()

    def load(self) -> list[dict]:
        """All groups, normalised; [] when the file does not exist."""
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GroupError(
                f"cannot read groups file {self.path}: {exc}") from exc
        if isinstance(data, list):
            raw_groups = data  # lenient: a bare list is a store too
        elif isinstance(data, dict) and isinstance(data.get("groups"), list):
            raw_groups = data["groups"]
        else:
            raise GroupError(
                f"groups file {self.path}: top level must be an object "
                "{\"version\": 1, \"groups\": [...]} (or a bare list)")
        return [normalise_group(item, f"{self.path} entry {idx}")
                for idx, item in enumerate(raw_groups)]

    def save(self, groups: list[dict]) -> Path:
        """Write the document atomically; returns the file written.

        When the resolved path is the primary location and the
        write is refused (Program Files installs), the document
        lands in the fallback dir instead and this store follows
        it — the CredStore rule, mirrored.
        """
        payload = {"version": STORE_VERSION, "groups": groups}
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        try:
            self._write(self.path, text)
            return self.path
        except OSError:
            if self.path == _primary_dir() / STORE_FILENAME:
                fallback = _fallback_dir() / STORE_FILENAME
                self._write(fallback, text)
                self.path = fallback
                return fallback
            raise

    @staticmethod
    def _write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(path) + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)

    # -- convenience over load/save --------------------------------

    def find(self, name: str) -> dict | None:
        for group in self.load():
            if group["name"] == name:
                return group
        return None

    def record_scan(self, name: str, summary: dict) -> None:
        """Persist one group's last_scan summary after a scan."""
        groups = self.load()
        for group in groups:
            if group["name"] == name:
                group["last_scan"] = summary
                self.save(groups)
                return
        raise GroupError(f"group not found: {name!r}")


# ---------------------------------------------------------------------------
# validation / normalisation
# ---------------------------------------------------------------------------

def _validate_cred_entries(raw, source: str) -> list[dict]:
    """Structural check of a group's embedded creds list.

    The entries keep the v0.23 --creds-file shape verbatim (the CLI
    normalises them with the very same code as a creds file when a
    scan consumes them); here we only prove each entry is an object
    carrying a login pair or an api_key, so a broken store fails at
    load time, not mid-scan.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise GroupError(f"{source}: \"creds\" must be a list")
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise GroupError(f"{source}: creds entry {idx} must be an object")
        has_login = isinstance(item.get("user"), str) \
            and isinstance(item.get("password"), str)
        has_key = isinstance(item.get("api_key"), str) \
            and bool(item.get("api_key"))
        if not has_login and not has_key:
            raise GroupError(
                f"{source}: creds entry {idx} needs string "
                "\"user\" + \"password\", or an \"api_key\"")
    return list(raw)


def normalise_group(raw, source: str = "group") -> dict:
    """Validate one group object and fill its defaults.

    Required: a non-empty "name" and a "targets" string that
    parse_targets accepts. Everything else defaults: a minted id,
    no creds, autoscan off at the default interval, no last scan.
    """
    if not isinstance(raw, dict):
        raise GroupError(f"{source}: a group must be an object")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise GroupError(f"{source}: a group needs a non-empty \"name\"")
    name = name.strip()
    description = raw.get("description", "")
    if description is None:
        description = ""
    if not isinstance(description, str):
        raise GroupError(
            f"{source} ({name!r}): \"description\" must be a string")
    description = description.strip()
    targets = raw.get("targets")
    if not isinstance(targets, str) or not targets.strip():
        raise GroupError(
            f"{source} ({name!r}): a group needs a \"targets\" string")
    targets = targets.strip()
    try:
        parse_targets(targets)
    except ValueError as exc:
        raise GroupError(
            f"{source} ({name!r}): invalid targets: {exc}") from exc

    autoscan_raw = raw.get("autoscan") or {}
    if not isinstance(autoscan_raw, dict):
        raise GroupError(f"{source} ({name!r}): \"autoscan\" must be an object")
    interval = autoscan_raw.get("interval_min", DEFAULT_INTERVAL_MIN)
    if isinstance(interval, bool) or not isinstance(interval, (int, float)) \
            or int(interval) < 1:
        raise GroupError(
            f"{source} ({name!r}): autoscan interval_min must be >= 1")

    last_scan = raw.get("last_scan")
    if last_scan is not None:
        if not isinstance(last_scan, dict) \
                or not isinstance(last_scan.get("at"), str):
            raise GroupError(
                f"{source} ({name!r}): \"last_scan\" must be null or an "
                "object with an \"at\" timestamp")
        last_scan = {
            "at": last_scan["at"],
            "scanned": int(last_scan.get("scanned") or 0),
            "found": int(last_scan.get("found") or 0),
            "ok": int(last_scan.get("ok") or 0),
            "check": int(last_scan.get("check") or 0),
            "error": int(last_scan.get("error") or 0),
        }

    gid = raw.get("id")
    return {
        "id": gid if isinstance(gid, str) and gid else secrets.token_hex(6),
        "name": name,
        "description": description,
        "targets": targets,
        "creds": _validate_cred_entries(raw.get("creds"), f"{source} ({name!r})"),
        "autoscan": {
            "enabled": bool(autoscan_raw.get("enabled", False)),
            "interval_min": int(interval),
        },
        "last_scan": last_scan,
    }


def find_group(groups: list[dict], name: str) -> dict | None:
    """Exact-name lookup — names are the operator-facing identity."""
    for group in groups:
        if group["name"] == name:
            return group
    return None


def merge_import(existing: list[dict], imported: list[dict]) -> list[dict]:
    """Merge an imported list into the stored one, BY NAME.

    A same-name imported group replaces the stored one in place
    (position kept); new names append in import order; every other
    stored group is kept untouched. BeeSky's stated policy —
    HashCore's own import policy could not be observed (see the
    mapping doc, §3.5).
    """
    merged = list(existing)
    positions = {g["name"]: i for i, g in enumerate(merged)}
    for group in imported:
        if group["name"] in positions:
            merged[positions[group["name"]]] = group
        else:
            positions[group["name"]] = len(merged)
            merged.append(group)
    return merged


def effective_creds(group_sets: list[dict] | None,
                    global_sets: list[dict] | None) -> list[dict] | None:
    """The credential list a group scan tries: group sets first,
    then global sets — or None when neither layer has any (the scan
    then keeps the legacy single --user/--password behaviour).

    The per-miner family ordering is NOT reimplemented here:
    discover.ordered_creds partitions this merged list stably, so
    its tiers come out group-family → global-family → group-any →
    global-any → the rest (group-then-global). Concatenation IS the
    layering.
    """
    merged = list(group_sets or []) + list(global_sets or [])
    return merged or None


def scan_summary(records: list[dict], scanned: int, at: str) -> dict:
    """The last_scan summary for one finished scan pass.

    error = records whose fetch failed outright (a FETCH_ERROR
    problem — the table's ERROR chip); check = the remaining
    non-OK records. Mirrors the Flutter fleet chips' counting.
    """
    ok = sum(1 for r in records if r.get("status") == "OK")
    error = sum(
        1 for r in records
        if any(p.get("code") == "FETCH_ERROR"
               for p in r.get("problems") or []))
    found = len(records)
    return {
        "at": at,
        "scanned": scanned,
        "found": found,
        "ok": ok,
        "check": found - ok - error,
        "error": error,
    }
