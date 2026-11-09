# BeeSky — ASIC miner LAN scanner & repair diagnostics

BeeSky is a small, dependency-free tool for ASIC repair shops. It scans a local
network for miners, reads their health over whichever API the firmware
exposes — the classic **cgminer RPC API (TCP 4028)**, the **VNish/HashCore
dashd HTTP API**, or **Bitmain stock web CGI** (digest auth) — and turns the
raw numbers into something a repair tech can act on: a status table and, for
every sick miner, a plain-text **repair ticket** (Vietnamese) with per-board
details and suggested checks.

Fleet tools (e.g. HashCore Toolkit) stop at generic dashboards and exports.
BeeSky's focus is the repair bench: *which board, how many chips down, how hot,
and what to check first.*

Pure **Python 3 standard library** — no pip installs, runs anywhere Python 3
does (Windows / macOS / Linux), fully offline, no analytics, no phone-home.

## Usage

```bash
# Scan one miner
python -m beesky scan 192.168.1.50

# Scan a subnet or an IP range
python -m beesky scan 192.168.1.0/24
python -m beesky scan 192.168.1.10-192.168.1.60

# Save machine-readable results and repair tickets
python -m beesky scan 192.168.1.0/24 --json out.json --tickets tickets/

# Non-default credentials (stock web UI / dashd), non-standard ports
python -m beesky scan 192.168.1.0/24 --user root --password <pw> \
    --api-key <dashd-key> --http-port 80 --cgminer-port 4028
```

Example output (note the **Source** column — which adapter read the miner):

```
IP            | Model            | Source  | TH/s   | Chips   | MaxTemp | Fans                | Status
--------------+------------------+---------+--------+---------+---------+---------------------+-------
192.168.1.50  | Antminer S19 Pro | cgminer | 110.02 | 342/342 | 71      | 4320/4380/4440/4500 | OK
192.168.1.51  | Antminer S19 Pro | vnish   | 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK
192.168.1.52  | Antminer S19     | stock   | 95.10  | 342/342 | 70      | 4200/4260/4320/4380 | OK

Found 3 miner(s), 1 need(s) checking.
```

### What gets flagged (`Status = CHECK`)

- a chain (hashboard) missing chips — dead-chip positions are listed
- a chain reporting **0 chips** (board down / not detected)
- any chain temperature **≥ 85 °C**
- hashrate **0** while the miner has been running > 300 s

For each flagged miner, `--tickets <dir>` writes one `ticket-<ip>.txt` with the
problems, per-board chip/temp detail, and repair suggestions in Vietnamese.

## How it works

Architecture mirrors the pattern used by mature fleet tools, kept minimal:

- **CLI core first** (`beesky/`): all logic lives in a scriptable core package;
  a GUI can be bolted on later without touching it.
- **Per-vendor adapters** (`beesky/core/`): the generic cgminer RPC client
  (`summary` / `stats` / `pools`); the VNish/HashCore **dashd** adapter,
  implemented against the firmware's own OpenAPI doc (`/api/v1/summary` +
  `/api/v1/boards` — per-chip grades included, so dead-chip *positions*
  survive); and the Bitmain **stock** adapter (web CGI + hand-rolled HTTP
  digest auth, stdlib only). WhatsMiner slots in beside them next.
- **Discovery**: for each host, walk the adapter chain in order — cgminer RPC
  **:4028** → dashd HTTP **:80** → stock CGI **:80** — and keep the first
  adapter that answers like a miner. Probing is threaded with bounded workers
  and short timeouts. HTTP adapters always connect directly (system proxy
  env vars are ignored — miners are LAN devices).
- **Normalised records** (`beesky/core/report.py`): every miner becomes one
  status record (JSON-friendly) plus a problems list; the CLI table, the JSON
  export, and the repair tickets are all rendered from that record.

## Mock tests

Fake miners are included so the whole pipeline can be verified with no
hardware — a sick cgminer S19 Pro, a sick VNish S19 Pro, and a healthy
stock-firmware S19 behind digest auth:

```bash
bash tests/run_mock_test.sh      # v0.1: cgminer only -> tests/RESULTS.md
bash tests/run_mock_test_v2.sh   # v0.2: all three adapters, appends to RESULTS.md
```

## Roadmap

- ~~v0.2 — VNish/HashCore dashd HTTP adapter (optional API-key/bearer auth)
  + Bitmain stock web adapter (digest auth); scan table gains a Source
  column.~~ **Done.**
- v0.3 — WhatsMiner (MicroBT API v2) adapter; scan history + before/after
  compare for repair verification; `devs` command for per-chain detail.
- Later — pool switch / reboot actions, signed self-update manifests,
  single-hashboard fixture tester integration.

## Layout

```
beesky/
  cli.py            # `python -m beesky scan ...`
  core/
    cgminer.py      # cgminer RPC client (TCP 4028)
    dashd.py        # VNish/HashCore dashd HTTP API adapter (/api/v1)
    bitmain.py      # Bitmain stock web CGI adapter (digest auth)
    discover.py     # target parsing + threaded adapter-chain probing
    report.py       # status records, problem rules, repair tickets
tests/
  mock_miner.py     # fake cgminer API server (S19 Pro sample data)
  mock_dashd.py     # fake VNish dashd server (api-doc-shaped S19 Pro)
  mock_bitmain.py   # fake stock-firmware server (digest auth, healthy S19)
  run_mock_test.sh  # v0.1 end-to-end mock test -> tests/RESULTS.md
  run_mock_test_v2.sh  # v0.2 three-adapter mock test (appends to RESULTS.md)
```
