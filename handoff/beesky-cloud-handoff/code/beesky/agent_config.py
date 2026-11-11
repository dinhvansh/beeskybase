"""Persistent configuration for the standalone BeeSky Agent app.

The farm agent used to exist only as a command line
(``beesky agent <target> --cloud ... --key ... --site ...``). The
v0.14 agent app (:mod:`beesky.agent_app`) keeps those settings in one
JSON file instead, so the agent can be set up once in a small config
window and then run unattended (Windows Scheduled Task, see
``beesky-agent install-task``):

    {
      "target": "192.168.1.10-192.168.1.60",
      "cloud_url": "https://cloud.example.com",
      "key": "<agent key, shown once by the cloud>",
      "site": "Xưởng 1",
      "interval": 30,
      "notify_config": null,
      "auto_update": false
    }

``notify_config`` is the same dict the ``--notify`` JSON file carries
for the CLI agent (local alert channels — Telegram / webhook), or
``null`` for no local alerting. The remaining optional fields mirror
the CLI's scan flags (adapter credentials and ports) and keep their
CLI defaults when absent.

Where the file lives — :func:`default_config_path`:

  1. ``$BEESKY_AGENT_CONFIG`` when set (any OS),
  2. ``%APPDATA%\\BeeSky\\agent-config.json`` on Windows,
  3. ``~/.beesky/agent-config.json`` everywhere else.

SECURITY NOTE: the agent key in this file *is* the credential (the
cloud stores only a SHA-256 hash and can revoke it at any time —
cloud Cài đặt view / ``agent_by_key``). Since v0.16 the file is
hardened on a best-effort basis:

* On **Windows** the key is stored DPAPI-protected
  (``key_protected``, base64; the ``key`` field is written empty).
  Protection uses ``CRYPTPROTECT_LOCAL_MACHINE`` on purpose: the
  background agent runs as SYSTEM (see the Scheduled Task in
  :mod:`beesky.agent_app`), and a per-user blob would be unreadable
  to it. Machine scope means the blob can only be decrypted *on
  this PC* — copying the file elsewhere yields nothing — but any
  local administrator can still decrypt it. It protects against the
  file leaking off the machine, not against someone who already
  owns the machine.
* Everywhere else the key stays plain text, but the file is
  ``chmod 0600`` after every save (POSIX). On Windows an ``icacls``
  pass additionally restricts the file to the current user +
  SYSTEM. Both are best-effort: a failure never blocks saving.
* If DPAPI is present but the protect call itself fails, saving
  falls back to the plain-text key rather than losing the config.
* A config written by an older version (plain-text ``key``) is
  migrated in place on the next save; a ``key_protected`` blob that
  cannot be decrypted (file copied from another PC) loads as an
  empty key — re-issue the agent on the cloud and paste the new key.
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_ENV_VAR = "BEESKY_AGENT_CONFIG"
CONFIG_FILENAME = "agent-config.json"

# CRYPTPROTECT_LOCAL_MACHINE — see the security note above.
_CRYPTPROTECT_LOCAL_MACHINE = 0x04


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi_available() -> bool:
    """True when Windows DPAPI (crypt32) is callable from here.

    Probed per call (cheap attribute walks); tests monkeypatch this
    to force the protected / fallback branches off Windows.
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        return hasattr(ctypes, "windll") \
            and hasattr(ctypes.windll, "crypt32") \
            and hasattr(ctypes.windll, "kernel32")
    except Exception:  # noqa: BLE001 — a probe must never raise
        return False


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, object]:
    buffer = ctypes.create_string_buffer(data, len(data))
    blob = _DataBlob(len(data),
                     ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    return blob, buffer  # keep the buffer alive for the call


def protect_key(plaintext: str) -> str:
    """DPAPI-protect *plaintext*; returns base64 for the config file.

    Raises OSError when DPAPI is unavailable or the call fails —
    callers decide the fallback (save() degrades to plain text).
    """
    if not _dpapi_available():
        raise OSError("DPAPI is not available on this platform")
    in_blob, _buf = _blob_from_bytes(plaintext.encode("utf-8"))
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob), None, None, None, None,
        _CRYPTPROTECT_LOCAL_MACHINE, ctypes.byref(out_blob))
    if not ok:
        raise ctypes.WinError()
    try:
        raw = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return base64.b64encode(raw).decode("ascii")


def unprotect_key(blob_b64: str) -> str:
    """Reverse :func:`protect_key`; raises OSError on any failure
    (including a blob protected on a different machine)."""
    if not _dpapi_available():
        raise OSError("DPAPI is not available on this platform")
    raw = base64.b64decode(blob_b64.encode("ascii"), validate=True)
    in_blob, _buf = _blob_from_bytes(raw)
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0,
        ctypes.byref(out_blob))
    if not ok:
        raise ctypes.WinError()
    try:
        data = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return data.decode("utf-8")


def default_config_path(env: dict | None = None,
                        platform: str | None = None) -> Path:
    """Resolve the default agent-config path (see module docstring).

    *env* / *platform* are injectable for tests; production callers
    leave both as None and get the real environment.
    """
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    override = env.get(CONFIG_ENV_VAR)
    if override:
        return Path(override)
    if platform.startswith("win"):
        appdata = env.get("APPDATA")
        if appdata:
            return Path(appdata) / "BeeSky" / CONFIG_FILENAME
    return Path.home() / ".beesky" / CONFIG_FILENAME


@dataclass
class AgentConfig:
    """One farm agent's settings — the config file as a dataclass.

    The first seven fields are the documented config contract; the
    rest are the CLI agent's scan-side options with the CLI's own
    defaults, persisted only so a config-driven run behaves exactly
    like the equivalent `beesky agent` command line.
    """

    target: str = ""
    cloud_url: str = ""
    key: str = ""
    # DPAPI-protected form of `key` (base64, Windows — v0.16). The
    # in-memory `key` is always the plain text; save() writes either
    # `key` (plain) or `key_protected` (and an empty `key`), and
    # from_dict() decrypts back into `key` transparently.
    key_protected: str = ""
    site: str = ""
    interval: float = 30.0
    notify_config: dict | None = None
    auto_update: bool = False
    # --- scan-side options (CLI defaults) --------------------------
    timeout: float = 1.5
    workers: int = 64
    user: str = "root"
    password: str = "root"
    api_key: str | None = None
    token: str | None = None
    http_port: int = 80
    cgminer_port: int = 4028
    update_url: str | None = None

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Build from parsed JSON, ignoring unknown keys.

        Tolerant by design: a config written by a newer/older build
        (or edited by hand) must still load — missing fields keep
        their defaults, wrong-typed scalars are coerced where cheap.
        """
        if not isinstance(data, dict):
            raise ValueError("agent config is not a JSON object")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        values = {k: v for k, v in data.items() if k in known}
        cfg = cls(**values)
        cfg.interval = float(cfg.interval or 30.0)
        cfg.timeout = float(cfg.timeout or 1.5)
        cfg.workers = int(cfg.workers or 64)
        cfg.http_port = int(cfg.http_port or 80)
        cfg.cgminer_port = int(cfg.cgminer_port or 4028)
        cfg.auto_update = bool(cfg.auto_update)
        if cfg.notify_config is not None \
                and not isinstance(cfg.notify_config, dict):
            cfg.notify_config = None
        for name in ("target", "cloud_url", "key", "key_protected",
                     "site", "user", "password"):
            value = getattr(cfg, name)
            setattr(cfg, name, "" if value is None else str(value))
        if cfg.key_protected and not cfg.key:
            try:
                cfg.key = unprotect_key(cfg.key_protected)
            except Exception:  # noqa: BLE001 — foreign/corrupt blob
                # Documented behaviour (module docstring): a blob
                # that cannot be decrypted on this machine loads as
                # an empty key; the operator re-issues the agent.
                cfg.key = ""
        return cfg

    def to_dict(self) -> dict:
        return asdict(self)

    def missing_fields(self) -> list[str]:
        """Required-but-empty fields, in the order a human fixes them."""
        return [name for name in ("target", "cloud_url", "key", "site")
                if not str(getattr(self, name) or "").strip()]

    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path | None = None) -> "AgentConfig":
        """Load the config at *path* (default: :func:`default_config_path`).

        Raises FileNotFoundError when the file does not exist and
        ValueError when it is not valid config JSON — the caller
        decides how to present those (GUI status line / CLI error).
        """
        cfg_path = Path(path) if path is not None \
            else default_config_path()
        try:
            raw = cfg_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError(f"cannot read {cfg_path}: {exc}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{cfg_path} is not valid JSON: {exc}") \
                from exc
        return cls.from_dict(data)

    def _disk_dict(self) -> dict:
        """The dict actually written to disk (see the security note).

        With DPAPI available the key is stored protected and the
        plain ``key`` field is emptied; a protect failure degrades
        to plain text rather than failing the save. Either way the
        in-memory config keeps its plain-text key. This is also the
        migration path: a plain-text config from an older version is
        rewritten protected on its next save.
        """
        data = self.to_dict()
        if self.key and _dpapi_available():
            try:
                data["key_protected"] = protect_key(self.key)
                data["key"] = ""
                return data
            except Exception:  # noqa: BLE001 — degrade, don't lose it
                pass
        if self.key:
            # Plain-text save (no DPAPI, or it just failed): a stale
            # protected blob must not shadow the plain key on load.
            data["key_protected"] = ""
        # No plain key in memory (e.g. an undecryptable blob loaded
        # on a foreign machine): keep whatever blob we carry.
        return data

    def save(self, path: str | Path | None = None) -> Path:
        """Write the config as indented JSON; returns the path used.

        Creates the parent directory on first save (the config
        window's "Lưu cấu hình" on a fresh PC), then tightens the
        file's permissions best-effort (0600 on POSIX; an owner +
        SYSTEM-only ACL via icacls on Windows) — the file carries
        the agent key.
        """
        cfg_path = Path(path) if path is not None \
            else default_config_path()
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            json.dumps(self._disk_dict(), ensure_ascii=False, indent=2)
            + "\n", encoding="utf-8")
        _tighten_permissions(cfg_path)
        return cfg_path


def _tighten_permissions(cfg_path: Path) -> None:
    """Best-effort owner-only permissions on the config file.

    Never raises: the save already succeeded, and a locked-down
    file must not come at the cost of a crashed config window.
    """
    try:
        if sys.platform.startswith("win"):
            user = os.environ.get("USERNAME", "")
            grants = ["/grant:r", "SYSTEM:(F)"]
            if user:
                grants = ["/grant:r", f"{user}:(F)"] + grants
            subprocess.run(
                ["icacls", str(cfg_path), "/inheritance:r", *grants],
                capture_output=True, timeout=15)
        else:
            os.chmod(cfg_path, 0o600)
    except Exception:  # noqa: BLE001 — best effort by design
        pass
