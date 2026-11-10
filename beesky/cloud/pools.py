"""Pool-side hashrate adapters + the cloud's pool poller (v0.9).

EMCD Monitoring's standout feature is comparing what the *farm*
reports (sum of miner-reported hashrate — BeeSky has that from agent
snapshots) with what the *pool* reports for the account. A persistent
gap means hashrate is going somewhere it should not: wrong pool
config, a dead stratum, a hijacked worker — or the pool itself is
under-reporting. This module fetches the pool side.

Adapters
--------
``generic`` — the real workhorse. The site config names a URL, optional
headers (an API key typically rides in one), a dot-notation ``json_path``
to the hashrate value, and the unit that value is in
(``TH/s`` | ``GH/s`` | ``PH/s``). Numeric path segments index into
lists (``data.workers.0.hashrate``).

``worker_filter`` changes the meaning of the last path segment: the
path up to it must resolve to a *list of worker objects*; objects whose
``worker`` / ``name`` / ``worker_name`` string contains the filter are
kept, and the named field is summed over them::

    json_path = "data.workers.hashrate"   worker_filter = "xuong1"
    -> sum(w["hashrate"] for w in data["workers"] if "xuong1" in name)

``emcd`` — a *preset* of the generic adapter, not a verified schema.
EMCD does expose a pool API, but its exact hashrate endpoint/field
shape could not be verified from anything available locally, so the
preset ships with a PLACEHOLDER url/path (see ``EMCD_PRESET``): the
owner replaces them with the real values from his own EMCD API
documentation (EMCD dashboard → API) and from then on it behaves
exactly like a generic config. Nothing here pretends otherwise.

Fetching connects *directly* (proxy env vars ignored), matching the
rest of BeeSky: a stray ``http_proxy`` on the cloud host must not
silently reroute — or break, for local test pools — these reads.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.request

from .store import CloudStore

FETCH_TIMEOUT_S = 10
DEFAULT_POLL_S = 300.0

UNIT_TO_THS = {"TH/s": 1.0, "GH/s": 0.001, "PH/s": 1000.0}

# Placeholder preset — see the module docstring. The URL/path below are
# deliberately obvious placeholders, NOT a verified EMCD API shape.
EMCD_PRESET = {
    "url": "https://emcd.io/api/v1/PLACEHOLDER_SET_FROM_EMCD_API_DOCS",
    "json_path": "PLACEHOLDER",
    "unit": "TH/s",
}


class PoolError(Exception):
    """Raised when a pool read fails or the payload has no hashrate."""


def resolve_config(raw: dict) -> dict:
    """Effective fetch config: EMCD preset under stored values."""
    config = dict(raw)
    if config.get("adapter") == "emcd":
        for key, value in EMCD_PRESET.items():
            if not config.get(key):
                config[key] = value
    return config


def _walk(data, path: str):
    """Resolve dot notation; numeric segments index into lists."""
    current = data
    for segment in path.split("."):
        if segment == "":
            raise PoolError(f"empty segment in json_path {path!r}")
        if isinstance(current, list):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError):
                raise PoolError(
                    f"json_path {path!r}: {segment!r} is not a valid "
                    "list index") from None
        elif isinstance(current, dict):
            if segment not in current:
                raise PoolError(
                    f"json_path {path!r}: key {segment!r} not present "
                    f"(have: {sorted(map(str, current))[:8]})")
            current = current[segment]
        else:
            raise PoolError(
                f"json_path {path!r}: cannot descend into "
                f"{type(current).__name__} at {segment!r}")
    return current


def _as_number(value, path: str) -> float:
    if isinstance(value, bool) or value is None:
        raise PoolError(f"json_path {path!r}: value is not a number")
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise PoolError(
            f"json_path {path!r}: value {value!r} is not numeric") from None


def extract_hashrate(payload, config: dict) -> float:
    """Raw (config-unit) hashrate from a decoded pool payload."""
    path = (config.get("json_path") or "").strip()
    if not path:
        raise PoolError("pool config has no json_path")
    worker_filter = config.get("worker_filter") or None
    if worker_filter:
        segments = path.split(".")
        if len(segments) < 2:
            raise PoolError(
                "worker_filter needs json_path of the form "
                "<list path>.<field>, e.g. data.workers.hashrate")
        workers = _walk(payload, ".".join(segments[:-1]))
        if not isinstance(workers, list):
            raise PoolError(
                f"json_path {path!r}: worker_filter set but the parent "
                "path does not resolve to a list")
        field = segments[-1]
        total = 0.0
        matched = 0
        for worker in workers:
            if not isinstance(worker, dict):
                continue
            name = str(worker.get("worker") or worker.get("name")
                       or worker.get("worker_name") or "")
            if worker_filter not in name:
                continue
            if field in worker:
                total += _as_number(worker[field], path)
                matched += 1
        if not matched:
            raise PoolError(
                f"no worker matching {worker_filter!r} with field "
                f"{field!r} in the pool reply")
        return total
    return _as_number(_walk(payload, path), path)


def fetch_pool_ths(config: dict, timeout: float = FETCH_TIMEOUT_S) -> float:
    """Fetch one pool read and return the pool-side hashrate in TH/s."""
    config = resolve_config(config)
    url = (config.get("url") or "").strip()
    if not url:
        raise PoolError("pool config has no url")
    unit = config.get("unit") or "TH/s"
    if unit not in UNIT_TO_THS:
        raise PoolError(f"unknown pool unit {unit!r}")
    headers = {"Accept": "application/json", "User-Agent": "BeeSky-Cloud"}
    for name, value in (config.get("headers") or {}).items():
        headers[str(name)] = str(value)
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise PoolError(f"pool GET {url} -> HTTP {exc.code}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise PoolError(f"pool GET {url} failed ({exc})") from exc
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise PoolError(f"pool GET {url} -> non-JSON reply") from exc
    return extract_hashrate(payload, config) * UNIT_TO_THS[unit]


class PoolPoller:
    """Background thread: sample every configured site's pool gap.

    One cycle = for each site with a pool config: fetch the pool
    hashrate, take the farm hashrate from the site's latest snapshot,
    and record the pair (the store decides on POOL_GAP events). Sites
    whose agent has not pushed a snapshot yet are skipped — there is
    no farm side to compare against. A failing pool never kills the
    thread; the error is logged and the next cycle retries.
    """

    def __init__(self, store: CloudStore, interval_s: float = DEFAULT_POLL_S):
        self.store = store
        self.interval_s = max(0.5, float(interval_s))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def poll_once(self) -> list[dict]:
        """Run one cycle; returns the samples recorded."""
        samples = []
        for site in self.store.list_pool_config_sites():
            config = self.store.pool_config_raw(site)
            if config is None:
                continue
            farm_ths = self.store.farm_ths(site)
            if farm_ths is None:
                continue
            try:
                pool_ths = fetch_pool_ths(config)
            except PoolError as exc:
                print(f"pool poller: site {site!r}: {exc}",
                      file=sys.stderr)
                continue
            sample = self.store.record_pool_sample(
                site, time.time(), pool_ths, farm_ths)
            samples.append(sample)
            if sample["event_fired"]:
                print(f"pool poller: POOL_GAP event for site {site!r} "
                      f"(gap {sample['gap_pct']}%)", file=sys.stderr)
        return samples

    def start(self) -> None:
        if self._thread is not None:
            return

        def loop() -> None:
            while not self._stop.wait(self.interval_s):
                try:
                    self.poll_once()
                except Exception as exc:  # noqa: BLE001 — never die
                    print(f"pool poller: cycle failed ({exc})",
                          file=sys.stderr)

        self._thread = threading.Thread(target=loop, name="pool-poller",
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
