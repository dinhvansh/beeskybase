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

**UPDATE 2026-11-12 (§6 addendum below): the container
structure is now ~80% described at byte level from a real
public stock `.bmu` file** — outer header + 5 item entries
with a chain-verified offset/length table, inner `26 01`
items with an embedded RSA-2048 PEM key. What stays UNKNOWN
is the signature scheme/coverage (the 256-byte block at
item+0x418 is NOT a PKCS#1 v1.5 or PSS signature under the
embedded key — verification fails on every candidate data
range) and the chunk-table semantics. U-2 moves to
PARTIALLY CLOSED; see §6 for the layout tables and the
new residual U-6.

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
| U-2 | `.bmu` container field layout | **CLOSED (§7)** — outer + inner layout, chunk table, both signature levels, CityHash64 tag all described and verified; a `.bmu` **parser** can now be written. A **generator** cannot — the signing keys (root private key for level 1, per-family embedded private key for level 2) are not in any material. |
| U-6 | `.bmu` signature scheme/coverage: which bytes the 256-byte block at item+0x418 signs, and under which key/scheme | **CLOSED (§7)** — level 1: RSA PKCS#1 v1.5 + SHA-256 of the embedded PEM, key = on-disk root `/etc/bitmain.pub`; level 2: RSA PKCS#1 v1.5 + SHA-256 of the SHA-256 digest table (D0 header + D1..D7 chunks + D8..D14 per-chunk .sig blocks), key = embedded PEM. Verified with `openssl` AND the genuine `FileParser` under qemu. (The §6.3 "not PKCS#1 v1.5" conclusion was wrong — wrong key for level 1, wrong openssl subcommand for level 2.) |
| U-3 | Inter-attempt delay / patch-success poll timeout | One timed real unlock, or a DWARF-carrying btm-lib build |
| U-4 | Per-stock-version flow variants | Real migrations across stock versions (the 1.7.4 changelog widened the list progressively) |
| U-5 | The 22-char constant's role | Same as U-1/U-2 — it sits in the command cluster; its use is only observable in a live run |
| U-7 | Outer header CRC32 at +0x18 (`0x61513ee5`): which bytes it covers | IEEE CRC32 of header[0:24], of the 5 item entries, and of the header with the field zeroed — none matches. CRC32C (Castagnoli) NOT tested. The web UI's `.bmu` reader (`reader.dd4a57.js`) names the field `Crc32`. |
| U-8 | Per-family root keys + item 1/3/4 rootfs layout | Item 1 (CVITEK) fails level 1 under the Zynq root key (ret 13) — the per-family model is proven by the failure mode — but item 1's own `/etc/bitmain.pub` is not yet in hand: item 1 has no uImage ramdisk (3 chunks: BOOT + dtb + one 4.6 MB blob) and its rootfs was not extracted. Same open for items 3 (Amlogic) and 4 (BeagleBone). Closes by extracting those items' rootfses and verifying level 1 under their own root keys. |

Standing rule (unchanged): research only; no BeeSky
production unlock until a real locked-miner session
validates the recipe end to end, and the unlock stays
behind its three hard gates (owner-supplied `.bmu`
payloads, `--experimental-unlock` + `BEESKY_ALLOW_UNLOCK=1`,
typed-IP confirmation), never a bulk Operations action.

## 6. Addendum 2026-11-12 — `.bmu` format from a public stock firmware (U-2 partially closed)

File dissected: **`Antminer-S19-Pro-merge-release-20221226124238.bmu`**,
72,159,729 bytes (68.8 MB), S19 Pro merged firmware (low-power-mode
release). Source: `https://cdn.miners.tools/downloads/bitmain/sha256/S19PRO/FW/Antminer-S19-Pro-merge-release-20221226124238.bmu`
(Miners Tools CDN direct link; the same file is listed on
asic.tools with matching checksums). Verified:
SHA-256 `3df0d3b4be2079855e0901d3f0b3b5967dcc87ace00105c1a832ddc1821c529c`,
MD5 `91cbf6f4a55698dba075a3a76748a07c`. `.bmu` is Bitmain's
own container — confirmed, not HashCore's invention.

### 6.1 Outer container — FULLY DESCRIBED, chain-verified

Global header (36 bytes, little-endian u32 unless noted):

| Offset | Value | Meaning |
|---|---|---|
| +0x00 | `AB AB AB AB` | Magic |
| +0x04 | `0` | Unknown, zero |
| +0x08 | `0x24` = 36 | Header size / entries offset |
| +0x0c | `5` | Item count |
| +0x10 | `0xAC` = 172 | Item entry size (bytes) |
| +0x14 | `0x4000` = 16384 | Data section start (= first item's offset) |
| +0x18 | `0x61513ee5` | UNKNOWN u32 (timestamp-shaped: 1632714469 = 2021-09-27; predates the firmware build, so not a build date) |
| +0x1c | `0` | Unknown, zero |
| +0x20 | `0` | Unknown, zero |

Item entries: 5 × 172 bytes from 0x24. Each entry:

| Field | Size | Content (this file) |
|---|---|---|
| +0x00 | 4 | `0A 00 ?? 10` — byte0 `0x0a` constant; byte2 varies per item (`0x0f`/`0x10`/`0x11`); purpose UNKNOWN |
| +0x04 | 16 | Inner filename, NUL-padded: `update.bmu` (all 5) |
| +0x14 | 80 | All zero — reserved, purpose UNKNOWN |
| +0x64 | 32 | Platform, NUL-padded |
| +0x84 | 32 | Model, NUL-padded: `Antminer S19 Pro` (all 5) |
| +0xa4 | u32 LE | Data offset |
| +0xa8 | u32 LE | Data length |

The five items (platform → offset/length):

| # | Platform | Offset | Length |
|---|---|---|---|
| 0 | `zynq7007_NBP1901` | 0x4000 | 17,964,303 |
| 1 | `CVCtrl_BHB42XXX` | 0x1125D0F | 12,568,671 |
| 2 | `zynq7007_BHB42XXX` | 0x1D2256E | 18,011,759 |
| 3 | `AMLCtrl_BHB42XXX` | 0x2E4FBDD | 12,798,976 |
| 4 | `BBCtrl_BHB42XXX` | 0x3A847DD | 10,799,636 |

**Chain check (exact):** each item's offset equals the
previous item's offset + length, and item 4 ends at
61,360,093 + 10,799,636 = **72,159,729 = the file size**.
One merged file carries all five control-board variants
(Xilinx Zynq, CVITEK, Amlogic, BeagleBone).

### 6.2 Inner item — structure described, signature UNKNOWN

> **CORRECTED by §7:** the `hsqs`/squashfs claim below is a
> false positive (the `hsqs` bytes sit in item 4, not item 0,
> inside high-entropy data); the rootfs is a gzip-compressed
> ext2 ramdisk in a uImage wrapper. The 8-byte tag at +0x02
> is **CityHash64(subtype)** (§7.1), the byte at +0x0b is
> the high byte of the chunk mask, and the table at +0x518
> is the chunk table (§7.2). The signature is **verified**,
> not unknown (§7.4).

Every item starts with the `26 01` magic from §3:

| Offset (item-relative) | Content |
|---|---|
| +0x00 | `26 01` magic (2 bytes, all 5 items) |
| +0x02 | 8 bytes, varies per item — UNKNOWN (not a SHA-256/SHA-1/MD5 prefix of the whole item, of the post-PEM bytes, of the post-signature bytes, or of the payload from +0x800; tested, no match) |
| +0x0a | `0x01` constant |
| +0x0b | 1 byte, varies (`FE`/`E0`/`FE`/`02`/`F6`) — UNKNOWN |
| +0x0c | u32 `0` |
| +0x10 | u64 **big-endian** = 451 = length of the PEM block below, trailing newline included |
| +0x18 | PEM `-----BEGIN PUBLIC KEY-----` (RSA-2048; DER SHA-256 `76bcdf2d818f57893e47bdf2119dd955e2e6499172602ff01950b22bc2a90258`) |
| +0x1db | `\n`, then zero padding to +0x418 |
| +0x418 | 256 bytes high-entropy block — signature candidate, **NOT verified** (see §6.3) |
| +0x518 | u64 LE = 7, then a table region to +0x800 — raw bytes recorded, semantics UNKNOWN |
| +0x800 | Payload: ARM code (`EAFFFFFE` branch-to-self padding at 0x4800 in item-relative terms — i.e. absolute 0x4800), squashfs rootfs (`hsqs` at absolute 0x3E40490 in item 0), other firmware data |

Keys: **two distinct RSA-2048 keys** across the five items —
items 0 and 2 (both Zynq) share one key; items 1 (CVITEK),
3 (Amlogic), 4 (BeagleBone) each carry their own. The key
is per control-board family, not per file.

### 6.3 Signature — attempted verification, all FAILED

> **CORRECTED by §7:** the failures below were test errors,
> not a scheme difference — level 1 was tested under the
> wrong key (the embedded PEM instead of the on-disk root
> key), and level 2 was tested with the wrong openssl
> subcommand (`dgst -verify` hashes its input; a precomputed
> digest needs `pkeyutl -verify`). The block IS a valid
> RSA PKCS#1 v1.5 + SHA-256 signature at both levels (§7.4).

The 256-byte block at item+0x418 was tested as a signature
under the item's own embedded PEM key with `openssl`:

- `dgst -sha256 -verify` over four data ranges (after the
  block, after the PEM, from +0x800, whole item with the
  block zeroed) — all **verification failure**.
- `pkeyutl -verifyrecover` (tests padding/key alone, no
  data) — **invalid PKCS#1 v1.5 padding**. The block is
  therefore NOT a PKCS#1 v1.5 signature under this key.
- PSS verify (`rsa_padding_mode:pss`, saltlen -1) over the
  post-block range — **first octet invalid**.

**Verdict: the signature scheme and coverage are UNKNOWN.**
Either the block is not the signature (it may be encrypted
data, or a nonce), or the embedded PEM is not the key that
verifies it (the miner verifies against `/etc/bitmain-adv.pub`,
which may differ), or the scheme is a third one. No
forgery was attempted and none is possible from this data:
without the signing key and the covered range, no valid
`.bmu` can be produced — which is exactly the safety
property the format is designed to have.

### 6.4 What this changes

- U-2: **PARTIALLY CLOSED**. A `.bmu` **parser** for the
  outer container + inner items can now be written from
  this layout (magic, header, entries, offsets, PEM
  extraction). A `.bmu` **generator** cannot — the
  signature block is unverified and the 8-byte tag / 0x0b
  byte / chunk table are undescribed.
- New residual U-6 (see §5 table): signature scheme/coverage.
- Recommended next step (not done here): extract the
  payload squashfs (item 0, `hsqs` at 0x3E40490) — the
  stock firmware's own upgrade handler scripts inside it
  are the most direct evidence of how the miner verifies
  a `.bmu`, and may also name the chunk-table format.

> **Done — see §7.** The "squashfs" was a false positive;
> the handler was found in the gzip+ext2 ramdisk instead.

## 7. Addendum 2026-11-12 — the miner-side upgrade handler (U-6 CLOSED)

Same file as §6 (`Antminer-S19-Pro-merge-release-20221226124238.bmu`,
SHA-256 `3df0d3b4…`). The payload was extracted and the
stock firmware's own upgrade handler was read out of it.
**U-6 is CLOSED, both levels, empirically verified** — by
`openssl` AND by running the genuine stock `FileParser`
under qemu-arm-static.

### 7.1 Corrections to §6 — the rootfs is NOT squashfs

- The `hsqs` at absolute 0x3E40490 is a **false positive**:
  it sits inside **item 4** (`BBCtrl_BHB42XXX`),
  item-relative 0x3BBCB3 — not item 0 — in high-entropy
  data (a superblock parse there yields garbage: inodes
  251,682,525, block_size 1,181,483,086, version 43776.589;
  a cramfs magic and a `-rom1fs-` string within 20 bytes
  confirm random-data coincidences). There is exactly ONE
  `hsqs` in the whole file; no `sqsh`, no xz, no zstd, no
  UBI# anywhere.
- Item 0's payload is a **gzip-compressed ext2 ramdisk
  inside a uImage wrapper**: uImage kernel at item0+0x2AF28E
  (size 4,057,256, Linux 4.6.0-xilinx, ARM, type 2 kernel);
  uImage ramdisks at item0+0x68DB76 (size 6,827,839, type 3
  ramdisk, gzip) and item0+0xD10AF5 (size 4,277,189). Both
  gzip payloads decompress to exactly 33,554,432-byte ext2
  images (magic 0x53EF at +1080). Ramdisk 1 is the main
  rootfs (contains `upgrade.cgi`, `openssl`, `cgminer`
  strings); ramdisk 2 has none of those.
  Evidence: `~/workspace/vendor-remining/sqfs/rd1.cpio`,
  `rd2.cpio` (ext2 images, despite the name),
  `rootfs-rd1/` (extracted via `debugfs rdump`).
- The 8-byte tag at item+0x02 is **CityHash64(subtype)**,
  little-endian u64 — verified against all five items
  (Python `cityhash` module, all MATCH):
  `zynq7007_NBP1901` → `986762bbb59972d8`,
  `CVCtrl_BHB42XXX` → `883b7c5d69fe738b`,
  `zynq7007_BHB42XXX` → `1def947662ceb57a`,
  `AMLCtrl_BHB42XXX` → `5f13c15d6fb62afb`,
  `BBCtrl_BHB42XXX` → `36cd874c0797f5d8`.
  (FNV-1a/1-64, djb2, SHA-256 prefixes, xxHash64 all
  failed; CityHash64 matches all four qemu-observed
  pairs plus the fifth tag. The length-dispatched
  structure of `FileParser` 0x12180 — ≤16 / ≤32 / ≤64 /
  longer — is CityHash64's HashLen0to16/17to32/33to64
  shape.)
- The byte at item+0x0b is the **high byte of the 16-bit
  chunk mask** (`mask = (buf[0x0b]<<8)|buf[0x0c]`):
  item 0 mask `0xFE00` (popcount 7), item 1 mask `0xE000`
  (popcount 3). `buf[0x518]` = popcount = chunk count.
  The u32 at +0x519..0x51c is 0 in item 0 (purpose
  unknown — only printed in the size-mismatch error).

### 7.2 The chunk table (item 0, 7 chunks)

Byte +0x518 = count (7); +0x519–0x51c = BE u32 (0);
entries 5 bytes each from +0x51d: `[index:1][size:4 BE]`.
Chunk names come from `FileParser`'s jump table
(§7.5): 0 BOOT.bin, 1 devicetree.dtb, 2 uImage,
3 minerfs.image.gz, 4 update.image.gz, 5 crl.tar.gz,
6 miner.btm.tar.gz, 7 reserve, 8 datafile, 9 .sig.

| # | Name | Size | Starts at (item-rel) | Content |
|---|---|---|---|---|
| 0 | BOOT.bin | 2,788,160 | 0x800 | ARM code (`EAFFFFFE` padding, `665599aa`) |
| 1 | devicetree.dtb | 8,014 | 0x2A9340 | `d00dfeed` FIT device tree |
| 2 | uImage | 4,057,320 | 0x2AB28E | uImage kernel (4,057,256 + 64 header) |
| 3 | minerfs.image.gz | 6,827,903 | 0x689B76 | uImage ramdisk 1 (6,827,839 + 64) |
| 4 | update.image.gz | 4,277,253 | 0xD0CAF5 | uImage ramdisk 2 (4,277,189 + 64) |
| 5 | crl.tar.gz | 552 | — | gzip `1f8b0800…` |
| 6 | miner.btm.tar.gz | 1,005 | — | gzip `1f8b0800…` |

Σ chunk sizes + 4096 (= 0x800 header + 8×256
per-chunk `.sig` blocks) = 17,964,303 = item 0 length
**exactly**. Each chunk start lands exactly on its
content magic (diff 0). `FileParser -s` splits these to
`/tmp/tmpfw/` (copied to
`~/workspace/vendor-remining/split-item0/` — 16 files:
7 chunks + 7 `.sig` + `miner.pem` + `miner.pem.sig`).

### 7.3 The handler chain, in order

All paths are inside the stock rootfs (`rootfs-rd1/`).

**1. `www/pages/cgi-bin/upgrade.cgi`** (738 bytes, POSIX
shell, `#!/bin/sh -e`): creates `/tmp/$$`, reads the
multipart upload (skips headers to the blank line),
writes the rest to `update.bmu`, truncates trailing CRLF
bytes, runs **`/usr/sbin/daemonc $file`**; exit 0 →
`{"stats":"success","code":"U000","msg":"OK!"}` +
`echo 2 > /tmp/miner_act`; else
`{"stats":"error","code":"U00<err>","msg":"<err>"}`.
`upgrade_clear.cgi` (722 bytes) is identical except on
success it writes `echo 3 > /tmp/miner_act`. Both
`trap atexit 0` removing the uploaded file + `sync`.

**2. `/usr/sbin/daemonc`** → symlink to
`/usr/sbin/update-daemon` (9,660 bytes, ELF 32-bit LSB
ARM EABI5, dynamically linked, stripped, BuildID sha1
`5d8be2c984f4bab9e6b5358b44cd64e951611871`): a local
socket server listening on **127.0.0.1:22322**; `argv[0]`
dispatch — `daemonc` = client, `daemons` = server
(`accept` + `system()` on the received command).
Started at boot by `/etc/init.d/S67update-daemon`
(`/usr/sbin/daemons &`). Strings: "ProcessServer",
"Recv:'%s'", "Shell Exec Successfully!",
"Shell Execute Failed, Ret[%d]", "Other Exit Ret[%d]",
"Come On WUHAN", "Cannot Find Command!",
"daemonc"/"daemons", "update-daemon.c",
"/usr/sbin/updateporc.sh ".

**3. `/usr/sbin/updateporc.sh`** (2,525 bytes): if the
file exists → `miner_type.cgi` for the subtype (`jq
.subtype`; subtype comes from `/etc/subtype` on the
miner, else "unknown"; miner_type from line 2 of
`/usr/bin/compile_time`) → **`/usr/bin/FileParser -f
"$subtype" $FILE /etc/bitmain.pub`**; non-zero return →
return that code; else UBIFS staging (`ubiattach
/dev/ubi_ctrl -m 6 -b 2`, `ubimkvol /dev/ubi1 -m -N
update_file` if needed, `flash_erase /dev/mtd6` +
`ubiformat` on failure paths; `mount -t ubifs
/dev/ubi1_0 /tmp/updatedata`), `rm -rf
/tmp/updatedata/*`, `cp $FILE /tmp/updatedata/update.bmu`,
`sync`, `umount`, `set_marker` =
`flash_erase /dev/mtd0 0x1B00000 0x1` (boot flag so the
bootloader picks up the update on reboot), return 0.

**4. `/usr/bin/FileParser`** (23,912 bytes, ELF 32-bit
ARM, stripped, BuildID sha1
`181de1e2c242bfbc527795edba919e57c22fa25a`, links
libcrypto.so.1.1 OPENSSL_1_1_0): the actual `.bmu`
verifier/parser. Modes from its own strings: `-f
[minerType] [fileName] [rootPublicKeyFile]` = "Only Check
If Filename was Valided."; `-s` = check + split BMU to
`/tmp/tmpfw/`; `-p` = check + dump BmuComments; `-x` =
check full-size BMU; `-n [nandBinFile]` = split SigImg to
`/tmp/tmpNand/`; `-q` = generate 256-byte 0xFF file to
`/tmp/256BFF`. Returns 0 = "Well Done!", others =
"Something Wrong!". Error strings: "Read Root PubK
Failed!", "Check miner.pem Failed!", "Check File Sig
failed!", "Load Pem Failed!", "Check pem payload failed!
ret:[%d]", "input miner_type and bmu miner type donot
match!", "miner_type_hash %16llx, bmu_hash %16llx",
"This Package Was Not Full Package!", "Content Doesn't
Match![%d][%d]", "Check FileSize Failed, FileSize Should
Be [%d]Bytes, But It Was [%d] Bytes, And Total Says[%d]",
"Cannot Open Root PublicKey '%s'!".

### 7.4 What FileParser checks, in order (0x12c40 main check)

Disassembly: Capstone, ARM LE, `.text` vaddr 0x10838,
3,277 insns; saved at
`~/workspace/vendor-remining/fp_dis.txt`, `fp_main.txt`.
PLT at 0x106f4 (20-byte PLT0, 12-byte stubs, a 4-byte
gap at 0x107e0 shifting later stubs +4 — verify
stub→symbol mapping by decoding the `ldr pc, [ip,
#imm]` targets, not a naive grid). Function starts:
0x108f8, 0x109a8, 0x10b9c, **0x10c70 (verify helper)**,
0x10de8 (chunk hash+split helper), 0x11490, 0x116c8,
0x11a00, 0x11be0, 0x11fbc, 0x120dc, **0x12180 (CityHash64
miner-type hash)**, **0x12c40 (main check)**, 0x1373c
(main).

1. **Size + magic:** file size < 0x800 → err 6;
   `buf[0] != 0x26` → err 8 ("'%s' Not A Btmu File!").
2. **Miner type:** CityHash64(subtype string) vs the
   8-byte tag at item+0x02; mismatch → err **0x1e (30)**.
3. **Chunk-table validation:** `(mask & 0xfe00) == 0xfe00`
   → err 0x14 (20); popcount(mask) must equal
   `buf[0x518]` else err 9; Σ chunk sizes + 4096 must
   equal the file size else err 0xa (10).
4. **LEVEL 1 — the embedded PEM, under the ROOT key:**
   `verify(data = buf+0x18 [embedded PEM], len = BE u64
   at +0x10 = 451, sig = buf+0x418 [256-byte block],
   key = /etc/bitmain.pub)` — helper 0x10c70:
   `BIO_new_mem_buf(pem, 0x400)` →
   `PEM_read_bio_RSA_PUBKEY` → `SHA256_Init/Update/
   Final` → `RSA_verify(NID_sha256=0x2a0, digest, 32,
   sig, 256, rsa)`. Failure → "Check miner.pem Failed!"
   (ret 13 observed for item 1 under the wrong family's
   key). **Verified by openssl:**
   `openssl dgst -sha256 -verify rootfs-rd1/etc/bitmain.pub
   -signature <item0[0x418:0x518]> <item0[0x18:0x18+451]>`
   → **"Verified OK", exit 0**.
5. **LEVEL 2 — the content chain, under the EMBEDDED key:**
   D0 = SHA256(header[0:0x800]); D1..D7 =
   SHA256(each chunk, in file order from offset 0x800);
   D8..D14 = SHA256(each 256-byte `.sig` block trailing
   the chunks); Dfinal = SHA256(concat D0..D14, 480
   bytes = (popcount<<6)+0x20); final signature = the
   last 256 bytes of the item file; second `RSA_verify`
   at 0x1361c (NID_sha256, Dfinal, 32, final sig, 256,
   embedded key). Failure → "Check File Sig failed!"
   err **0x12 (18)**. **Verified by openssl**
   (note the method trap: `dgst -verify` hashes its
   input file, so a precomputed digest must be verified
   with `pkeyutl`):
   `openssl pkeyutl -verify -pubin -inkey <embedded PEM>
   -sigfile <item0 last 256 bytes> -in <Dfinal>
   -pkeyopt digest:sha256`
   → **"Signature Verified Successfully", exit 0**.
   The digest model was cross-checked against the
   `FileParser -s` split files (hashing each split chunk
   and `.sig` file reproduces the same D values).
6. **On success:** `-s` dumps chunks + `.sig` files +
   `miner.pem`/`miner.pem.sig` to `/tmp/tmpfw/`; `-p`
   prints "This Comment Of This Package:" + 0x100 bytes
   at `buf+0x550` (empty/zero in item 0); prints
   "All Done!", return 0.

**Ground truth (qemu-arm-static, `-L rootfs-rd1`):**
item 0 with subtype `zynq7007_NBP1901` → prints
"miner_type_hash 986762bbb59972d8, bmu_hash
986762bbb59972d8", all seven "file[N] size:[…]",
"All Done!", **exit 0** — the genuine stock item
verifies fully, both levels pass. Wrong subtype
(`NBP1901` / `Antminer S19 Pro` / `unknown`) →
hash mismatch, **exit 30**. Item 1 with subtype
`CVCtrl_BHB42XXX` under the Zynq root key → "Check
miner.pem Failed!", **exit 13**. `-p` mode on item 0:
same verification passes, comment field empty, exit 0.

### 7.5 Which key verifies what

| Level | Data signed | Key | Where the key lives |
|---|---|---|---|
| 1 | Embedded PEM bytes, item[0x18:0x18+451] | **Root key** `/etc/bitmain.pub` (DER SHA-256 `6593db327a23a412b0306dba82296d32f78a91fabccb151c08edfa7448ef0b82`, 451 bytes) | On the miner's own rootfs — **DIFFERENT from the `.bmu`-embedded PEM** (DER SHA-256 `76bcdf2d…`) |
| 2 | SHA-256 digest table D0..D14 (480 bytes) | **Embedded PEM** (the item's own key) | Inside the `.bmu` at item+0x18 |

The root key is **per control-board family**: items 0
and 2 (Zynq) share one embedded key; items 1 (CVITEK),
3 (Amlogic), 4 (BeagleBone) each carry their own.
Item 1 fails level 1 under the Zynq family's root key
(ret 13, RSA padding error — well-formed signature,
wrong key), which proves the per-family model from the
failure mode. **No `/etc/bitmain-adv.pub` exists
anywhere in the stock rootfs** (grep finds only
`/etc/bitmain.pub` + `/etc/bitmain_category.conf`) —
the adv key the unlock race targets is NOT a stock
file; it must be introduced by the unlock payload
itself (transition). The stock `updateporc.sh` only
ever references `/etc/bitmain.pub`.

### 7.6 U-6 verdict — CLOSED

Both levels are RSA PKCS#1 v1.5 + SHA-256, verified
two independent ways (openssl + the genuine
FileParser under qemu). The §6.3 conclusion ("NOT a
PKCS#1 v1.5 signature") was wrong: it tested the
level-1 block under the embedded key instead of the
root key, and tested the level-2 digest with
`dgst -verify` instead of `pkeyutl -verify`.

**What this changes for the unlock recipe (UNLOCK-DEEP.md):**
- The race target is now fully explained: the unlock
  flow's `openssl dgst -sha256 -verify
  /etc/bitmain-adv.pub` is the *payload-side* analogue
  of FileParser's level-1 check — the first `.bmu`
  (verified under the stock `/etc/bitmain.pub`)
  installs the adv key, and the second `.bmu` is
  verified against it; the race kills that verify
  mid-upgrade. The stock handler never references the
  adv key, so the adv-key step is entirely a
  payload-side transition — consistent with the
  recipe's "unlock is fully local" finding.
- U-2 is now **CLOSED for the parser**: outer + inner
  layout, chunk table, both signature levels, CityHash64
  tag. A `.bmu` **generator** is still impossible
  without the signing keys (the root private key for
  level 1, the per-family embedded private key for
  level 2) — the format's safety property stands, and
  no forgery was attempted.
- New residuals: U-7 (outer CRC32 coverage), U-8
  (per-family root keys for items 1/3/4 + their rootfs
  layouts — item 1 has only 3 chunks and no uImage
  ramdisk; its 4.6 MB chunk 2 is an unparsed blob).
- The chunk-table + signature model also explains why
  the Toolkit's unlock needs a *real* firmware package:
  the payload (run.sh + the two `.bmu` files) is the
  only thing that can carry a validly-signed inner
  item, and the race is the only way around the
  second-level check without the adv private key.
