# v0.35.0 mapping — unlock payload research (Blutter / Rust disassembly)

The last open piece of the HashCore unlock recipe
(`research/hashcore/UNLOCK-DEEP.md`, ~85% at step level): the
contents of the SSH payload's `run.sh`, the `.bmu` container
format, and the exact race timing. This document records one
bounded research session (2026-11-12) against the Toolkit 1.7.5
materials in `research/hashcore/` — what was attempted, what
each tool returned, what was RECOVERED, and what stays UNKNOWN.
Nothing here is invented; a failed avenue is recorded as failed.

## 0. Where the payload lives (why most of it is unrecoverable from Toolkit)

The payload is NOT inside Toolkit. `UNLOCK-DEEP.md` already
established this and this session re-confirmed it: the SSH
payload (`/tmp/payload`, `run.sh`) ships inside the *firmware
package* that Toolkit downloads from
`hashcore.s3.amazonaws.com/toolkit` (or that the operator
chooses locally) — Toolkit only carries the *names* and the
*commands* that run it. No `.bmu` file exists anywhere in the
research materials (`find` over the whole workspace: zero
hits), and the VNish firmware package dissected in
`research/vnish/` contains its own NAND installer
(`extracted/nand137/runme.sh`) — a different script (it
installs VNish onto NAND behind the HashCore signature chain;
it is NOT the unlock payload). The VNish rootfs was grepped for
`bitmain-adv.pub`, `update_first`, `/tmp/payload`: no hits
except `/usr/sbin/update_firmware` mentioning `openssl dgst`
(the firmware-side updater, not the unlock).

Consequence: **no static analysis of Toolkit can recover
`run.sh`'s contents.** The only routes left are (a) obtaining
a real firmware package from HashCore's S3 distribution and
extracting its payload, or (b) watching a real locked miner
unlock. Both are hardware/session-gated — see §5.

## 1. Blutter — BLOCKED (tool does not support this target)

Attempt: `git clone https://github.com/worawit/blutter` (succeeded
— network works for GitHub), then read its README.

Result: **Blutter supports Android `libapp.so` (arm64) ONLY**
(README: "Currently the application supports only Android
libapp.so (arm64 only)"). The Toolkit binary under analysis is
the **Linux x64** build (`toolkit-x64/lib/libapp.so`). A
secondary blocker: Blutter needs the Dart SDK matching the
app's Dart version (**3.11.5**, identified in UNLOCK-DEEP);
the SDK on this machine is 3.13.7. No Blutter run was possible;
no Dart-side unlock orchestration beyond the already-mined
string pools was recovered this way.

(The string pools themselves were already fully mined in
UNLOCK-DEEP / UI-ANALYSIS: Dart file map, translation keys,
`UnlockMethod`/`InstallFirmwareParam` shapes. Nothing new was
left in them for this question.)

## 2. Rust disassembly — PARTIAL RECOVERY (race attempts = 10)

The unlock core is Rust (`librust_ffi_plugin.so`, crate
`btm-lib`: `miner/unlock_flow.rs`, `unlock/upgrade_race.rs`,
`unlock/upgrade_cgi.rs`, `unlock/upgrade_http.rs`,
`miner/install.rs`, `firmware_file.rs`), stripped, no debug
sections (`readelf -S`: only `.rodata`/`.text`, no `.debug_*`).
Method: `strings -t x` for the race string cluster, then
`objdump -d` cross-references to the string addresses, then
hand-read the enclosing async state machine.

### 2.1 RECOVERED — the race retry count is 10

Evidence (link-time addresses in `librust_ffi_plugin.so`):

- `update_first.bmu` at file offset `0x166d0`;
  `update_second.bmu` + the whole unlock command cluster at
  `0x27b78` (`sudo kill -9 $(ps | grep '[o]penssl dgst -sha256
  -verify /etc/bitmain-adv.pub' | awk '{print $1}')`,
  `sudo rm /nvdata/update.log`, the `/tmp` cleanup,
  `/cgi-bin/pool_protect.cgi`, `upgrade race`,
  `/cgi-bin/patch_success.cgi`, `success response read timed
  out`, `race update upload`, `upgrade race attempts
  exhausted` at `0x27d4a`).
- The "attempts exhausted" error is constructed at `0x1b4bdc`
  (`lea 0x27d4a`, length `0x1f` = 31 = len("upgrade race
  attempts exhausted")). Immediately before it:
  `movw $0xa00, 0x288(%rbx)` — one 16-bit store packing
  counter = `0x00` (low byte) and limit = `0x0a` = **10**
  (high byte) — then `mov $0xa, %cl`.
- The loop head at `0x1b6961`: `mov 0x288(%rbx),%al`
  (counter), `mov 0x289(%rbx),%cl` (limit 10),
  `cmp %cl,%al; jae 0x1b69eb` (exit when counter >= 10),
  `lea 0x1(%rax),%ecx; mov %cl,0x288(%rbx)` (increment),
  `mov %al,0x28a(%rbx)` (stash the attempt index just run).
  The loop body at `0x1b697f` loads `update_first.bmu`.

**Verdict: the upgrade race runs at most 10 attempts.**
Grade: RECOVERED (instruction-trace, two independent
observations of the constant 10 — the packed word and the
compare — in one function).

### 2.2 NOT RECOVERED — the inter-attempt delay / poll timeout

The same region contains Duration arithmetic keyed off the
attempt index stored at `0x28a` (at `0x1b5d86`:
`imul $0x19` (×25), `div $0x28` (÷40), `div $0x3e8`
(÷1000), `imul $0xf4240` (×1,000,000 = ns conversion)) —
consistent with a `Duration` built from the attempt index
with a tens-of-milliseconds-per-attempt factor (a backoff or
a poll interval). But the exact formula is **ambiguous from
the dump alone**: the ÷40 step has no single clean reading
(it could be part of a `from_millis(25 * attempt)` expansion,
a normalisation after a `Duration * factor`, or a separate
value), and the call it feeds (`0x12ad05`, also called
elsewhere with a different static) cannot be identified
without symbols. No sleep duration and no
patch-success poll timeout is asserted here.

**Verdict: UNKNOWN.** A live observation (one real unlock
with timing) is the honest way to close it; deeper RE would
need symbol recovery (e.g. a DWARF-carrying build, which the
shipped .so is not).

### 2.3 Context recovered from the param structs (strings only)

`InstallFirmwareParam` has 12 elements; its field-name
cluster (strings dump line 1103) includes
`connectionTimeoutSec` and `installFwTimeoutSec` — the
timeouts are **parameters passed in from Dart settings, not
constants in the binary**, so there is nothing to recover for
them here. `UnlockSshAccessParam` has 8 elements;
`RestoreCvitekFirmwareParam` 8; `CleanupUpgradeUnlockFilesParam`
3. The 22-char constant in the unlock cluster (~`0x27b78`)
is recorded by offset/existence only, per UNLOCK-DEEP policy;
its value is deliberately not reproduced in this repo.

## 3. `.bmu` format — INSUFFICIENT (public sources only)

Public web research (2026-11-12) establishes only:

- `.bmu` is Bitmain's proprietary firmware-update container
  (filext.com: "primarily associated with AntMiner Firmware
  Update Tool"); the common variant starts with signature
  bytes `26 01`, is 15–18 MB, and embeds a PEM public key
  (`----BEGIN PUBLIC KEY----`).
- Stock Antminer firmware enforces the signature at flash
  time; the two-file dance (`update_first.bmu` then
  `update_second.bmu`) matches Bitmain's own "transition then
  merge" upgrade pattern for old firmware (blockchain-council
  tutorial), which is consistent with Toolkit uploading a
  small first image to break the signature gate and the real
  image second — but the *contents* of HashCore's two files
  are not public.

No documented field layout, no offsets, no magic beyond the
two leading bytes. **Insufficient to implement a `.bmu`
parser or generator.** BeeSky's `core/firmware.py` unlock
path stays as it is: it uploads *operator-supplied* `.bmu`
files and never fabricates one.

## 4. What this changes in BeeSky (v0.35.0)

- `docs/unlock-payload-mapping.md` (this file) — the research
  record.
- `beesky/core/firmware.py` docstring + `tests/RESULTS.md`:
  the race attempt count is now **10, recovered** (was:
  "retry until attempts exhausted", count unknown). No code
  change: BeeSky's gated unlock already retries the race in a
  loop; the count is documented as the Toolkit-observed
  bound, not newly implemented behaviour.
- Nothing else in the unlock path changes. The recipe
  confidence moves **~85% → ~87%** at step level (one
  constant closed); the production leg stays gated.

## 5. Residuals (what still needs a farm / a session)

| # | Unknown | Closes with |
|---|---|---|
| U-1 | `run.sh` / payload contents | A real HashCore firmware package from S3 (extract the payload) or watching a real locked miner unlock |
| U-2 | `.bmu` container field layout | A real `update_first/second.bmu` pair to parse (operator-supplied, from a real migration) |
| U-3 | Inter-attempt delay / patch-success poll timeout | One timed real unlock, or a DWARF-carrying btm-lib build |
| U-4 | Per-stock-version flow variants | Real migrations across stock versions (the 1.7.4 changelog widened the list progressively) |
| U-5 | The 22-char constant's role | Same as U-1/U-2 — it sits in the command cluster; its use is only observable in a live run |

Standing rule (unchanged): research only; no BeeSky
production unlock until a real locked-miner session
validates the recipe end to end, and the unlock stays
behind its three hard gates (owner-supplied `.bmu`
payloads, `--experimental-unlock` + `BEESKY_ALLOW_UNLOCK=1`,
typed-IP confirmation), never a bulk Operations action.
