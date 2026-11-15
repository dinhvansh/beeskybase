# Research note — vendor re-mining + .bmu format (2026-11-12)

Research-only session, two tracks. Full records:
`docs/vendor-remining.md` (Track 1) and the §6 addendum in
`docs/unlock-payload-mapping.md` (Track 2). No product code
changed; no version bumped.

## Track 2 — .bmu format: VERDICT ~80% DESCRIBED (the headline result)

Downloaded the public stock S19 Pro firmware
`Antminer-S19-Pro-merge-release-20221226124238.bmu`
(72,159,729 bytes; SHA-256 verified against asic.tools).
The outer container is **fully described and chain-verified
to the byte**: magic `ABABABAB`, 36-byte header, 5 × 172-byte
item entries (one per control-board family), offsets/lengths
summing exactly to the file size. Each inner item starts
`26 01` and embeds an RSA-2048 PEM public key (two distinct
keys across the five items). **Still UNKNOWN:** the signature
scheme/coverage — the 256-byte block at item+0x418 fails
PKCS#1 v1.5 and PSS verification under the embedded key on
every candidate data range — plus an 8-byte tag, one varying
byte, and a 7-entry table. A `.bmu` parser can now be
written; a generator cannot (by design — no signing key,
no covered range). U-2 partially closed; new residual U-6.
Recommended next step: extract the payload squashfs
(`hsqs` at 0x3E40490) for the miner-side upgrade handler.

## Track 1 — vendor re-mining: NO SPEC-GRADE TRANSPORTS, but richer leads

Fresh string dumps + the runnable `toolkit_cli` (string-richer
than the GUI) + one dynamic localhost probe. Braiins, IceRiver
and Jasminer/SunLune all show **real DTO/repository surfaces**
(data models recovered — config/tuner/fans/temps for Braiins;
session + pools for IceRiver; SunLune as Jasminer's real
adapter family) but **no transport, endpoint, or fingerprint**
— SUGGESTIVE only, not implementable. New names from the
CLI's `--fw-type` enum: **auradine, epic, pit-bit, sealminer**
(Epic's DTOs are `generated/` — code-generated from a spec,
the strongest new lead). Dynamic probe confirmed the generic
discovery order live: HTTP `GET /` on :80, then `:4028`
`stats`/`summary`/`devdetails`/`pools`. One datum per gap
still closes it — a live machine's reply or the vendor doc
(see the table in `docs/vendor-remining.md` §6).

## What a live-machine session still needs

- Braiins: one `version` reply (fingerprint). IceRiver: one
  HTTP session capture. Jasminer: one SunLune API capture.
  Auradine/Epic/Pit-Bit/Sealminer: one capture or doc each.
- `.bmu`: signature scheme/coverage (Dart parser disassembly
  or observing the miner's verifier); payload squashfs
  extraction may expose the upgrade handler.
