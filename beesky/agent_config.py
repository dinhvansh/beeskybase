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

SECURITY NOTE: the agent key lives in this file in plain text — the
file *is* the credential, exactly like the token files of the
Pulse/EMCD agents this design follows. The cloud only stores a
SHA-256 hash of the key and can revoke it at any time (cloud Cài đặt
view / ``agent_by_key``), but anyone who can read this file can
impersonate the agent until then. Keep it on the farm PC's own disk,
readable only by the account that runs the agent.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_ENV_VAR = "BEESKY_AGENT_CONFIG"
CONFIG_FILENAME = "agent-config.json"


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
        for name in ("target", "cloud_url", "key", "site",
                     "user", "password"):
            value = getattr(cfg, name)
            setattr(cfg, name, "" if value is None else str(value))
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

    def save(self, path: str | Path | None = None) -> Path:
        """Write the config as indented JSON; returns the path used.

        Creates the parent directory on first save (the config
        window's "Lưu cấu hình" on a fresh PC).
        """
        cfg_path = Path(path) if path is not None \
            else default_config_path()
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
            + "\n", encoding="utf-8")
        return cfg_path
