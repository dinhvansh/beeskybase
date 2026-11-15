# v0.34.0 mapping — IP-Report (closes gap G1)

Gap G1 (docs/presets-ipreport-mapping.md §5) said the IP-Report wire
format was a RESEARCH-GAP: no port, no payload, no sender set was
evidenced in HashCore's shipped materials. This doc records the
public-source research that closes it — and what it does NOT prove.

## 1. The evidence (two independent open-source implementations)

### 1.1 Source A — asic-rs (256foundation, successor of pyasic)

`src/listener.rs` (cloned 2026-11-12, `~/workspace/vendor-research/asic-rs`):

- `AntMinerListener` binds **`UdpSocket::bind("0.0.0.0:14235")`**.
- On ANY datagram received it treats the **sender's source IP as the
  miner** — `factory.get_miner(addr.ip())`. The payload is never
  parsed: for Antminer the source address IS the report.
- `WhatsMinerListener` binds **`0.0.0.0:8888`** the same way.

Grade: **OPEN-SOURCE-IMPLEMENTATION** (maintained library, the
pyasic lineage — the standard community miner-management library).

### 1.2 Source B — Find-My-Miner (OBitsPlease, Avalonia app)

`src/IpScanner.Core/Discovery/IpReportListener.cs` + README
(cloned 2026-11-12, `~/workspace/vendor-research/find-my-miner`):

- `DefaultPort = 14235`; README: "Many miners broadcast their
  address on UDP port 14235 when their IP/IP-report button is
  pressed. **Listen for IP report** opens a passive listener (it
  sends nothing)."
- `Parse(sender, data)`: decodes up to 200 bytes as ASCII text
  (binary payloads → `"(binary) <hex>"` preview, never a crash);
  extracts the first **private IPv4** in the text (regex
  `\b(?:\d{1,3}\.){3}\d{1,3}\b`) and the first **MAC**
  (`[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}`, normalised to
  upper-case colon form); public IPs claimed in the payload are
  ignored; `Target => ReportedIp ?? Sender`.
- Only private-network senders are accepted
  (`IsAcceptableSender`: `Subnet.IsPrivate`, loopback test-only).
- Test fixtures name the payload forms: Bitmain-style
  `"192.168.1.55,AA:BB:CC:DD:EE:FF"` (comma-separated IP,MAC)
  and free text `"Jasminer IP 192.168.1.99 mac
  de-e5-38-f4-64-87"`. A tcpdump-style line in `OffSubnetTests`
  (`169.254.7.7.14235 > 169.254.255.255.14235: UDP`) shows the
  broadcast goes to the subnet broadcast address.
- `OffSubnetDiscovery.cs`: `[14235] = "Bitmain-style IP report
  (used by many ASIC miners)"`.

Grade: **OPEN-SOURCE-IMPLEMENTATION** (independent of asic-rs).

### 1.3 What the two agree on (the buildable contract)

| Fact | asic-rs | Find-My-Miner | Verdict |
|---|---|---|---|
| Transport | UDP, bind 0.0.0.0 | UDP, bind 0.0.0.0, passive | **CORROBORATED** |
| Antminer port | **14235** | **14235** | **CORROBORATED** |
| Sender IP authoritative | yes (only signal used) | yes (fallback) | **CORROBORATED** |
| Payload | ignored | text; extract private IPv4 + MAC | **CORROBORATED** (text form) |
| Sender scope | — | private networks only | adopted (one source) |
| Whatsminer port | **8888** | not mentioned | **SINGLE-SOURCE** |

### 1.4 What is still UNKNOWN (named, not filled in)

- **U1 — the exact canonical Antminer payload bytes.** No real
  packet capture exists in either source; Find-My-Miner's
  `"IP,MAC"` string is the implementation's own test fixture, not
  a capture. BeeSky's design does NOT depend on it: regex
  extraction + sender fallback accept ANY text form (and binary
  payloads are displayed safely). If a real capture later shows a
  fixed format, the parser can be tightened — the listener keeps
  working either way.
- **U2 — HashCore's own listener transport/port.** Still nothing
  in the AOT pools attributes a port to `IpReportService`. BeeSky
  implements the public Bitmain-style protocol (14235) + Whatsminer
  (8888); the user-visible behaviour (toggle, panel, group-open)
  is ported faithfully, but no claim is made that HashCore binds
  the same ports. (Divergence D-IP1.)
- **U3 — Whatsminer 8888.** Single-source (asic-rs). Implemented,
  graded, and labelled in the UI as needing a real button-press
  to confirm. (Divergence D-IP2.)

## 2. HashCore surface being ported (v0.28 §5.1, VERIFIED)

- Settings toggle `ipReportListenerEnabled`;
  `settings_dialog.appearance.ip_report` = "IP Report listening",
  desc "Enables IP-Reports listening in the network" — it lives in
  the **General/Appearance** tab.
- Panel on the Network groups screen
  (`ip_report_action_panel.dart`): `"IP Report listening
  started"`, `"Failed to start IP Report listening"`,
  `"Received IP Report: {}"`; a received address can be **opened
  as a network group**; modifier keys select / isolate the
  reported devices in the current group.

## 3. BeeSky port (mapping)

| HashCore | BeeSky | Notes |
|---|---|---|
| `IpReportService` listener | `beesky/core/ipreport.py`: `IpReportListener` (stdlib threads + UDP sockets, SO_REUSEADDR, bind 0.0.0.0) + `parse_report()` (pure, mirrors Find-My-Miner's Parse incl. binary-safe rendering, private-IP rule, MAC normalisation) | Ports 14235 (Antminer) + 8888 (Whatsminer, single-source) |
| `ipReportListenerEnabled` toggle | `ip_report_enabled` in `beesky-settings.json` (General tab), default **off** (listening opens UDP ports — opt-in; HashCore's default is UNKNOWN) | — |
| Panel on groups screen | Card at the bottom of the groups screen: status line + toggle + received reports | Always visible (HashCore shows the panel on the groups screen) |
| "IP Report listening started" / "Failed to start…" | Same strings (Vietnamese): "Đang nghe IP Report…" / "Không mở được cổng nghe IP Report…" | — |
| "Received IP Report: {}" | Report row: IP (payload or sender), MAC, time, family (Antminer/Whatsminer by port) | — |
| Open as network group | Per-report "Mở thành nhóm" — creates a group with that IP as its target (name "IP Report <ip>") | BeeSky addition of the same action |
| Modifier select / isolate | Per-report "Quét IP này" — scans that single IP into the miners view | BeeSky's equivalent (no modifier-key model in BeeSky's grid) |
| — | `beesky ipreport listen` (NDJSON stream, `--out FILE` persists reports) + `beesky ipreport list --file FILE --json` (read-only) | Bridge verbs in the established --json style; app streams like an ops run |
| — | Reports persist to `beesky-ipreports.json` (cap 100, newest first) | BeeSky choice: a report survives an app restart; HashCore's retention is UNKNOWN |

## 4. Gaps / divergences register

| # | Item | Status |
|---|---|---|
| D-IP1 | BeeSky listens on the public Bitmain-style ports (14235/8888); HashCore's own listener bind is UNKNOWN | divergence (wire side is public protocol, UI behaviour ported) |
| D-IP2 | Whatsminer 8888 is SINGLE-SOURCE (asic-rs only) | gap (confirmation needs a real Whatsminer button-press) |
| D-IP3 | "Mở thành nhóm" creates a group named "IP Report <ip>"; HashCore's group-open naming is UNKNOWN | named choice |
| D-IP4 | Reports persist across restarts (cap 100); HashCore's retention UNKNOWN | BeeSky choice |
| U1 | Exact canonical Antminer payload bytes | UNKNOWN — design does not depend on them |
