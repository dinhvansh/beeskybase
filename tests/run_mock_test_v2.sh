#!/usr/bin/env bash
# v0.2 end-to-end mock test: all three adapters in one scan.
#   127.0.0.1:4028  fake cgminer S19 Pro (v0.1 sample: sick)
#   127.0.0.2:80    fake VNish dashd S19 Pro (board 1: 2 dead chips,
#                   board 2 at 87 C) -> must be flagged CHECK, source vnish
#   127.0.0.3:80    fake Bitmain stock S19 behind digest auth (healthy)
#                   -> must come back OK, source stock
# Evidence is APPENDED to tests/RESULTS.md (run run_mock_test.sh first so
# the v0.1 section exists; re-running it regenerates the file).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT_JSON="tests/mock_scan_v2.json"
TICKET_DIR="tests/tickets_v2"
RESULTS="tests/RESULTS.md"
rm -rf "$TICKET_DIR" "$OUT_JSON"

python3 tests/mock_miner.py &
PID1=$!
python3 tests/mock_dashd.py &
PID2=$!
python3 tests/mock_bitmain.py &
PID3=$!
cleanup() { kill "$PID1" "$PID2" "$PID3" 2>/dev/null || true; }
trap cleanup EXIT

python3 - <<'PY'
import socket, sys, time
targets = [("127.0.0.1", 4028), ("127.0.0.2", 80), ("127.0.0.3", 80)]
deadline = time.time() + 10
for host, port in targets:
    while True:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                break
        except OSError:
            if time.time() > deadline:
                sys.exit(f"mock did not start on {host}:{port}")
            time.sleep(0.1)
PY

SCAN_OUTPUT="$(python3 -m beesky scan 127.0.0.1,127.0.0.2,127.0.0.3 --json "$OUT_JSON" --tickets "$TICKET_DIR" --timeout 1.0)"
echo "$SCAN_OUTPUT"

ASSERT_OUTPUT="$(python3 - "$OUT_JSON" <<'PY'
import json, sys
records = json.load(open(sys.argv[1]))
assert len(records) == 3, f"expected 3 miners, got {len(records)}"
by_ip = {r["ip"]: r for r in records}

cg = by_ip["127.0.0.1"]
assert cg["source"] == "cgminer", cg["source"]
assert cg["status"] == "CHECK" and cg["chips_alive"] == 339, cg
print("PASS: 127.0.0.1 via cgminer RPC, unchanged v0.1 behaviour (CHECK, 339/342)")

vn = by_ip["127.0.0.2"]
assert vn["source"] == "vnish", vn["source"]
assert vn["model"] == "Antminer S19 Pro", vn["model"]
assert vn["status"] == "CHECK", vn["status"]
assert vn["chips_alive"] == 340 and vn["chips_total"] == 342, vn
board1 = next(c for c in vn["chains"] if c["index"] == 1)
assert board1["chips_missing"] == 2, board1
assert board1["dead_positions"] == [10, 55], board1
assert vn["max_temp_c"] == 87, vn["max_temp_c"]
codes = {p["code"] for p in vn["problems"]}
assert "MISSING_CHIPS" in codes and "OVER_TEMP" in codes, codes
print("PASS: 127.0.0.2 via VNish dashd (CHECK): board 1 missing exactly 2 chips "
      "at positions 10, 55 (340/342); board 2 at 87 C flagged OVER_TEMP")

st = by_ip["127.0.0.3"]
assert st["source"] == "stock", st["source"]
assert st["model"] == "Antminer S19", st["model"]
assert st["status"] == "OK", st
assert st["chips_alive"] == 342 and st["chips_total"] == 342, st
print("PASS: 127.0.0.3 via Bitmain stock CGI + digest auth (OK, healthy S19, 342/342)")
print("PASS: scan table sources = cgminer + vnish + stock")
PY
)"
echo "$ASSERT_OUTPUT"

TICKET_FILE="$TICKET_DIR/ticket-127_0_0_2.txt"
test -f "$TICKET_FILE"
grep -q "Board 1: thiếu 2 chip" "$TICKET_FILE"
grep -q "vị trí chết: 10, 55" "$TICKET_FILE"
grep -q "Board 2: nhiệt độ cao 87°C" "$TICKET_FILE"
echo "PASS: VNish repair ticket written to $TICKET_FILE (missing chips + over-temp, Vietnamese)"

{
  echo
  echo "---"
  echo
  echo "# v0.2 mock test — VNish dashd + Bitmain stock adapters"
  echo
  echo "Three fake miners in one scan: \`tests/mock_miner.py\` (cgminer RPC,"
  echo "127.0.0.1:4028), \`tests/mock_dashd.py\` (VNish dashd API shaped after"
  echo "the firmware's own \`api-doc.json\`, 127.0.0.2:80 — board 1 missing 2"
  echo "chips at positions 10/55, board 2 at 87 °C), \`tests/mock_bitmain.py\`"
  echo "(stock CGI behind digest auth, healthy S19, 127.0.0.3:80)."
  echo
  echo "## Scanner output"
  echo
  echo '```'
  echo "$SCAN_OUTPUT"
  echo '```'
  echo
  echo "## Assertions"
  echo
  echo '```'
  echo "$ASSERT_OUTPUT"
  echo "PASS: VNish repair ticket written to $TICKET_FILE (missing chips + over-temp, Vietnamese)"
  echo '```'
  echo
  echo "## Repair ticket — VNish miner ($TICKET_FILE)"
  echo
  echo '```'
  cat "$TICKET_FILE"
  echo '```'
} >> "$RESULTS"

echo
echo "V0.2 MOCK TEST PASSED — evidence appended to $RESULTS"
