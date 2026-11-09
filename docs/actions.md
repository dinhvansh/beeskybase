# BeeSky remote actions (v0.6) — lệnh từ xa qua cloud

The cloud can never reach into a farm LAN, so a remote action rides
the channels that already exist: the viewer issues a command on the
cloud, the site's agent picks it up on its next poll, executes it
against the miner on the farm LAN, and reports the result back.

```
 browser (đã đăng nhập)          cloud                      agent tại trại           miner
 ──────────────────────          ─────                      ──────────────           ─────
 POST /api/commands ───────────▶ commands row (pending)
 GET  /api/commands ◀─────────── history + trạng thái
                                  GET /api/agent/commands ◀── agent poll mỗi vòng quét
                                  (claim nguyên tử ─ pending → sent)
                                                             execute (LAN) ─────────▶ reboot /
                                                                                      switch-pool
                                  POST /api/agent/commands/{id}/result ──▶ (done|failed + result text)
```

Command lifecycle: `pending` (vừa tạo) → `sent` (agent đã nhận,
đang chạy) → `done` | `failed`. The result text is whatever the
miner's own API answered — a refusal is stored verbatim, never
dressed up as a success.

## Flow chi tiết

1. **Viewer** (logged in with the cloud password) presses
   *Khởi động lại* on a miner row, or POSTs directly:
   `POST /api/commands {"site", "ip", "type", "payload"}` → `201`.
   The site name resolves to that site's registered agent.
2. **Agent**, at the end of every scan pass: first redelivers any
   queued results, then `GET /api/agent/commands?limit=5` — the
   claim is atomic, so a command is handed to exactly one poll, and
   at most 5 commands execute per pass.
3. The agent resolves the miner's **source** from the pass's fresh
   scan records (falling back to a live probe of that one IP), then
   runs the executor with the same credentials/ports its scan
   adapters use (`--user/--password`, `--api-key/--token`,
   `--http-port/--cgminer-port`).
4. The agent POSTs `{status, result}` to
   `/api/agent/commands/{id}/result`. If the cloud is unreachable the
   result is queued (bounded) and redelivered next pass — the
   execution itself already happened on-site and is never repeated
   just because the report got lost. (A command claimed by an agent
   that then dies stays `sent`; reap those by hand for now.)

## Support matrix

| Lệnh | cgminer RPC | dashd (VNish/HashCore) | stock Bitmain |
|------|-------------|------------------------|---------------|
| `reboot` | ✔ qua RPC `restart` — **xem caveat bên dưới** | ✔ `POST /api/v1/system/reboot` | ✔ `GET /cgi-bin/reboot.cgi` (digest auth) |
| `switch_pool` | ✘ chưa hỗ trợ (trả `failed`: "not supported for this source yet") | ✔ — xem bên dưới | ✘ chưa hỗ trợ |

dashd `switch_pool` has two documented forms (from the firmware's own
`api-doc.json`):

- `{"pool_id": N}` → `POST /api/v1/mining/switch-pool` — activates
  the already-configured pool slot N. It does **not** take a new
  url/user; the endpoint's body is exactly `{pool_id}`.
- `{"url": ..., "user": ..., "password": ..., "pool_id": 0}` →
  `GET /api/v1/settings`, rewrite `miner.pools[pool_id]`,
  `POST /api/v1/settings`, then activate via `/mining/switch-pool`.
  Caveat from the doc: `GET /settings` accepts **only** an
  `x-api-key` (apikeyAuth), so this form needs the agent started
  with `--api-key`; without one the command fails with that
  explanation instead of guessing.

dashd write endpoints need a bearer JWT or an API key. The agent
passes `--api-key` / `--token` straight through; with only a
password it first mints a JWT via `POST /api/v1/unlock`
(`{"pw": ...}`), the same flow the firmware UI uses.

## Caveat: cgminer write access

The cgminer `restart` command is *privileged*. Most Antminer units
ship their API **read-only** (no `W:` grant in `api-allow`), and they
refuse with `STATUS E` — e.g. `Access denied`. BeeSky surfaces that
reply verbatim as the command's failure result; the command is
**not** reported as done. To make cgminer reboots actually work on a
unit, its API must be provisioned writable (on stock Bitmain
firmware that is a firmware-level setting, not something a fleet
tool can grant itself remotely).

## Security

- Commands can only be **created** by the logged-in viewer
  (`POST /api/commands` sits behind the same session gate as the
  other viewer APIs; without login → 401).
- An **agent** can only claim and finish **its own site's** commands:
  the claim query is scoped to the agent's id, and
  `POST /api/agent/commands/{id}/result` answers **403** when the
  command belongs to another agent (404 for unknown ids, 409 when
  already finished). Agent keys are the same per-site SHA-256-hashed
  bearer keys as ingest (see docs/cloud.md).
- Executors receive only the miner IP/source/type/payload plus the
  agent's own adapter credentials — a command payload can never
  smuggle in credentials or a different target.
- Every command and its result stay in the cloud's `commands` table
  (newest 5000) and on the dashboard's *Lệnh gần đây* panel — who
  asked, which miner, what the miner answered.

## Thêm loại lệnh mới

Add one handler in `beesky/core/actions.py`, register its name in
`COMMAND_TYPES`, and the cloud/agent/dashboard plumbing already
carries it — no protocol change needed.
