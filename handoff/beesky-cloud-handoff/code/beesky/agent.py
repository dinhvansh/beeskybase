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

Since v0.10 the agent also minds its own version: a daily check of
the signed update channel (first check 60 s after start, then every
24 h — :mod:`beesky.core.updater`) reports an ``UPDATE_AVAILABLE``
event to the cloud when a newer signed release exists. Applying it
is opt-in per agent (``--auto-update``, default OFF — farm safety):
an auto-updating agent swaps in the verified binary and exits so
the swap/relaunch of its exact argv can proceed.

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
UPDATE_FIRST_CHECK_S = 60.0
UPDATE_INTERVAL_S = 24 * 3600.0


def redact(text: str, *secrets: str) -> str:
    """Return *text* with every occurrence of each secret masked.

    Log hygiene (v0.16): the agent key — and anything derived from
    it, like an ``Authorization: Bearer <key>`` value — must never
    reach a log file or console. Failure messages interpolate
    exceptions whose text the agent does not control, so delivery /
    poll failure prints route through here with the key, and the
    agent app's background log writer redacts the whole stream as a
    second line of defence.
    """
    out = text
    for secret in secrets:
        if secret:
            out = out.replace(secret, "***")
    return out


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
                 creds: dict | None = None, auto_update: bool = False,
                 update_url_base: str | None = None,
                 status_hook=None):
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
        # Signed self-update (v0.10): report-only unless --auto-update.
        self.auto_update = auto_update
        self.update_url_base = update_url_base
        self._started_mono = time.monotonic()
        self._last_update_check: float | None = None
        self._update_reported: str | None = None
        self._exit_for_update = False
        # Per-cycle status sink (v0.16): called after every pass as
        # hook(ok, miners, error) — the agent app writes
        # agent-status.json through it. None = no reporting (the
        # `beesky agent` command line behaves exactly as before).
        self._status_hook = status_hook

    def _fail(self, message: str) -> None:
        """A failure line on stderr, with the agent key scrubbed."""
        print(redact(message, self._key), file=sys.stderr)

    def _emit_status(self, ok: bool, miners: int,
                     error: str | None) -> None:
        if self._status_hook is None:
            return
        try:
            self._status_hook(ok, miners,
                              redact(error, self._key) if error else None)
        except Exception:  # noqa: BLE001 — reporting must not break
            pass  # the monitoring loop it reports on

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
            self._fail(f"agent: cloud events POST failed ({exc}); "
                       f"{len(self._pending_events)} event(s) kept "
                       "for retry")
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
            self._fail(f"agent: cloud snapshot POST failed ({exc}); "
                       "will retry with the next pass")
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
            self._fail(f"agent: result POST for command "
                       f"#{command_id} failed ({exc}); queued "
                       "for retry")
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
            self._fail(f"agent: probe of {ip} failed: {exc}")
        return None

    def _run_commands(self, records: list[dict]) -> None:
        """Poll the cloud for commands, execute them, report results."""
        from .core import actions

        try:
            reply = _get_json(
                f"{self.cloud_url}/api/agent/commands"
                f"?limit={COMMANDS_PER_PASS}", self._key)
        except Exception as exc:  # noqa: BLE001 — cloud outage != crash
            self._fail(f"agent: command poll failed ({exc})")
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
    # signed self-update (v0.10)
    # ------------------------------------------------------------------

    def _maybe_update_check(self) -> None:
        """Daily signed-update check; report (and maybe apply).

        Cadence: first check UPDATE_FIRST_CHECK_S after start, then
        every UPDATE_INTERVAL_S. Never raises — a broken update
        channel must not disturb the monitoring loop. Each newly seen
        version is reported to the cloud exactly once per run.
        """
        now = time.monotonic()
        if self._last_update_check is None:
            if now - self._started_mono < UPDATE_FIRST_CHECK_S:
                return
        elif now - self._last_update_check < UPDATE_INTERVAL_S:
            return
        self._last_update_check = now
        from .core import updater

        try:
            res = updater.check(self.update_url_base)
        except Exception as exc:  # noqa: BLE001 — advisory only
            self._fail(f"agent: update check failed: {exc}")
            return
        if not res["ok"] or not res["update_available"]:
            return
        latest = res["latest"]
        if latest != self._update_reported:
            self._update_reported = latest
            stamp = time.time()
            event = {
                "ts": stamp,
                "time": time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(stamp)),
                "ip": None, "model": "BeeSky agent",
                "source": "beesky-agent",
                "type": "UPDATE_AVAILABLE", "severity": "info",
                "detail": (f"BeeSky {latest} is available (this agent "
                           f"runs {res['current']})"
                           + ("; --auto-update is on, applying it"
                              if self.auto_update else
                              "; run `beesky update` to install")),
                "data": {"current": res["current"], "latest": latest,
                         "auto_update": self.auto_update},
            }
            print(f"EVENT UPDATE_AVAILABLE [info] BeeSky {latest} "
                  f"(running {res['current']})", flush=True)
            self._pending_events.append(event)
            self._deliver_events()
        if not self.auto_update:
            return
        argv = ([sys.executable] + sys.argv[1:]
                if getattr(sys, "frozen", False) else
                [sys.executable, "-m", "beesky"] + sys.argv[1:])
        try:
            verdict = updater.apply(self.update_url_base,
                                    relaunch=True, argv=argv)
        except Exception as exc:  # noqa: BLE001 — retry tomorrow
            self._fail(f"agent: auto-update failed: {exc}")
            return
        print(f"agent: auto-update: {verdict['message']}", flush=True)
        if verdict["ok"] and not verdict["up_to_date"]:
            # The new binary is swapped in (Windows: the swap helper
            # relaunches us once we exit; POSIX: apply scheduled the
            # relaunch). Either way this process must now step aside.
            self._exit_for_update = True

    # ------------------------------------------------------------------
    # passes
    # ------------------------------------------------------------------

    def run_pass(self) -> list[dict]:
        """One scan pass; returns the events it produced."""
        try:
            records = self._scan_fn()
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            self._fail(f"agent: scan failed: {exc}")
            self._deliver_results()  # results don't depend on the scan
            self._emit_status(False, 0, f"scan failed: {exc}")
            return []
        present = {r["ip"]: r for r in records if not _is_error_record(r)}
        events = self.engine.observe_cycle(present)

        delivered = self._deliver_snapshot(records)
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
                self._fail(f"  notify error: {error}")
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
        self._maybe_update_check()
        self._emit_status(
            delivered, len(records),
            None if delivered else
            "cloud snapshot POST failed (see agent.log); "
            "will retry with the next pass")
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
                if self._exit_for_update:
                    print("agent: exiting so the self-update swap / "
                          "relaunch can proceed", flush=True)
                    break
                if once:
                    break
                delay = self.interval - (time.monotonic() - started)
                if delay > 0:
                    time.sleep(delay)
        except KeyboardInterrupt:
            print("\nagent stopped")
