# Deploy BeeSky real backend

This deploys `cloud_service`, not the legacy preview or the old deploy-cloud workflow. Public deployment target: `https://mine.beeskybase.com` (existing proxy setup below). The current release supports account isolation, telemetry, 2D/3D layout, power planning, customer/groups, maintenance evidence/approval, repairs and server-evaluated alert rules. Rules create in-app alerts only; they do not dispatch physical commands or external webhooks.

## VPS preparation

Linux VPS with Docker Compose v2, a DNS domain pointing to its IP, and ports 80/443 available. PostgreSQL and the application are only on the private Compose network. Caddy handles HTTPS. Use a separate private directory/volume from any old BeeSky deployment.

```sh
git clone https://github.com/dinhvansh/beeskybase.git /opt/beesky-next
cd /opt/beesky-next
git checkout feat/cloud-accounts-preview
python3 -m venv .venv
.venv/bin/pip install -r cloud_service/requirements.lock
.venv/bin/python cloud_service/production_setup.py --domain cloud.example.com --smtp-host smtp.example.com --from-email no-reply@example.com
```

Edit **only the private** `cloud_service/.env.production`: set SMTP username/password and confirm provider port/TLS (default STARTTLS 587). Keep generated keys and database password unchanged across upgrades. Values with `$` should be single-quoted using Compose env-file syntax. Never commit or paste the configuration into issue logs. The generator refuses to overwrite an existing file.

```sh
docker compose --env-file cloud_service/.env.production -f cloud_service/compose.production.yaml config --quiet
docker compose --env-file cloud_service/.env.production -f cloud_service/compose.production.yaml up -d --build
docker compose --env-file cloud_service/.env.production -f cloud_service/compose.production.yaml ps
curl --fail https://cloud.example.com/health/ready
```

Open the domain, register your own account, follow the verification email, log in, create your organization/site, then create an agent key for that site. There are no default passwords or demo accounts. Local QA accounts belong only to the local development database. Keep Mailpit local; production uses the configured external SMTP server.

`BEESKY_TRUST_PROXY=1` is only for the included private web service behind Caddy, which replaces `X-Real-IP`; do not expose the application port directly with this setting. HTTPS forwarded headers are trusted only in that deployment configuration. The ready endpoint checks the required schema; it does not certify mail delivery or an operational miner.

## Agent test

Create a dedicated test workshop/key first. Set `BEESKY_AGENT_KEY` as a private environment variable on the agent computer. Do not commit it or paste it in screenshots. From the repo root:

```sh
python tools/check_cloud_agent.py --url https://cloud.example.com
# Explicit synthetic telemetry test, only in your dedicated test workshop:
python tools/check_cloud_agent.py --url https://cloud.example.com --send-fixture
```

The checker calls the existing agent transport functions. It validates agent authentication/control-disabled response, then optionally posts one **synthetic** test miner, a retry and an event. It does not scan a network or issue commands. The test miner is labeled `BEESKY-CONNECTION-CHECK-ONLY` and uses documentation IP `192.0.2.21`.

Then start your normal agent on the farm LAN with its real target range, the HTTPS cloud URL and the site's issued key. Existing CLI syntax:

```text
python -m beesky agent <target> --cloud https://cloud.example.com --key <site-agent-key> --site <site-label> --interval 30 --once
```

For routine operation prefer the agent UI's private configuration rather than pasting the literal key into shell history. The server determines site from the key, not `--site`. First run `--once`, verify IP/model/serial/worker/power in the web app, then run continuously. Only actual hardware testing can verify model adapter support. Remote reboot/pool changes remain disabled in this release.

## Backup and upgrades

Photos and maintenance records are stored in PostgreSQL and included in the dump. Preserve the private `.env.production` separately with restricted access: the mail encryption key is required for pending outbox messages.

```sh
# Supply an existing, restricted directory on a separate disk/storage path:
sh cloud_service/backup.sh /private/beesky-backups
```

The backup script uses a private file mode, custom-format pg_dump and validates archive readability before renaming. It does not schedule backups or copy them off the VPS; configure that separately before relying on the service. Never use Compose `down -v` for an operational database.

Upgrade: create/verify backup, `git pull --ff-only`, then repeat `up -d --build` and readiness check. Migrations run before the web becomes ready. If an upgrade fails, preserve volumes and inspect logs; do not roll back schema blindly. Restore into a **new empty database** using `pg_restore --exit-on-error --no-owner`, verify account login, placement, photos and counts before routing users to it. This procedure must be rehearsed against your VPS backup storage.

## Scope and limits

- New cloud data is real and tenant-scoped. Old preview SQLite is not automatically imported. A later explicit migration needs an owner/site mapping and reconciliation, so old data cannot silently become another customer's data.
- Monthly maintenance sheets are generated for the current month even with no browser open. Each report freezes its checklist; every item needs before/after evidence to submit. Only owners approve/reject; approved evidence is immutable through the API.
- Power calculations are capacity planning, not metered kWh. Only placed machines count. Fresh measured watts and explicit/catalog ratings are distinguished; unknown variants are flagged. ABC divides load equally and requires actual 3-phase hardware. Phase currents/imbalance need physical measurement confirmation.
- Alerts run every 30 seconds server-side. Surges compare fresh measured power (>20% and at least 100 W increase), remain for 10 minutes. Rules support temperature, watts and stale minutes. No arbitrary workflow execution, remote control or external notifications are enabled.
- Snapshot history retains 100 snapshots per agent. This is not long-term energy/time-series billing storage. MFA, fleet-scale indexing/partitioning and external alarm delivery are future work.

## Existing Nginx Proxy Manager deployment

For `mine.beeskybase.com`, the VPS already owns ports 80/443 through Nginx Proxy Manager. Apply `cloud_service/compose.npm.yaml` after the production file and use project `beesky-mine`. It disables the standalone Caddy service and exposes the web container only on the existing external proxy network (default `eoffice_proxy`), as `beesky-mine-web:8000`. The new database and worker stay on their own network.

```sh
docker compose -p beesky-mine --env-file /opt/beesky-mine/shared/.env.production -f cloud_service/compose.production.yaml -f /opt/beesky-mine/shared/compose.npm.yaml up -d --build db web worker
```

The proxy template is `cloud_service/nginx-mine.conf.example`. Install it through the existing proxy's supported custom HTTP include, validate with `nginx -t`, then reload. It replaces forwarded IP/protocol headers and uses Docker DNS to survive web container replacement. TLS uses a dedicated certificate for this domain; keep its ACME webroot reachable on port 80 and schedule renewal with a validated reload hook.

Release source: `/opt/beesky-mine/releases/2715077`. Private configuration: `/opt/beesky-mine/shared/.env.production`, linked into the release; no production secret belongs in Git. The archive deployment records its source commit; it does not depend on private GitHub credentials on the VPS. SMTP must be configured before users can receive verification/password reset emails; a DNS placeholder is not a mail service.

When using the backup script for this project, set `BEESKY_COMPOSE_PROJECT=beesky-mine`; otherwise its default project is the standalone installation. Preserve database backups and the private encryption keys independently of release source.

Operational certificate renewal on this VPS is installed as `beesky-mine-certificate.timer` (twice daily with jitter). It renews only the dedicated `beesky-mine` certificate and validates Nginx before reload. Proxy configuration backups and deployment logs are retained in `/opt/beesky-mine/shared`. SMTP is pending account/domain verification; the placeholder `smtp.invalid` intentionally cannot deliver mail.

Deployment verified on 2026-11-13: public HTTPS readiness, secure cookies/CSRF, isolated test login/onboarding, actual agent transport with snapshot retry deduplication and events, persisted rack placement/power, 3D static assets and revoked-key rejection. Temporary test user/site/agent data was removed. An initial PostgreSQL dump was created and its archive list validated under `/opt/beesky-mine/backups`. This does not verify physical miner adapters or mail delivery; SMTP account/domain setup remains pending.
