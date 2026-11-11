# BeeSky cloud CD — tự động deploy lên VPS bằng GitHub Actions

Workflow `.github/workflows/deploy-cloud.yml` does two things:

1. **Build check (always on, no secrets needed).** Every push to
   `main` that touches the cloud (`beesky/cloud/**`, the root
   `Dockerfile`, `docker-compose.yml`, …) builds the `beesky-cloud`
   Docker image on a GitHub runner and throws it away. A broken image
   fails here — never on the VPS.
2. **Deploy (opt-in).** Only when the repo variable
   `BEESKY_DEPLOY_ENABLED` is `true`, a second job SSHes into the VPS,
   checks out **the exact commit that triggered the run**, rebuilds
   the `beesky-cloud` service and health-checks it. Until the variable
   is set, the deploy job is skipped cleanly and the workflow is just
   a build check.

Deploys are serialised (concurrency group `deploy-cloud`) and never
cancelled halfway — a half-finished deploy is worse than a queued one.

## Anh cần chuẩn bị MỘT LẦN (one-time setup)

### 1. Một VPS

Any small Linux VPS with a public IP is enough (the cloud is one
stdlib Python process + SQLite). On the VPS install:

- Docker + the `docker compose` plugin
- `git`

Create a **dedicated deploy user** (e.g. `beesky`) and put it in the
`docker` group, so the workflow never needs root:

```bash
sudo useradd -m -s /bin/bash beesky
sudo usermod -aG docker beesky
```

Generate a **dedicated SSH keypair for deploys only** (on your own
machine, not a key you use for anything else):

```bash
ssh-keygen -t ed25519 -f beesky-deploy -C "beesky cloud deploy"
# public half -> VPS:  ~beesky/.ssh/authorized_keys
# private half -> GitHub secret BEESKY_VPS_SSH_KEY (step 3), then
#                 delete the local copy or keep it somewhere safe
```

### 2. Trên VPS: clone + file `.env` (one time, by hand)

The repo is private, so the first clone needs *your* GitHub access
(your PAT or your own SSH key on the VPS). After this one clone, the
workflow only ever runs `git fetch` + `git checkout` in place.

```bash
# as the deploy user, on the VPS:
git clone https://github.com/dinhvansh/beeskybase.git /opt/beesky
cd /opt/beesky
printf 'BEESKY_CLOUD_PASSWORD=<mật-khẩu-xem-web>\n' > .env
chmod 600 .env
```

`BEESKY_CLOUD_PASSWORD` is the cloud viewer password (see
`docs/cloud.md`). The `.env` file is **untracked**, so no
`git checkout` in any deploy can overwrite it — and the workflow
double-checks: if `.env` is missing or has no password, the deploy
aborts with instructions instead of starting an open viewer.

### 3. Trong GitHub repo: Variables + Secrets

Repo → **Settings → Secrets and variables → Actions**:

**Variables** tab (configuration — visible, not credentials):

| Name | Value |
|------|-------|
| `BEESKY_DEPLOY_ENABLED` | `true` ← this is the on/off switch for deploys |
| `BEESKY_VPS_PATH` | *(optional)* default `/opt/beesky` |
| `BEESKY_VPS_PORT` | *(optional)* default `22` |

**Secrets** tab (credentials — write-only, masked in logs):

| Name | Value |
|------|-------|
| `BEESKY_VPS_HOST` | VPS public IP or hostname |
| `BEESKY_VPS_USER` | the deploy user, e.g. `beesky` |
| `BEESKY_VPS_SSH_KEY` | the **private** half of the deploy keypair from step 1 |
| `BEESKY_VPS_PORT` | *(optional alternative)* SSH port, if you prefer it secret; the variable of the same name wins when both are set |

If `BEESKY_DEPLOY_ENABLED=true` but a required secret is missing, the
deploy job fails in its first step and **names the missing secret** —
it never dies halfway with a cryptic SSH error.

## Sau khi setup xong: deploy tự chạy

Every push to `main` touching the cloud paths (or a manual
**Actions → BeeSky Cloud CD → Run workflow**) then does:

```
build image on runner (validation)
  → ssh to VPS
  → git fetch + checkout <exact commit SHA of this run>
  → guard: .env + BEESKY_CLOUD_PASSWORD present?
  → docker compose up -d --build beesky-cloud     # cloud service only
  → health check: curl http://127.0.0.1:8788/ for up to ~60 s
       (200/302/401/403 = up; the unauthenticated 302 → /login is by design)
  → on failure: compose ps + last 100 log lines are printed in the run
```

Only the `beesky-cloud` service is deployed — `beesky-web` is the
farm-LAN scanner and does **not** belong on a VPS (see
`docs/cloud.md`). The cloud's SQLite database lives in the
`beesky-cloud-data` Docker volume, so redeploys never touch the data.

## Rollback

The workflow always deploys the commit that triggered the run; there
is no "deploy an older commit" button. To roll back, either:

- **Push a revert** to `main` (`git revert <bad-commit>`) — the
  normal path; CI + CD rerun and the VPS lands on the reverted tree, or
- **By hand on the VPS**:

  ```bash
  cd /opt/beesky
  git checkout <older-sha>
  docker compose up -d --build beesky-cloud
  ```

  (The next automated deploy will move it forward again to that
  run's commit.)

## Security notes

- **Dedicated user + dedicated key.** The deploy key exists only as
  this repo's `BEESKY_VPS_SSH_KEY` secret and in the deploy user's
  `authorized_keys` — nowhere else. Leaked repo secrets therefore buy
  an attacker exactly one thing: redeploying this repo's own cloud
  service as the unprivileged `beesky` user. Revoke by removing the
  public key from `authorized_keys` and rotating the secret.
- On the runner, the private key is written `0600`, used for one job,
  and shredded (`shred -u`) in an `always()` step.
- The VPS host key is fetched with `ssh-keyscan` at deploy time
  (trust-on-first-use per run). For stricter pinning, verify the
  fingerprint printed by your VPS provider against
  `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the VPS once —
  if they ever differ, treat it as a red flag, not a nuisance.
- The deploy job checks out code and restarts a container; it never
  receives the cloud password (that stays in the VPS `.env`) and
  never touches agent keys (those live in the cloud DB volume).
- **HTTPS is still your job** (unchanged from `docs/cloud.md`): put
  the cloud behind Caddy/nginx with TLS on the VPS before real use —
  this workflow deploys the app, not the proxy.
