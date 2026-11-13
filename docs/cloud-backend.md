# BeeSky real cloud backend

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

35 automated tests passed on PostgreSQL, including organization isolation, CSRF, roles, token replay, session revocation, ingest identity/retry rules, database placement guards and a real two-thread placement race. Browser walkthrough passed registration, Mailpit verification, login, onboarding, agent issuance, synthetic telemetry, rack creation and persisted placement after reload. No real miner hardware was used. Mobile checked at 390px. Added walkthroughs for station persistence, Three.js scene loading, checklist/image persistence and the actual agent transport (synthetic snapshot + retry + event + revoked-key rejection). Physical miner adapters have not been tested on hardware.

CI runs PostgreSQL tests, schema drift checks and Django system checks. To run locally, install `requirements.lock`, provide a dedicated PostgreSQL database URL and set `BEESKY_TESTING=1`; run `python cloud_service/manage.py test core.tests`. Django creates a separate test database; the database user needs permission to create it.

## Operational modules added

Tenant-scoped `GET/PUT /sites/{id}/plan` uses revision checks and validates all rack/miner/branch references. `GET /sites/{id}/power` calculates station/cabinet/branch/phase loads server-side. `GET /sites/{id}/layout` returns the real fleet/placements; rack edits persist floor/X/Z/90-degree rotation and reject overlaps. `/customers`, site `/groups`, miner `/assignment` persist ownership, cooling group and condition. Worker names come from telemetry.

Site `/maintenance/schedules`, `/maintenance/tickets`, ticket `/photos` and `/maintenance/photos/{id}` provide monthly checklists, revision protection, authenticated image evidence and submit/owner approval/rejection. JPEG/PNG/WebP images are decoded, size-limited and re-encoded as JPEG to discard metadata/active content. Photos are stored in PostgreSQL. The browser's report view supports printing/saving PDF. Site `/repairs` tracks failure/resolution and condition.

Site `/rules`, `/alerts`, alert `/acknowledge` and `/events` expose server-evaluated alerts and agent events. Rules support temperature, measured power and stale minutes; no physical commands or arbitrary workflow nodes. The worker runs independently of the browser, every 30 seconds for alerts and current-month tickets.

Production Compose/HTTPS, setup and agent checks: see [cloud-deployment.md](cloud-deployment.md). No public deployment performed; hardware agent testing and SMTP/domain setup remain for the selected server. No implicit old-SQLite import, MFA or remote command dispatcher is enabled. Existing preview remains separate.
