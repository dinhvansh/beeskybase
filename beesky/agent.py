"""Farm agent — scans at the site, dials OUT to the BeeSky cloud.

    python -m beesky agent <target> --cloud https://cloud.example.com
                                    --key <agent-key> --site "Xưởng 1"
                                    [--interval 30] [--notify cfg.json]
                                    [--once]

The agent is the farm-side half of the v0.5 cloud shape (the Pulse /
EMCD pattern): the cloud can never reach into a farm LAN, so the agent
runs the normal scan pipeline on-site, diffs it through the v0.3
:class:`~beesky.core.events.EventEngine` locally, and POSTs

  * the full snapshot to ``POST /api/ingest`` every pass, and
  * each event batch to ``POST /api/ingest/events`` as events fire,

authenticated with its per-site agent key
(``Authorization: Bearer <key>``).

Failure behaviour is deliberate: a dead cloud (or dead uplink) never
crashes the loop and never blocks local alerting. Snapshot POSTs are
simply superseded by the next pass; undelivered events are kept in a
bounded pending queue and retried on the following pass. Local
notification channels (``--notify``) dispatch immediately on-site —
the OVER_TEMP → webhook → fans/water automation path must work even
while the cloud is unreachable.

Like the notify channels, cloud POSTs connect *directly* (proxy env
vars ignored): the uplink target is explicit operator config, not
something a stray ``http_proxy`` should reroute.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

POST_TIMEOUT_S = 5
PENDING_CAP = 500


def _post_json(url: str, payload: dict, key: str, timeout: float =
               POST_TIMEOUT_S) -> int:
    """POST *payload* with the agent key; return the HTTP status.

    Raises on transport failure or non-2xx so the caller can retry on
    the next pass. Direct connection (empty ProxyHandler) — see the
    module docstring.
    """
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": "BeeSky-Agent/0.5",
                 "Authorization": f"Bearer {key}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        response.read()
        return response.status


def _is_error_record(record: dict) -> bool:
    return any(p.get("code") == "FETCH_ERROR" for p in record["problems"])


class AgentService:
    """Scan -> local event engine -> cloud ingest (+ local notify).

    *scan_fn* is the same injected zero-argument callable the web
    MonitorService uses, so the agent reuses the CLI's exact discovery
    + adapter pipeline without importing it.
    """

    def __init__(self, scan_fn, cloud_url: str, key: str, site: str,
                 interval: float = 30.0, notify_config: dict | None = None):
        from .core.events import EventEngine
        from .core.notify import Notifier

        notify_config = notify_config or {}
        self._scan_fn = scan_fn
        self.cloud_url = cloud_url.rstrip("/")
        self._key = key
        self.site = site
        self.interval = float(interval)
        self.engine = EventEngine(notify_config.get("thresholds"))
        self.notifier = Notifier(notify_config)
        self._pending_events: list[dict] = []

    # ------------------------------------------------------------------
    # cloud delivery
    # ------------------------------------------------------------------

    def _deliver_events(self) -> None:
        """Try to flush the pending-event queue; keep it on failure."""
        if not self._pending_events:
            return
        try:
            _post_json(f"{self.cloud_url}/api/ingest/events",
                       {"site": self.site, "ts": time.time(),
                        "events": self._pending_events}, self._key)
        except Exception as exc:  # noqa: BLE001 — retried next pass
            print(f"agent: cloud events POST failed ({exc}); "
                  f"{len(self._pending_events)} event(s) kept for retry",
                  file=sys.stderr)
            return
        self._pending_events = []

    def _deliver_snapshot(self, records: list[dict]) -> bool:
        try:
            _post_json(f"{self.cloud_url}/api/ingest",
                       {"site": self.site, "ts": time.time(),
                        "interval": self.interval,
                        "miners": records}, self._key)
            return True
        except Exception as exc:  # noqa: BLE001 — next pass supersedes it
            print(f"agent: cloud snapshot POST failed ({exc}); "
                  "will retry with the next pass", file=sys.stderr)
            return False

    # ------------------------------------------------------------------
    # passes
    # ------------------------------------------------------------------

    def run_pass(self) -> list[dict]:
        """One scan pass; returns the events it produced."""
        try:
            records = self._scan_fn()
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            print(f"agent: scan failed: {exc}", file=sys.stderr)
            return []
        present = {r["ip"]: r for r in records if not _is_error_record(r)}
        events = self.engine.observe_cycle(present)

        self._deliver_snapshot(records)
        for event in events:
            print(f"EVENT {event['type']} [{event['severity']}] "
                  f"{event['ip']} {event['model']} — {event['detail']}",
                  flush=True)
            results = self.notifier.dispatch(event)
            if results:
                sent = ", ".join(f"{name}={'ok' if ok else 'FAILED'}"
                                 for name, ok in results.items())
                print(f"  notified (local): {sent}", flush=True)
            for error in self.notifier.pop_errors():
                print(f"  notify error: {error}", file=sys.stderr)
        self._pending_events.extend(events)
        if len(self._pending_events) > PENDING_CAP:
            del self._pending_events[: len(self._pending_events) - PENDING_CAP]
        self._deliver_events()
        return events

    def run(self, once: bool = False) -> None:
        """Pass loop until Ctrl+C (or a single pass with *once*)."""
        mode = "single pass" if once else f"every {self.interval:g}s"
        print(f"BeeSky agent: site {self.site!r} -> {self.cloud_url} "
              f"({mode})", flush=True)
        try:
            while True:
                started = time.monotonic()
                self.run_pass()
                stamp = time.strftime("%H:%M:%S")
                print(f"[{stamp}] pass done", flush=True)
                if once:
                    break
                delay = self.interval - (time.monotonic() - started)
                if delay > 0:
                    time.sleep(delay)
        except KeyboardInterrupt:
            print("\nagent stopped")
