# BeeSky web dashboard (v0.4)

A monitoring web UI on top of the same scan/watch engine as the CLI.
Pure Python 3 stdlib (`http.server.ThreadingHTTPServer`) — no new
dependencies, so the identical code also runs inside the packaged
single-file exe.

## Run it

```bash
# Local, this machine only (default bind 127.0.0.1):
python -m beesky serve 192.168.1.0/24 --port 8787 --interval 30

# With notifications (same config file as `beesky watch`):
python -m beesky serve 192.168.1.0/24 --notify docs/notify.example.json

# Expose on the LAN (trusted networks only — see the auth note below):
python -m beesky serve 192.168.1.0/24 --host 0.0.0.0
```

Open http://127.0.0.1:8787/ — summary cards (số máy, tổng hashrate, máy
có vấn đề, nhiệt độ cao nhất), a miners table and a live events feed.
The page polls the JSON API every 10 s; the **Quét ngay** button forces
an immediate scan pass.

All `scan`/`watch` options work too (`--user/--password` for stock
firmware, `--api-key/--token` for VNish, custom `--http-port` /
`--cgminer-port`), because `serve` reuses the exact same discovery +
adapter pipeline.

## JSON API

| Route            | Returns |
|------------------|---------|
| `GET /`          | The dashboard page |
| `GET /api/miners` | `{"generated_at", "generated_ts", "miners": [...]}` — latest normalised record per IP, plus `"online"` (answered in the most recent pass) |
| `GET /api/events` | `{"generated_at", "events": [...]}` — newest first, `?n=` up to 200 (ring buffer size) |
| `GET /api/status` | `{"uptime_s", "target", "interval", "miner_count", "event_count", "last_scan_at", "scan_count", "scanning"}` |
| `POST /api/scan` | `202 {"ok": true, "started": bool}` — starts a background scan unless one is already running |

Events are the v0.3 engine's events (OFFLINE, BACK_ONLINE,
HASHRATE_DROP, OVER_TEMP, CHIPS_LOST, CHAIN_DOWN) and are also
dispatched through the Notifier when `--notify` is given — so an
OVER_TEMP shown in the feed can simultaneously fire the farm-automation
webhook.

## No authentication in v0.4

There is **no login** yet. The default bind is `127.0.0.1` for that
reason. Anyone who can reach the port can see your fleet's IPs, models
and health. Binding `--host 0.0.0.0` (or publishing the Docker port) is
the deployer's choice — do it only on a trusted LAN/VPN, never on the
open internet.

## Docker

```bash
BEESKY_TARGET=192.168.1.0/24 docker compose up -d --build
# -> http://<host>:8787
```

The image (`python:3.12-slim` + the `beesky/` package, stdlib only)
binds `0.0.0.0:8787` *inside the container*; compose publishes it as
`8787:8787` and passes `BEESKY_TARGET` / `BEESKY_INTERVAL` through.

### The honest network caveat

A scanner can only see the network it runs on. A VPS or cloud server
**cannot** scan your farm's LAN — deploying there gives you a pretty,
empty dashboard. This is the same constraint EMCD Monitoring and
HashCore Pulse have: both run a local *agent* inside the farm.

So the Docker route is for:

- a small server / mini-PC / Raspberry Pi **inside the farm LAN**
  (on Linux, uncomment `network_mode: host` in docker-compose.yml so
  the container scans the host LAN rather than the Docker bridge), or
- a demo with a reachable target.

For a farm, the natural deployment is the packaged exe or this image
on an always-on machine at the site, exactly like a Pulse/EMCD agent.

## Packaging note (single-file exe)

`beesky/web/server.py` reads `dashboard.html` from beside itself at
startup. When building the one-file exe, bundle the page as data:

```bash
pyinstaller --onefile --add-data "beesky/web/dashboard.html:beesky/web" ...
```

If the file is missing at runtime, `/` falls back to a minimal page and
the JSON API keeps working.
