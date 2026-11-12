# BeeSky real cloud backend — first slice

## Run locally

From the repository root (Python 3.12 recommended):

```powershell
python -m pip install -r cloud_service/requirements.lock
python cloud_service/dev_setup.py
docker compose -f cloud_service/compose.yaml up -d --build
```

- App: http://127.0.0.1:8793/
- Local email inbox: http://127.0.0.1:8026/
- Readiness: http://127.0.0.1:8793/health/ready
- Existing preview: http://127.0.0.1:8790/ (independent legacy backend).

The setup generates private `.env` secrets; never commit this file. PostgreSQL stores data in a separate named volume. Restarting containers preserves data. `down` preserves the volume; do not use `down -v` for operational data. No seeded accounts: register, open the local verification email, log in, then create an organization and its first site.

## Implemented

Django 5.2 LTS / DRF, PostgreSQL, versioned migrations, Argon2 passwords, email verification, reset and password change, revocable database sessions, CSRF including anonymous forms, owner/admin/viewer permissions, organization isolation checked on every request, invitations, sites, agent key creation/rotation/revocation, miner telemetry, racks/slots, placement/detachment with reason, and audit history.

Agent keys are only shown at issuance; only their hashes are stored. The key determines the site regardless of a payload's claimed site. Serial/MAC supplies reported identity; IP-only identities need explicit confirmation for placement. A new serial at an existing IP does not inherit the previous machine's slot. Placement transactions and database triggers prevent cross-site placement and concurrent occupation of one slot. Raw telemetry is retained in bounded snapshot history (100 snapshots per agent), not a long-term time-series archive.

Mail uses an encrypted durable outbox with retries. Token digests are stored separately, links carry tokens in URL fragments, and sent outbox payloads are cleared. Local SMTP terminates in Mailpit, not external recipients. Email delivery is at least once.

## API

Browser APIs use `/api/v2`, JSON, same-origin session cookies and `X-CSRFToken`. Fetch `GET /auth/csrf` first. List endpoints use bounded `limit`/`offset` where supported. Paths below omit `/api/v2`.

| Area | Routes |
| --- | --- |
| Accounts | `GET /auth/me`, `POST /auth/register`, `/auth/verify`, `/auth/resend`, `/auth/login`, `/auth/logout`, `/auth/forgot`, `/auth/reset`, `/auth/password` |
| Sessions | `GET/POST /auth/sessions` |
| Organizations | `POST /organizations`, `/organizations/select` |
| Membership | `GET /members`, `PATCH/DELETE /members/{id}`, `POST /invitations`, `/invitations/accept` |
| Sites | `GET/POST /sites`, `GET/PATCH /sites/{id}` |
| Agents | `GET/POST /sites/{id}/agents`, `POST/DELETE /sites/{id}/agents/{agentId}` (rotate/revoke) |
| Miners | `GET /sites/{id}/miners`, `/sites/{id}/miners/{minerId}`, `POST /sites/{id}/miners/{minerId}/placement` |
| Racks | `GET/POST /sites/{id}/racks`, `PATCH/DELETE /sites/{id}/racks/{rackId}` |
| Monitoring | `GET /overview`, `/audit` |

Agent contract: `POST /api/ingest` accepts `{ts, miners:[{ip, model, mac_or_serial, power_w, max_temp_c, ...}]}` with `Authorization: Bearer <agent key>` (or `X-Agent-Key`). `POST /api/ingest/events` receives events. Retries are deduplicated; older telemetry cannot overwrite newer readings. `GET /api/agent/commands` returns an empty queue with control disabled. No physical command dispatcher is enabled.

## Verification

24 automated tests passed on PostgreSQL, including organization isolation, CSRF, roles, token replay, session revocation, ingest identity/retry rules, database placement guards and a real two-thread placement race. Browser walkthrough passed registration, Mailpit verification, login, onboarding, agent issuance, synthetic telemetry, rack creation and persisted placement after reload. No real miner hardware was used. Mobile checked at 390px.

CI runs PostgreSQL tests, schema drift checks and Django system checks. To run locally, install `requirements.lock`, provide a dedicated PostgreSQL database URL and set `BEESKY_TESTING=1`; run `python cloud_service/manage.py test core.tests`. Django creates a separate test database; the database user needs permission to create it.

## Remaining work

This is the first working backend slice. Power network/phase calculations, maintenance/photos/reports, customer/worker grouping, 2D/3D layout editing and workflows still use the legacy preview and are not yet migrated to the tenant service. No old SQLite data is imported automatically: a later importer must require an explicit owner/site mapping, read-only dry run and reconciliation. MFA, hardware control, production backup/restore, observability and fleet-scale tuning remain separate work.

Before public deployment configure a real HTTPS domain, `BEESKY_DEBUG=0`, allowed hosts/CSRF origins, private PostgreSQL, external SMTP, private keys, backup and restore procedures. Startup fails closed without required secrets/PostgreSQL/HTTPS configuration. Compose is local-only; it does not deploy or secure a public reverse proxy. Do not expose Mailpit publicly. Keep the old preview separate from authenticated traffic.

