"""Notification channels — webhook, Telegram, logfile.

Routing mirrors EMCD Monitoring's settings matrix (researched
2026-11-09): per event type, choose which channels receive it and the
minimum severity that is worth sending. EMCD ships Email + Telegram;
BeeSky's channels are **webhook** (first-class — an OVER_TEMP webhook
can drive farm automation such as exhaust fans or water-mist relays
through a local controller), **Telegram**, and a JSON-lines **logfile**.

Config is one JSON file; see ``docs/notify.example.json``::

    {
      "thresholds": { ... EventEngine overrides ... },
      "channels": {
        "webhook":  {"enabled": true, "url": "https://...", "headers": {}},
        "telegram": {"enabled": true, "bot_token": "...", "chat_id": "...",
                     "api_base": "https://api.telegram.org"},
        "logfile":  {"enabled": true, "path": "events.log"}
      },
      "events": {
        "OVER_TEMP": {"channels": ["webhook", "telegram"],
                      "min_severity": "warning"},
        "*":         {"channels": ["logfile"], "min_severity": "info"}
      }
    }

Telegram credentials may also come from the environment
(``BEESKY_TELEGRAM_BOT_TOKEN`` / ``BEESKY_TELEGRAM_CHAT_ID``), which
wins over the config file. All HTTP is stdlib urllib and connects
*directly* (proxy env vars ignored — farm webhooks are LAN endpoints,
the same lesson the v0.2 adapters learned). Dispatch never raises: a
dead webhook must not kill the watch loop. Failures are collected in
:meth:`Notifier.pop_errors`.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .events import SEVERITIES, severity_rank

CHANNELS = ("webhook", "telegram", "logfile")
WEBHOOK_TIMEOUT_S = 5
WEBHOOK_RETRIES = 1  # one retry after the first attempt


def format_message(event: dict) -> str:
    """One-line human-readable rendering of an event (Telegram / console)."""
    return (f"[BeeSky] {event['type']} ({event['severity']}) "
            f"{event['ip']} {event['model']} — {event['detail']}")


def _post_json(url: str, payload: dict, headers: dict | None = None,
               timeout: float = WEBHOOK_TIMEOUT_S, retries: int = 0):
    """POST *payload* as JSON; return the HTTP status. Raises on failure.

    Connects directly (empty ProxyHandler) — see module docstring.
    """
    data = json.dumps(payload).encode("utf-8")
    all_headers = {"Content-Type": "application/json",
                   "User-Agent": "BeeSky/0.3"}
    if headers:
        all_headers.update(headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last_exc: Exception | None = None
    for _attempt in range(retries + 1):
        request = urllib.request.Request(
            url, data=data, method="POST", headers=all_headers)
        try:
            with opener.open(request, timeout=timeout) as response:
                response.read()
                return response.status
        except Exception as exc:  # noqa: BLE001 — retried, then reported
            last_exc = exc
    raise last_exc  # type: ignore[misc]


class Notifier:
    """Routes events from :class:`~beesky.core.events.EventEngine`."""

    def __init__(self, config: dict | None = None):
        config = config or {}
        self.channels_cfg: dict = config.get("channels", {}) or {}
        self.rules: dict = config.get("events", {}) or {}
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # routing
    # ------------------------------------------------------------------

    def _rule_for(self, event: dict) -> dict:
        rule = self.rules.get(event["type"]) or self.rules.get("*") or {}
        channels = rule.get("channels")
        if channels is None:
            channels = [name for name in CHANNELS
                        if self._channel_enabled(name)]
        min_severity = rule.get("min_severity", "info")
        if min_severity not in SEVERITIES:
            min_severity = "info"
        return {"channels": list(channels), "min_severity": min_severity}

    def _channel_enabled(self, name: str) -> bool:
        cfg = self.channels_cfg.get(name) or {}
        if not cfg.get("enabled"):
            return False
        if name == "webhook":
            return bool(cfg.get("url"))
        if name == "logfile":
            return bool(cfg.get("path"))
        if name == "telegram":
            token, _chat = self._telegram_credentials()
            return bool(token)
        return False

    def _telegram_credentials(self) -> tuple[str | None, str | None]:
        cfg = self.channels_cfg.get("telegram") or {}
        token = os.environ.get("BEESKY_TELEGRAM_BOT_TOKEN") or cfg.get("bot_token")
        chat = os.environ.get("BEESKY_TELEGRAM_CHAT_ID") or cfg.get("chat_id")
        return token, (str(chat) if chat is not None else None)

    # ------------------------------------------------------------------
    # channels
    # ------------------------------------------------------------------

    def _send_webhook(self, event: dict) -> None:
        cfg = self.channels_cfg["webhook"]
        _post_json(cfg["url"], event, headers=cfg.get("headers"),
                   timeout=WEBHOOK_TIMEOUT_S, retries=WEBHOOK_RETRIES)

    def _send_telegram(self, event: dict) -> None:
        cfg = self.channels_cfg.get("telegram") or {}
        token, chat_id = self._telegram_credentials()
        api_base = (cfg.get("api_base") or "https://api.telegram.org").rstrip("/")
        _post_json(f"{api_base}/bot{token}/sendMessage",
                   {"chat_id": chat_id, "text": format_message(event)},
                   timeout=WEBHOOK_TIMEOUT_S, retries=WEBHOOK_RETRIES)

    def _send_logfile(self, event: dict) -> None:
        path = Path(self.channels_cfg["logfile"]["path"])
        if path.parent and str(path.parent) not in ("", "."):
            path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # dispatch
    # ------------------------------------------------------------------

    _SENDERS = {"webhook": _send_webhook, "telegram": _send_telegram,
                "logfile": _send_logfile}

    def dispatch(self, event: dict) -> dict[str, bool]:
        """Send *event* to its routed channels; return per-channel success."""
        rule = self._rule_for(event)
        results: dict[str, bool] = {}
        if severity_rank(event["severity"]) < severity_rank(rule["min_severity"]):
            return results
        for name in rule["channels"]:
            if name not in CHANNELS or not self._channel_enabled(name):
                continue
            try:
                self._SENDERS[name](self, event)
                results[name] = True
            except Exception as exc:  # noqa: BLE001 — never kill the caller
                results[name] = False
                self._errors.append(
                    f"{name} <- {event['type']} {event['ip']}: {exc}")
        return results

    def pop_errors(self) -> list[str]:
        """Drain accumulated dispatch errors (for the CLI to report)."""
        errors, self._errors = self._errors, []
        return errors
