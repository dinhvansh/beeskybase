# BeeSky cloud (v0.5) — agent + cloud backend + multi-site web

The full BeeSky product shape has three parts:

1. **Local tool** — `beesky scan` / `watch` / `serve` on one LAN
   (v0.1–v0.4), shipped as a Windows installer.
2. **Agent at the farm** — `beesky agent`, runs inside each farm LAN.
3. **Cloud** — `beesky cloud`, one server that many agents feed and
   the owner watches from anywhere.

Parts 2 + 3 are this document. The pattern is the one HashCore Pulse
and EMCD Monitoring use: the cloud can never reach into a farm LAN
(NAT, firewalls, dynamic IPs), so the agent dials **out**.

## Architecture

```
 ┌─ Farm / site "Xưởng 1" ────────────────┐      ┌─ Cloud server ─────────────┐
 │  miners ── LAN scan (cgminer/VNish/    │      │  beesky cloud              │
 │            stock adapters, như v0.1+)   │      │   SQLite store             │
 │  beesky agent                           │      │   ├─ agents (key hashes)   │
 │   ├─ EventEngine chạy tại chỗ           │      │   ├─ snapshots (mới nhất)  │
 │   ├─ Notifier tại chỗ (webhook quạt/    │      │   └─ events (5000 gần nhất)│
 │   │   nước — chạy cả khi mất cloud)     │      │                            │
 │   └─ POST /api/ingest        ───────────┼─HTTPS▶  POST /api/ingest         │
 │      POST /api/ingest/events ───────────┼─────▶  POST /api/ingest/events  │
 └─────────────────────────────────────────┘      │  GET /  multi-site web     │
 ┌─ Farm / site "Xưởng 2" ────────────────┐      │  GET /api/sites|miners|    │
 │  beesky agent ─────────────── pushes ───┼─────▶       events             │
 └─────────────────────────────────────────┘      └─────────────▲──────────────┘
                                                     browser (mật khẩu)
```

- The agent posts the **full snapshot every pass** and **each event
  batch as events fire**. An unreachable cloud never crashes the agent:
  snapshots are superseded by the next pass, undelivered events are
  kept in a bounded pending queue and retried next pass, and local
  notification channels (`--notify`, e.g. the farm-automation webhook)
  fire on-site regardless.
- The cloud keeps, per agent: the **latest snapshot** (plus a history
  of 100) and the **last 5000 events**. A site is shown **stale**
  ("Mất tín hiệu") when its agent has not reported for more than
  3× its scan interval (interval is reported by the agent itself).

## Quickstart

```bash
# 1) Start the cloud (on a VPS, or any always-on host):
BEESKY_CLOUD_PASSWORD='mật-khẩu-của-bạn' \
  python -m beesky cloud --host 0.0.0.0 --port 8788 --db beesky-cloud.db

# 2) Register one agent per site — the key is printed ONCE:
python -m beesky cloud-add-agent --db beesky-cloud.db --site "Xưởng 1"
#    -> BEESKY_AGENT_KEY=<key>   (save it now; only its SHA-256 is stored)

# 3) At the farm, run the agent (same scan options as scan/watch):
python -m beesky agent 192.168.1.0/24 \
  --cloud https://cloud.example.com \
  --key <key-vừa-tạo> --site "Xưởng 1" --interval 30
#    (the key can also come from the BEESKY_AGENT_KEY env var)

# 4) Open http://<cloud>:8788/ , log in with the password from step 1.
```

With Docker (cloud only — the agent belongs inside the farm LAN, e.g.
as the packaged exe on a workshop PC):

```bash
BEESKY_CLOUD_PASSWORD='mật-khẩu-của-bạn' docker compose up -d beesky-cloud
# -> http://<host>:8788 ; the db lives in the beesky-cloud-data volume
```

## API

Agent side — `Authorization: Bearer <agent-key>` (or `X-Agent-Key`):

| Route | Body → Result |
|-------|---------------|
| `POST /api/ingest` | `{"site", "ts", "interval", "miners": [records]}` → stores the snapshot, marks the agent seen |
| `POST /api/ingest/events` | `{"site", "ts", "events": [engine events]}` → stores the events |
| `GET /api/agent/commands?limit=` | claims this agent's pending remote actions (v0.6, see docs/actions.md) |
| `POST /api/agent/commands/{id}/result` | `{"status": "done"\|"failed", "result": "..."}` → finishes an own command (403 for another agent's) |

Viewer side — session cookie after `POST /login`:

| Route | Returns |
|-------|---------|
| `GET /` | Multi-site dashboard: per-site cards (online/stale, miners, TH/s, problems), miners table with a Site column, global events feed; click a site (or use the dropdown) to filter |
| `GET /api/sites` | `[{site, agent_id, last_seen_at, online, miner_count, ok_count, problem_count, total_ths, max_temp}]` |
| `GET /api/miners?site=` | Latest records (all sites merged when `site` is omitted), each annotated with `"site"` |
| `GET /api/events?n=&site=` | Stored events, newest first |
| `POST /api/commands` | `{"site", "ip", "type", "payload"}` → queue a remote action (reboot, switch_pool) for that site's agent — v0.6, see docs/actions.md |
| `GET /api/commands?n=&site=` | Remote-action history, newest first |

## Security notes

- **Agent keys** are per-site bearer tokens (`secrets.token_urlsafe(32)`,
  minted by `cloud-add-agent`). The cloud stores only their SHA-256
  hash, so a leaked database does not leak usable keys. A compromised
  key can only push fake data for its own site; revoke it by deleting
  the agent's row from the `agents` table and minting a new one.
- **Viewer password** is a single admin password from the environment
  variable `BEESKY_CLOUD_PASSWORD`; login sets an in-memory,
  HttpOnly session cookie (24 h). If the variable is unset the viewer
  is **open** and startup prints a loud warning — fine for a local
  test, never for deployment.
- **HTTPS is the deployer's job**: run the cloud behind a reverse
  proxy (Caddy/nginx/…) with TLS. Without it, agent keys and the
  viewer password travel as plain HTTP. Agent keys only ever travel
  in the `Authorization` header of the agent's own posts.
- The cloud binds `127.0.0.1` by default; `--host 0.0.0.0` (as in the
  compose file, inside the container) is the explicit opt-in.

## One binary, all roles

The **same Windows installer exe** contains every command — `scan`,
`watch`, `serve`, `agent`, `cloud`, `cloud-add-agent` — because all of
it is the same stdlib-only package (the two dashboard HTML pages are
bundled into the exe as data files; see `packaging/beesky.spec`). A
workshop PC can be the farm agent today and the cloud host tomorrow
with no extra installs.
