# Handoff — BeeSky Cloud Web (for Codex)

**Task:** take the BeeSky cloud website live on a VPS, end to end.
**Baseline:** repo `github.com/dinhvansh/beeskybase` (private), GitHub `main`
at v0.21.0 (`f0ccaed`). The cloud/web code in this package is byte-identical
to that commit. (Newer local work — v0.22/v0.23 desktop-app changes — does
not touch the cloud or web code and is not part of this handoff.)

## What the "web" is (two different things — don't confuse them)

1. **Cloud** (`beesky/cloud/`) — the multi-site dashboard. One stdlib-Python
   process + SQLite. Farm-side **agents dial out to it** (no inbound ports at
   farms): they POST miner snapshots, receive remote commands on their next
   poll. This is the thing that belongs on a VPS.
   - `server.py` HTTP server + API, `store.py` SQLite store, `pools.py`
     pool hashrate poller, `dashboard.html` the whole UI (single file).
   - Viewer login: a single password from env `BEESKY_CLOUD_PASSWORD`
     (if empty, the viewer is OPEN and startup prints a loud warning).
   - Agent access: per-agent keys, minted/revoked in the dashboard's agent
     section; only SHA-256 hashes are stored server-side.
2. **Local web** (`beesky/web/`) — single-site dashboard that scans the LAN
   it runs on. Useful at a farm, useless on a VPS. Not part of this deploy
   except that the same Docker image can run it (`beesky-web` service).

Reference docs included: `code/docs/cloud.md` (cloud behaviour + API),
`code/docs/cd-deploy.md` (the CD setup, step by step), `code/docs/web.md`,
`code/docs/agent-app.md` (how farm agents are installed + pointed at the
cloud).

## Deploy path A — GitHub Actions CD (preferred)

Workflow: `code/.github/workflows/deploy-cloud.yml` (already in the repo).
Its build-check half runs on every cloud-touching push and is green; the
deploy half is gated and has never run. One-time setup (details in
`cd-deploy.md`):

1. VPS: any small Linux box with public IP; install Docker + compose plugin
   + git. Create deploy user `beesky`, add to `docker` group.
2. Dedicated ed25519 deploy keypair: public half →
   `~beesky/.ssh/authorized_keys` on the VPS; private half → GitHub secret.
3. On the VPS as `beesky`: clone the repo to `/opt/beesky`, create `.env`
   with `BEESKY_CLOUD_PASSWORD=<strong password>` (`chmod 600 .env`).
   The workflow refuses to deploy without this file — by design.
4. GitHub repo settings → Secrets and variables → Actions:
   - Variable: `BEESKY_DEPLOY_ENABLED` = `true`
   - Secrets: `BEESKY_VPS_HOST`, `BEESKY_VPS_USER` (= `beesky`),
     `BEESKY_VPS_SSH_KEY` (the deploy private key)
   - Optional: `BEESKY_VPS_PORT` (default 22), `BEESKY_VPS_PATH`
     (default `/opt/beesky`)
5. Push anything cloud-touching to `main` (or re-run the workflow): it SSHes
   in, checks out the triggering commit, rebuilds `beesky-cloud`, and
   health-checks it. Deploys are serialised, never cancelled mid-run.

## Deploy path B — manual (fallback / first smoke test)

```bash
# on the VPS, as the deploy user:
git clone https://github.com/dinhvansh/beeskybase.git /opt/beesky
cd /opt/beesky
printf 'BEESKY_CLOUD_PASSWORD=<strong password>\n' > .env && chmod 600 .env
docker compose up -d --build beesky-cloud
# update later: git pull && docker compose up -d --build beesky-cloud
```

Cloud listens on **8788**; local web (if run) on **8787**. Data persists in
the `beesky-cloud-data` volume (`/data/beesky-cloud.db` inside the container).

## Verification checklist (what "done" means)

- [ ] `docker compose ps` shows `beesky-cloud` up; logs show no open-viewer
      warning (password set).
- [ ] `http://<vps>:8788` loads the login page; the password logs in.
- [ ] In the dashboard's agent section, mint one agent key.
- [ ] From any machine on a farm LAN, run a BeeSky agent pointed at the
      cloud URL with that key → the site appears in the dashboard with live
      miners within one poll cycle.
- [ ] HTTPS in front (domain + reverse proxy, e.g. Caddy/nginx, or a
      Cloudflare tunnel) — until then agent keys travel over plain HTTP;
      treat pre-HTTPS as smoke-test only.
- [ ] CD path verified: one no-op cloud-touching commit to `main` deploys
      cleanly via Actions.

## Secrets inventory (names only — no values exist in this package)

| Where | Name | Purpose |
|---|---|---|
| VPS `/opt/beesky/.env` | `BEESKY_CLOUD_PASSWORD` | dashboard viewer login |
| GitHub secret | `BEESKY_VPS_HOST` / `BEESKY_VPS_USER` / `BEESKY_VPS_SSH_KEY` | CD deploy access |
| GitHub variable | `BEESKY_DEPLOY_ENABLED` | master switch for the deploy job |

## Notes / gotchas

- The repo is private: the first VPS clone needs the owner's GitHub access;
  afterwards the workflow only fetches in place.
- The cloud scans nothing itself — if the dashboard is empty, the problem
  is agents (not deployed / wrong cloud URL / revoked key), not the cloud.
- Pool-gap alerts need a pool stats URL configured per site in the
  dashboard settings; the generic JSON adapter is the supported shape.
- Feature history and test evidence live in the repo's `RESULTS.md`
  (not included; ask the owner or read it in the repo if needed).
