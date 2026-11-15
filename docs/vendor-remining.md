# Vendor re-mining — Toolkit 1.7.5 binary, second pass (2026-11-12)

Why a second pass: v0.30 graded Braiins / IceRiver / Jasminer as
"cred-tag-only" because the AOT string pool held no API strings
for them. The v0.36 pyasic-mining agent is working the OSS-library
route in parallel; this pass re-mines the **Toolkit materials
themselves** harder — fresh offset-tagged dumps, the headless
`toolkit_cli` binary (which shares the services core and turned
out to be string-richer than the GUI's `libapp.so`), the CLI's
own `--help` surface, and one dynamic probe (the CLI run against
a logging mock server on localhost, no live miner involved).

Materials: `research/hashcore/toolkit-x64/` — `lib/libapp.so`
(14 MB), `lib/librust_ffi_plugin.so` (3.9 MB),
`lib/toolkit_cli` (12 MB), `data/flutter_assets/`.
Method: `strings -a -t x -n 4` (ASCII + UTF-16LE) on all three
binaries; case-insensitive targeted greps; `toolkit_cli --help`
and `help <command>`; one dynamic discovery probe.

## 0. Method limits (read first)

- **AOT strings are not code-local.** Sampling ±30 lines around
  a hit in the strings dump returns random Dart-SDK/framework
  strings (`package:pointycastle/...`, `dart:_internal/...`).
  Proximity mining for endpoints is **invalid**; only the
  literal itself counts.
- **DTO names prove a data model, not a transport.** A class
  named `IceRiverApiSession` proves an HTTP-ish session exists;
  it does not give the port, path, or request shape.
- Grading used here: **DIRECT-EVIDENCE** (observed behaviour
  or a literal that yields transport + request + fingerprint),
  **SUGGESTIVE** (real adapter surface, but no transport —
  a lead for the live-machine step, NOT implementable),
  **NOISE** (coincidental match, e.g. base64 blobs, SIMD type
  names).

## 1. Per-vendor verdicts

### Braiins (G-B1) — SUGGESTIVE (data model recovered, transport still unknown)

Hits: 53 in `libapp.so`, **212 in `toolkit_cli`**. DTO surface:

- `BraiinsOS`, `BraiinsConfigDto` /
  `BraiinsConfigResponseDto`, `BraiinsTunerStatusDto` /
  `BraiinsTunerStatusResponseDto`, `BraiinsFansDto` /
  `BraiinsFansResponseDto`, `BraiinsLuxorTempDto` /
  `BraiinsLuxorTempsResponseDto` (temps arrive in a Luxor-shaped
  DTO), `BraiinsUpdateStatisticsResult`, `BraiinsRepository`
  with `_discoverApplier` / `_discoverReceiver`,
  `_updateStatsApplier` / `_updateStatsReceiver`,
  `_updateTempFields`, `_unlockApplier`,
  `_removeFirmwareApplier`.

Zero hits (all dumps, all encodings): `bosminer`,
`braiins-os`, `Braiins OS`. No gRPC method string, no endpoint
path, no version-string fingerprint literal exists in the
binaries. **What this closes:** the Braiins adapter reads
config / tuner status / fans / temps through a repository
with discover + stats + unlock + remove-firmware appliers.
**What it does not close:** port, request format, fingerprint.
Live-machine step: one `version` reply from a real Braiins OS
machine (or the `bosminer` API doc's fingerprint) is still
the single datum that closes G-B1.

### IceRiver (G-I1) — SUGGESTIVE (richest new surface in this pass)

Hits: 54 in `libapp.so`, **310 in `toolkit_cli`**. DTO surface:

- `IceRiverApiSession`, `IceRiverDiscoverResult`,
  `IceRiverRepository`, `IceRiverUpdateStatisticsResult`,
  `IceRiverInfoDto`, `IceRiverBoardsDto` / `IceRiverBoardDto` /
  `IceRiverBoardPowDto`, `IceRiverPoolsDto` / `IceRiverPoolDto`,
  `IceRiverSetPoolDto` / `IceRiverSetPoolItemDto`,
  `IceRiverNetDto`, `IceRiverFanDto`, `IceRiverResponseDto`,
  `AppMetricsDto.fromIceRiverPowsReply`.

Zero hits: `kaspa`, `kheavyhash`, model strings `KS0`/`KS1`/
`KS2`/`KS3` (the 1–2 hits each are base64 noise). The
`IceRiverApiSession` class name + the set-pool DTOs prove a
session-based HTTP API with pool management; the paths and
auth are not in the binaries. Live-machine step: one capture
of the session's HTTP traffic (or the IceRiver web-API doc)
closes G-I1.

### Jasminer / SunLune (G-J1) — SUGGESTIVE (new lead: the adapter is SunLune's)

Hits: `jasminer` 5 + 9; `sunlune` 63 + **313**. Key line
(`toolkit_cli` strings dump, offset `0xa6e001`):

- `SunLuneRepository._convertMinerPoolToJasminerConfDto` —
  the Jasminer pool-config conversion lives in the **SunLune**
  repository. Jasminer hardware is SunLune-manufactured, and
  Toolkit treats it as such; the adapter to recover is the
  **SunLune API**, not a separate "Jasminer API".
- SunLune DTOs: `SunLuneSummaryDto`, `SunLuneBoardsDto`,
  `SunLuneMinerConfigDto`, `SunLunePoolsDto` /
  `SunLunePoolConfigDto` / `SunLunePoolItemDto`,
  `SunLuneHashBoardSnDto`, `SunLuneAsicSnDto`,
  `SunLuneRejectLineDto`, `SunLuneAvgHashLineDto`,
  `SunLuneHashLineDto`, `SunLuneStatusDto`,
  `SunLuneDiscoverResult`, `_parseSunLuneValue`,
  `_updateBoardsFields`, plus `JasminerHashLiner`,
  `JasminerPools`.

Live-machine step: one SunLune API capture (or the SunLune
web-API doc) closes G-J1.

### LuxOS — no change (v0.33 stands)

Only `uninstallLuxOs` / `LuxorDeviceApi.uninstallLuxOs`
hits. Consistent with v0.33: LuxOS is read via the
cgminer-compatible socket + Luxor API, implemented from
Luxor's docs.

### Already-implemented families — counts (sanity check)

Canaan, Avalon, Whatsminer/MicroBT all show the expected
rich surfaces (repository + device-API + DTO classes,
hundreds of hits each), matching the v0.30/v0.33 adapters.
`CanaanApiSession`, `AvalonCgConfigDto`,
`AvalonMinerInfoDto`, `WhatsMiner*SocketDto`,
`MicroBtApiV2Session` / `MicroBtHttpApiSession` all present.

## 2. New vendor names — the firmware-type enum is bigger than v0.30 recorded

`toolkit_cli help export` (and every other command) lists the
`--fw-type` filter verbatim:

> `[unknown, hashcore, old-vnish, bitmain, canaan, micro-bt,
> luxor, braiins, auradine, epic, jasminer, pit-bit, ice-river,
> sealminer, mock]`

Four families v0.30 did not name: **auradine, epic, pit-bit,
sealminer** (`mock` is a test stub). String counts in
`toolkit_cli`: auradine 556 (`auradine_temperature` DTOs,
`AuradineRepository`, `AuradineDeviceApi`), epic **931**
(`dto/miner/epic/generated/...` — the `generated/` path means
these DTOs are **code-generated from a spec**, i.e. Epic
speaks a documented API whose client was generated;
`EpicTotalHashrateDto`, `epic_tune_option_dto`,
`EpicRepository`), sealminer 6, pit-bit 19 (`PitBit`).
The model list also names `z15pro`, `l7`, `l9`, `u2l9h`,
`u3s19xph`/`u3s21exph` and the full S19/S21 range — useful
for BeeSky's model table, recorded here not implemented.

These four are **SUGGESTIVE leads, new gaps** (G-AU1,
G-EP1, G-PB1, G-SE1): real adapter surfaces exist, but no
transport was recovered in this pass. The Epic `generated/`
path is the strongest lead of the four — a generated client
implies a published spec somewhere upstream.

## 3. Dynamic probe — discovery sequence, observed live (DIRECT-EVIDENCE)

Setup: logging HTTP servers on 127.0.0.1:80/443/8080 and TCP
loggers on :4028/:4029/:8888; ran `toolkit_cli export
--ips-file <127.0.0.1> -s toolkit_settings.json -f json`
(no live miner; localhost mock only). Observed:

1. `HTTP:80 GET /` with `User-Agent: Dart/3.11 (dart:io)` —
   the port-80 availability probe.
2. TCP `:4028`, five rounds of
   `{"command":"stats"}`, `{"command":"summary"}`,
   `{"command":"devdetails"}`, `{"command":"pools"}` —
   the generic cgminer discovery, retried per discover pass.
3. No request touched :443, :8080, :4029 or :8888; no
   vendor-specific endpoint appeared, because the mock's
   404/empty replies never identified a vendor, so no
   vendor adapter path was entered.

**Verdict:** the generic discovery order is confirmed
(:80 probe, then :4028 cgminer commands in that exact
order). The probe cannot yield vendor endpoints without a
mock that answers like a real vendor device — that is the
designed next experiment (feed candidate version strings
and watch which follow-up requests fire), not run here.

## 4. Ports, CGI paths, translation files

- `4028`: confirmed as the fallback probe port
  (`Port 80 not available. Checking port 4028`, in both
  `libapp.so` and `toolkit_cli`).
- `8888` / `14235`: **zero hits** in every dump — the
  IP-Report listener ports are not evidenced in Toolkit
  strings, consistent with v0.34 (protocol recovered from
  OSS implementations, not from Toolkit). The feature name
  `ipReport` does occur once in the CLI dump.
- `/cgi-bin/`: the full stock CGI list re-confirmed
  (`miner_type.cgi`, `upgrade.cgi`, `set_miner_conf.cgi`,
  `reboot.cgi`, `get_system_info.php`, …) plus the unlock
  cluster at `librust` offset `0x27b78` (see UNLOCK-DEEP.md).
- Model strings `KS0`–`KS3`, `X4`, `AL1`: **NOISE**
  (base64 blobs in `libflutter_linux_gtk.so` region,
  `Int32x4`/`Float32x4` SIMD type names).
- Translation files: `data/flutter_assets/.../en.json` is a
  **25-key stub**; the ~1,500 keys mined in UI-ANALYSIS live
  compiled inside `libapp.so`, not on disk.

## 5. Direct feed into Track 2 (.bmu format)

`BitmainFirmwareContainerParser` exists in the Dart services
core (`package:toolkit_services/repository/repositories/
bitmain_repository/bitmain_firmware_container_parser/`):
`bitmain_firmware_container_parser.dart`,
`bitmain_firmware_header.dart`, `bitmain_firmware_item.dart`;
methods `getFirmwareFromFile`, `getFirmware`, `_chunk`,
`_readFilePart`; predicate `isBitmainContainer`; error
`InvalidSignature`. **DIRECT-EVIDENCE that Toolkit parses
the Bitmain container itself** — the parser's existence is
what made Track 2's byte-level dissection worth attempting
against a real `.bmu` file (see the §6 addendum in
`docs/unlock-payload-mapping.md`).

## 6. What a live-machine session still needs (per gap)

| Gap | One datum that closes it |
|---|---|
| G-B1 Braiins | One `version` reply from a Braiins OS machine (fingerprint), or the bosminer API fingerprint from docs |
| G-I1 IceRiver | One HTTP session capture (paths + auth), or the IceRiver web-API doc |
| G-J1 Jasminer | One SunLune API capture (paths + auth), or the SunLune web-API doc |
| G-AU1 Auradine | One API capture / vendor doc |
| G-EP1 Epic | The spec the `generated/` DTOs were generated from, or one API capture |
| G-PB1 Pit-Bit | One API capture / vendor doc |
| G-SE1 Sealminer | One API capture / vendor doc |

Nothing in this pass is spec-grade for implementation:
no vendor yielded transport + request format + fingerprint
together. The DTO surfaces above are the honest ceiling of
what the binaries contain.
