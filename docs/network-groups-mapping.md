# Network groups — HashCore Toolkit → BeeSky behaviour mapping (v0.24.0)

> **v0.35.0 update:** the §1.2 divergence is CLOSED — groups now
> carry a `description` field (core `normalise_group` + app
> `NetGroup`, card shows it or "Không có mô tả", editor field,
> group search covers it). The per-range divergences in §1.3
> (typed/named ranges, per-range disable, DNS, port ranges) stand.

Written BEFORE the port, per the dissect-before-porting discipline.
Every HashCore claim below is graded:

- **VERIFIED** — seen in the shipped Toolkit 1.7.5 materials on disk:
  the full translation table (`toolkit-x64/data/flutter_assets/assets/
  translations/en.json`, keys quoted), the AOT string pools
  (`deep/strings-libapp-off.txt`), the Dart file map, and the owner's
  own Windows screenshots of the Network groups page (2026-11-11).
- **INFERRED** — strongly implied by structure/naming, not observed.
- **UNKNOWN** — not observable from the materials on disk. The port
  does NOT invent these; where BeeSky must choose, the choice is
  marked DIVERGENCE and was pre-approved by the coordinator.

Primary prior analysis: `research/hashcore/UI-ANALYSIS.md` §2.1 + §3.

---

## 1. What a "group" is in HashCore

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 1.1 | The home screen IS the Network groups screen ("Network groups", subtitle "Main page"). The app opens there; the miners list is a per-group screen reached from a group ("Back to groups"). | VERIFIED (keys `network_groups.title`, `network_groups.subtitle`; owner's photo) | MATCH: the Flutter app launches on "Nhóm mạng"; "Máy đào" is the second sidebar view. A group scan switches to the miners view scoped to that group. |
| 1.2 | A group is a named object with: name, description ("No description" when unset), and a list of NETWORK RANGES. | VERIFIED (`network_groups.no_description`, edit-dialog keys `name_title` / `description_title`, `add_ip_range`) | PARTIAL / DIVERGENCE: BeeSky groups carry `name` + `targets` but NO `description` field (pre-approved v0.24 schema). |
| 1.3 | Ranges are TYPED objects in a list: IP ranges and PORT ranges, each individually named ("Range {}", `default_range_name`), renamable, and individually enable/disable-able for scanning (`range_disabled` = "Disabled for scan"). Addresses may also be DNS names ("DNS record"). Validation: "Invalid IPv4 range", "Reversed IPv4 range", "Port or address must be constant in the range", invalid DNS/IP/port messages (`validation.farm.*`). | VERIFIED (translation keys + file map: `models/farm/ip_address_range.dart`, `device_address.dart`, `ip_address_range_helper.dart`) | DIVERGENCE (pre-approved): BeeSky groups hold ONE multi-range string in the existing scan-target syntax (CIDR / `a-b` ranges / comma mixes), expanded and validated by the core's `parse_targets` — which already rejects bad IPs, reversed ranges and oversized unions loudly. No per-range names, no per-range disable, no DNS names, no port ranges. |
| 1.4 | Groups persist in `farms.json` in the app-data dir, via `FarmsService` / `FarmsStorageDto` (fromJson/toJson); the Farm model composes ranges + addresses (`models/farm/farm.dart`). A `Farm.fromOldRange` symbol suggests migration from a legacy ranges format. | VERIFIED (AOT literals `farms.json`, `FarmsStorageDto.fromJson`, `Farm.fromOldRange`) | MATCH in spirit: BeeSky persists `beesky-groups.json` (document `{"version": 1, "groups": [...]}`), located with the SAME strategy as the v0.23 creds file (beside the executable, `%APPDATA%\BeeSky\` fallback). No legacy format exists to migrate. |
| 1.5 | Exact `farms.json` field names/types. | UNKNOWN — the AOT pool exposes class/API names but does not attribute JSON keys to the DTO. | BeeSky uses its own documented schema (§4 below). Not a divergence: there is nothing observable to match. |

## 2. The groups screen

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 2.1 | Compact stat chips across the top: **Miners · Unlocked · Errors**. | VERIFIED (§2.1) | ADAPTED: BeeSky chips count groups-side facts it actually knows: total groups, groups with a last scan, total errors across last scans. BeeSky scans do not "unlock" devices, so there is no Unlocked chip (the scan-time equivalent — which login authenticated — is per-miner `cred_label`, unchanged from v0.23). |
| 2.2 | Each group card/row shows: name, description, ranges count, miners, unlocked, hashrate, errors, **last scan time**, autoscan state (icon tooltips "Autoscan enabled/disabled"). | VERIFIED (keys in `network_groups`) | MATCH minus fields BeeSky does not have: card shows name, targets summary, last-scan line ("Chưa quét" or time + scanned/found/OK/CHECK/ERROR counts), autoscan state line, and [Quét nhóm] [Sửa] [Xóa]. No description, no ranges COUNT (targets are one string — the string itself is the summary), no hashrate/unlocked totals on the card (pre-approved `last_scan` schema). |
| 2.3 | A group never scanned or opened carries a "new" tag (`new_tag`, tooltip "New ranges group which hasn't been scanned or opened yet"). | VERIFIED | MATCH: never-scanned groups (last_scan == null) carry a "MỚI" tag. (BeeSky has no separate "opened" event; scanning is the only state change — noted, not hidden.) |
| 2.4 | Empty state: centred icon + "Groups not defined" + "To create a group of devices, you must click on [New group] or [Import range group]" + buttons. | VERIFIED (`empty_title`, `empty_subtitle`, `empty_import`) | MATCH: BeeSky shows the same shape (icon + line + [Thêm nhóm]) when the store is empty. |
| 2.5 | Search groups "by IP, name or description"; a filtered-empty state exists ("Groups not found"). | VERIFIED | NOT PORTED in v0.24 (farm group counts are small; the sidebar screens have no search boxes anywhere yet). Recorded as a gap, not a silent omission. |
| 2.6 | Group-list operations menu: Autoscan groups · Import range groups · Export selected (JSON) · View groups in combined mode · Merge network groups · Reset statistics · Remove selected; plus "Rescan all groups", "Remove all groups". | VERIFIED (`network_groups.commands.*`) | PARTIAL: v0.24 ports per-group autoscan, JSON export/import (CLI + store format), and per-group remove. NOT ported: combined view, merge (see §3), reset-statistics as a separate act (deleting `last_scan` happens by editing the store / re-adding the group), rescan-all, remove-all, multi-select. Each is a named gap below. |
| 2.7 | "Reset statistics" = "Clear last scan statistics" — statistics are a distinct stored thing that can be dropped without deleting the group ("Drop statistics" dialog). | VERIFIED (`commands.reset_desc`, `dialogs.drop_statistics`) | ADAPTED: `last_scan` lives ON the group object; there is no separate statistics store and no reset command in v0.24. |
| 2.8 | An **IP Report panel** listens for miners' hardware IP-Report broadcasts; a received address can be opened as a network group. | VERIFIED (`ip_report_panel`) | OUT OF SCOPE for v0.24 (it is its own feature; already on the owner's copy-list as a later item). |

## 3. Group operations

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 3.1 | Edit-group dialog: name + description + ranges list editor, per-range menu (Enabled / Rename / Delete), "Save and scan" button (saving can chain straight into a scan). | VERIFIED (`dialogs.edit_group.*`, `save_and_scan`) | ADAPTED: the BeeSky editor dialog holds name, targets, autoscan (toggle + interval), and the group's own credential sets (reusing the v0.23 creds editor). No "Save and scan" chain — saving returns to the cards, where [Quét nhóm] is one click. Noted divergence in flow, not in data. |
| 3.2 | Removing a group asks first: "Are you sure you want to remove ranges group?" with the group named in the consequence text. | VERIFIED (`remove_range_message`, `dialogs.remove_group.*`) | MATCH: BeeSky's delete asks in a confirm dialog naming the group. |
| 3.3 | MERGE: "Merge network groups — Create new group from selected"; the merge variant of the edit dialog offers "Create new merge group" and "Don't delete source groups" (`keep_groups`): with it ON the sources survive the merge, otherwise they are consumed. | VERIFIED (commands + edit-dialog keys) | NOT PORTED in v0.24. DIVERGENCE (deferred, pre-approved scope): BeeSky has no multi-select and no merge. The CLI import merge-by-name (§3.4) covers the file-level case only. |
| 3.4 | EXPORT selected groups as JSON (file dialog, "JSON format export"); IMPORT range groups from a file. | VERIFIED (`ranges_import`, `ranges_export`, `export_desc`, import/export dialog titles) | MATCH at CLI level: `beesky groups export <file>` writes the store document; `beesky groups import <file>` merges it in. |
| 3.5 | Import conflict policy when an imported group's name already exists. | UNKNOWN — no string or code path on disk answers it. | BeeSky policy (coordinator-specified, stated in docs): merge BY NAME — a same-name imported group REPLACES the stored one, all other stored groups are kept, new names are appended. Invalid entries fail the whole import (exit 2), matching the creds file's fail-loud philosophy. |
| 3.6 | "View groups in combined mode" — the combined device list of several groups at once. | VERIFIED (`commands.view_*`) | NOT PORTED as a mode. A manual multi-range scan (comma targets) is the pre-existing equivalent for one pass; it carries no group identity. Named gap. |
| 3.7 | "Rescan group" per group; "Rescan all groups" globally; scans are Operations tasks (cancellable, progress, history). | VERIFIED (`rescan_range`, `refresh_ranges_statistic`) | PARTIAL: [Quét nhóm] / `scan --group` rescans one group. There is no task system yet (later copy-list item), so no cancel/progress/history, and no rescan-all. Named gap. |

## 4. Per-group overrides (the farms.json layer)

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 4.1 | Unlock methods layer: GLOBAL (Settings → Unlock, one method per firmware vendor) → PER-GROUP override → one-shot task argument. The group editor contains a "Custom password" dialog and a "Custom timeout" dialog. | VERIFIED (UI-ANALYSIS §3.2/§3.4; `dialogs.edit_group.custom_password.title`, `custom_timeout.title`) | MATCH in layering, adapted to BeeSky's v0.23 list model (pre-approved): a group may carry its OWN list of credential sets (same schema as the global creds file). Per-miner try order inside a group scan: (a) group sets matching the detected family → (b) global sets matching the family → (c) group "any" → (d) global "any" → (e) all remaining sets, group-then-global. Implemented by concatenating group-then-global and reusing v0.23's `ordered_creds` (its stable partition produces exactly this order); proven by tests (group set beats global same-family set; global rescues when the group set fails). |
| 4.2 | Per-group CUSTOM TIMEOUT override. | VERIFIED (dialog title above; values/unit UNKNOWN) | NOT PORTED: BeeSky scans keep the single scan timeout. Named gap (small; revisit if a farm needs slow-link groups). |
| 4.3 | A group's override REPLACES the global method for its vendor (it is not a merged list) — HashCore's model is one method per vendor per layer. | VERIFIED (§3: "one unlock method per firmware vendor, layered") | DIVERGENCE (inherited from v0.23, deliberate + documented there): BeeSky's layers MERGE as lists, because v0.23 allows multiple sets per vendor (same firmware, different passwords per hall). A wrong group password therefore costs attempts but never locks a machine out — the global sets still get tried. This is the one place BeeSky is intentionally MORE forgiving than the original. |

## 5. Autoscan

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 5.1 | Each group has an `autoscanEnabled` flag (AOT get/set literals) and the group editor carries an Autoscan field: label "Autoscan", dialog title "Autoscan timeout", tooltip "Interval for groups auto-scanning"; disabled reads "No scan". | VERIFIED | MATCH: each BeeSky group carries `autoscan: {enabled, interval_min}` (default off, 30 min); the card shows the state; the editor has the toggle + interval field. |
| 5.2 | The autoscan INTERVAL's unit, range and default. | UNKNOWN — no unit string for the field was found in the mined strings. | BeeSky uses MINUTES (`interval_min`, must be ≥ 1). BeeSky's choice, flagged here because HashCore's could not be observed. |
| 5.3 | There is ALSO a GLOBAL master switch: Settings → Appearance "Autoscan group ranges" ("Automatic statistics update for groups list"), and the per-group autoscan dialog warns "Autoscan is now disabled in app settings. Enable it to take effect". Autoscan is run by an app-side `AutoscanController`. | VERIFIED (settings keys, dialog warning, controller file path) | DIVERGENCE (pre-approved): BeeSky has no global settings screen, so there is no master switch — the per-group toggle is the only gate. Like HashCore, BeeSky's autoscan runs APP-SIDE while the app is open (a timer re-scans the active/last group at its interval); BeeSky's always-on equivalent remains the farm agent. |
| 5.4 | Autoscan updates group STATISTICS in the background (the settings description says "statistics update", and a `groupStatisticRefreshIntervalSeconds` symbol exists). Whether autoscan performs full discovery scans or statistics refreshes only. | INFERRED (wording) / partially UNKNOWN | BeeSky's app-side autoscan performs a full group scan (discovery + fetch) and therefore also refreshes `last_scan`. If HashCore's is statistics-only, BeeSky's is heavier — noted. |

## 6. Last-scan statistics

| # | HashCore behaviour | Grade | BeeSky behaviour |
|---|---|---|---|
| 6.1 | Cards display last-scan-derived numbers (miners / unlocked / hashrate / errors) and the last scan time; a `lastScan` symbol exists in the services pool. | VERIFIED (card keys; `lastScan` literal) | MATCH (subset): BeeSky persists `last_scan = {at, scanned, found, ok, check, error}` on the group after ANY successful scan run with that group (CLI human mode and bridge `--json` alike), and the card renders it. |
| 6.2 | Which exact fields are persisted, and whether they live inside farms.json or a separate statistics store. | UNKNOWN | BeeSky stores the summary on the group inside beesky-groups.json (pre-approved schema). No hashrate total is stored (records' native units make a single total misleading — the v0.20 lesson; the miners view already shows per-unit totals live). |

## 7. BeeSky group schema (v0.24)

```json
{"version": 1, "groups": [
  {"id": "9f1c…", "name": "Trại chính",
   "targets": "192.168.2.0/24",
   "creds": [ {"label": "...", "user": "...", "password": "...",
               "type": "any|stock|vnish", "api_key": "..."} ],
   "autoscan": {"enabled": false, "interval_min": 30},
   "last_scan": {"at": "2026-11-11T09:41:07+07:00", "scanned": 254,
                 "found": 63, "ok": 12, "check": 51, "error": 0} }
]}
```

`creds` entries use EXACTLY the v0.23 `--creds-file` entry schema and
normalisation. `id` is a random hex id minted on creation (identity
for the app; NAME is the identity for CLI lookup and import merging,
because names are what operators type).

## 8. Divergence / gap register (summary)

Pre-approved divergences: targets as one multi-range string (§1.3);
no description field (§1.2); merged-list credential layering instead
of per-vendor replacement (§4.3); autoscan app-side only, minutes,
no global master switch (§5.2–5.3); `last_scan` subset (§6.1).

Named gaps (not built in v0.24, none of them silent): group search
(§2.5), combined view (§3.6), merge groups (§3.3), reset-statistics
command (§2.7), rescan-all / remove-all / multi-select (§2.6),
per-group timeout (§4.2), IP-Report → group (§2.8), "Save and scan"
flow (§3.1).

Unknowns never invented: farms.json field names (§1.5), HashCore's
import conflict policy (§3.5), autoscan interval unit/range (§5.2),
last-scan persistence shape (§6.2), whether HashCore autoscan is
statistics-only (§5.4).
