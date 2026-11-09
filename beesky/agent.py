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

Since v0.6 the same outbound channel carries *remote actions* back
down: each pass, after the ingest posts, the agent polls
``GET /api/agent/commands`` for viewer-issued commands (reboot,
switch_pool — :mod:`beesky.core.actions`), executes them against the
miners on the farm LAN with the same CLI credentials the scan
adapters use, and reports the outcome to
``POST /api/agent/commands/{id}/result``.

Failure behaviour is deliberate: a dead cloud (or dead uplink) never
crashes the loop and never blocks local alerting. Snapshot POSTs are
simply superseded by the next pass; undelivered events are kept in a
bounded pending queue and retried on the following pass. Command
results get the same treatment: if the result POST fails, the result
is queued and redelivered next pass before any new command runs.
Local notification channels (``--notify``) dispatch immediately
on-site — the OVER_TEMP → webhook → fans/water automation path must
work even while the cloud is unreachable.

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
PENDING_RESULTS_CAP = 50
COMMANDS_PER_PASS = 5


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
                 "User-Agent": "BeeSky-Agent/0.6",
                 "Authorization": f"Bearer {key}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        response.read()
        return response.status


def _get_json(url: str, key: str, timeout: float = POST_TIMEOUT_S) -> dict:
    """GET *url* with the agent key; return the parsed JSON body."""
    request = urllib.request.Request(
        url, method="GET",
        headers={"Accept": "application/json",
                 "User-Agent": "BeeSky-Agent/0.6",
                 "Authorization": f"Bearer {key}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        body = response.read()
    data = json.loads(body.decode("utf-8", errors="replace"))
    if not isinstance(data, dict):
        raise ValueError("cloud reply is not a JSON object")
    return data


def _is_error_record(record: dict) -> bool:
    return any(p.get("code") == "FETCH_ERROR" for p in record["problems"])


class AgentService:
    """Scan -> local event engine -> cloud ingest (+ local notify).

    *scan_fn* is the same injected zero-argument callable the web
    MonitorService uses, so the agent reuses the CLI's exact discovery
    + adapter pipeline without importing it.
    """

    def __init__(self, scan_fn, cloud_url: str, key: str, site: str,
                 interval: float = 30.0, notify_config: dict | None = None,
                 creds: dict | None = None):
        from .core.events import EventEngine
        from .core.notify import Notifier

        notify_config = notify_config or {}
        self._scan_fn = scan_fn
        self.cloud_url = cloud_url.rstrip("/")
        self._key = key
        self.site = site
        self.interval = float(interval)
        # Adapter credentials/ports for command execution (v0.6) — the
        # same values the CLI hands the scan adapters.
        self.creds = creds or {}
        self.engine = EventEngine(notify_config.get("thresholds"))
        self.notifier = Notifier(notify_config)
        self._pending_events: list[dict] = []
        self._pending_results: list[dict] = []

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
    # remote actions (v0.6)
    # ------------------------------------------------------------------

    def _report_result(self, command_id: int, status: str,
                       result: str) -> bool:
        try:
            _post_json(
                f"{self.cloud_url}/api/agent/commands/{command_id}/result",
                {"status": status, "result": result}, self._key)
            return True
        except Exception as exc:  # noqa: BLE001 — queued for next pass
            print(f"agent: result POST for command #{command_id} failed "
                  f"({exc}); queued for retry", file=sys.stderr)
            return False

    def _deliver_results(self) -> None:
        """Flush queued command results; keep the failures queued."""
        if not self._pending_results:
            return
        still_pending = []
        for item in self._pending_results:
            if not self._report_result(item["id"], item["status"],
                                       item["result"]):
                still_pending.append(item)
        self._pending_results = still_pending

    def _source_for(self, ip: str, records: list[dict]) -> str | None:
        """Miner source for *ip*: latest scan first, then a live probe."""
        fallback = None
        for record in records:
            if record.get("ip") != ip or not record.get("source"):
                continue
            if not _is_error_record(record):
                return record["source"]
            fallback = fallback or record["source"]
        if fallback:
            return fallback
        try:
            from .core.discover import discover
            found = discover(
                ip, timeout=max(float(self.creds.get("timeout") or 2.0), 1.0),
                workers=1,
                http_port=int(self.creds.get("http_port") or 80),
                cgminer_port=int(self.creds.get("cgminer_port") or 4028),
                username=self.creds.get("user") or "root",
                password=self.creds.get("password") or "root",
                api_key=self.creds.get("api_key"),
                token=self.creds.get("token"))
            for cand in found:
                if cand.ip == ip and cand.source:
                    return cand.source
        except Exception as exc:  # noqa: BLE001 — probing is best-effort
            print(f"agent: probe of {ip} failed: {exc}", file=sys.stderr)
        return None

    def _run_commands(self, records: list[dict]) -> None:
        """Poll the cloud for commands, execute them, report results."""
        from .core import actions

        try:
            reply = _get_json(
                f"{self.cloud_url}/api/agent/commands"
                f"?limit={COMMANDS_PER_PASS}", self._key)
        except Exception as exc:  # noqa: BLE001 — cloud outage != crash
            print(f"agent: command poll failed ({exc})", file=sys.stderr)
            return
        commands = reply.get("commands")
        if not isinstance(commands, list):
            return
        for command in commands[:COMMANDS_PER_PASS]:
            cmd_id = command.get("id")
            ip = command.get("ip") or ""
            ctype = command.get("type") or ""
            payload = command.get("payload") or {}
            source = self._source_for(ip, records)
            if source is None:
                ok, message = False, (f"miner {ip} is not answering and "
                                      "its source could not be probed — "
                                      "command not executed")
            else:
                ok, message = actions.execute(ip, source, ctype, payload,
                                              self.creds)
            status = "done" if ok else "failed"
            print(f"COMMAND #{cmd_id} {ctype} {ip} [{source or '?'}] "
                  f"-> {status}: {message}", flush=True)
            if not self._report_result(cmd_id, status, message):
                self._pending_results.append(
                    {"id": cmd_id, "status": status, "result": message})
                if len(self._pending_results) > PENDING_RESULTS_CAP:
                    del self._pending_results[
                        : len(self._pending_results) - PENDING_RESULTS_CAP]

    # ------------------------------------------------------------------
    # passes
    # ------------------------------------------------------------------

    def run_pass(self) -> list[dict]:
        """One scan pass; returns the events it produced."""
        try:
            records = self._scan_fn()
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            print(f"agent: scan failed: {exc}", file=sys.stderr)
            self._deliver_results()  # results don't depend on the scan
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
        # Remote actions ride last: results of earlier commands are
        # redelivered first, then this pass's commands run against the
        # fresh scan records (probing covers IPs the scan missed).
        # With --once the pass still polls once.
        self._deliver_results()
        self._run_commands(records)
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
