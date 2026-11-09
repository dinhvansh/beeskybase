# BeeSky — ASIC miner LAN scanner & repair diagnostics

BeeSky is a small, dependency-free tool for ASIC repair shops. It scans a local
network for miners, reads their health over the classic **cgminer RPC API
(TCP 4028)**, and turns the raw numbers into something a repair tech can act
on: a status table and, for every sick miner, a plain-text **repair ticket**
(Vietnamese) with per-board details and suggested checks.

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
```

Example output:

```
IP            | Model           | TH/s   | Chips   | MaxTemp | Fans                | Status
--------------+-----------------+--------+---------+---------+---------------------+-------
192.168.1.50  | Antminer S19 Pro| 110.02 | 342/342 | 71      | 4320/4380/4440/4500 | OK
192.168.1.51  | Antminer S19 Pro| 102.90 | 339/342 | 88      | 4320/4380/4440/4500 | CHECK

Found 2 miner(s), 1 need(s) checking.
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
- **Per-vendor adapters** (`beesky/core/`): v0.1 ships one adapter — the generic
  cgminer RPC client (`summary` / `stats` / `pools`). Vendor-specific adapters
  (Bitmain stock web, VNish/HashCore dashd API, WhatsMiner) slot in beside it.
- **Discovery**: for each host in the target range, probe HTTP **:80** first,
  then the cgminer RPC port **:4028**; hosts answering the cgminer API are
  treated as live miners. Probing is threaded with bounded workers and short
  timeouts.
- **Normalised records** (`beesky/core/report.py`): every miner becomes one
  status record (JSON-friendly) plus a problems list; the CLI table, the JSON
  export, and the repair tickets are all rendered from that record.

## Mock test

A fake S19 Pro (3 dead chips on board 2, board 3 at 88 °C) is included so the
whole pipeline can be verified with no hardware:

```bash
bash tests/run_mock_test.sh   # writes tests/RESULTS.md
```

## Roadmap

- v0.2 — VNish/HashCore dashd HTTP adapter (token/API-key auth) + Bitmain
  stock web adapter (digest auth); `devs` command for per-chain detail.
- v0.3 — WhatsMiner (MicroBT API v2) adapter; scan history + before/after
  compare for repair verification.
- Later — pool switch / reboot actions, signed self-update manifests,
  single-hashboard fixture tester integration.

## Layout

```
beesky/
  cli.py            # `python -m beesky scan ...`
  core/
    cgminer.py      # cgminer RPC client (TCP 4028)
    discover.py     # target parsing + threaded :80/:4028 probing
    report.py       # status records, problem rules, repair tickets
tests/
  mock_miner.py     # fake cgminer API server (S19 Pro sample data)
  run_mock_test.sh  # end-to-end mock test -> tests/RESULTS.md
```
