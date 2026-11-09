#!/usr/bin/env bash
# End-to-end mock test: start the fake S19 Pro, scan it with BeeSky,
# verify the expected problems are flagged, and record tests/RESULTS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT_JSON="tests/mock_scan.json"
TICKET_DIR="tests/tickets"
RESULTS="tests/RESULTS.md"
rm -rf "$TICKET_DIR" "$OUT_JSON"

python3 tests/mock_miner.py &
MOCK_PID=$!
cleanup() { kill "$MOCK_PID" 2>/dev/null || true; }
trap cleanup EXIT

# Wait until the mock API accepts connections.
python3 - <<'PY'
import socket, sys, time
for _ in range(50):
    try:
        with socket.create_connection(("127.0.0.1", 4028), timeout=0.3):
            sys.exit(0)
    except OSError:
        time.sleep(0.1)
sys.exit("mock miner did not start on 127.0.0.1:4028")
PY

SCAN_OUTPUT="$(python3 -m beesky scan 127.0.0.1 --json "$OUT_JSON" --tickets "$TICKET_DIR" --timeout 1.0)"
echo "$SCAN_OUTPUT"

# Assertions: the scan must flag board 2 (3 missing chips) and board 3
# (88 C >= 85 C limit), mark the miner CHECK, and write a ticket.
ASSERT_OUTPUT="$(python3 - "$OUT_JSON" <<'PY'
import json, sys
records = json.load(open(sys.argv[1]))
assert len(records) == 1, f"expected exactly 1 miner, got {len(records)}"
rec = records[0]
assert rec["model"] == "Antminer S19 Pro", rec["model"]
assert rec["status"] == "CHECK", rec["status"]
assert rec["chips_alive"] == 339 and rec["chips_total"] == 342, rec
chain2 = next(c for c in rec["chains"] if c["index"] == 2)
assert chain2["chips_missing"] == 3, chain2
assert chain2["dead_positions"] == [10, 55, 114], chain2
assert rec["max_temp_c"] == 88, rec["max_temp_c"]
codes = {p["code"] for p in rec["problems"]}
assert "MISSING_CHIPS" in codes, codes
assert "OVER_TEMP" in codes, codes
print("PASS: 1 miner found, model = Antminer S19 Pro")
print("PASS: status = CHECK")
print("PASS: board 2 missing exactly 3 chips at positions 10, 55, 114 (339/342 total)")
print("PASS: board 3 temperature 88 C flagged OVER_TEMP (>= 85 C)")
print("PASS: problem codes =", ", ".join(sorted(codes)))
PY
)"
echo "$ASSERT_OUTPUT"

TICKET_FILE="$(find "$TICKET_DIR" -name 'ticket-*.txt' | head -n 1)"
test -n "$TICKET_FILE"
grep -q "Board 2: thiếu 3 chip" "$TICKET_FILE"
grep -q "Board 3: nhiệt độ cao 88°C" "$TICKET_FILE"
echo "PASS: repair ticket written to $TICKET_FILE with both problems in Vietnamese"

{
  echo "# Mock test results"
  echo
  echo "Fake miner: \`tests/mock_miner.py\` (Antminer S19 Pro sample — board 2 has"
  echo "3 dead chips at positions 10/55/114, board 3 runs at 88 °C)."
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
  echo "PASS: repair ticket written to $TICKET_FILE with both problems in Vietnamese"
  echo '```'
  echo
  echo "## Repair ticket ($TICKET_FILE)"
  echo
  echo '```'
  cat "$TICKET_FILE"
  echo '```'
} > "$RESULTS"

echo
echo "MOCK TEST PASSED — evidence in $RESULTS"
