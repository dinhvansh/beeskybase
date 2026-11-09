#!/usr/bin/env python3
"""v0.7 GUI smoke test — run under xvfb-run (see run_mock_test_v7.sh).

Starts the scripted sick S19 Pro (tests/mock_miner.py on
127.0.0.1:4028), then launches the real tkinter GUI headlessly via
`python3 -m beesky gui --smoke 127.0.0.1`, which builds the window,
runs one scan through the shared pipeline, fills the Treeview and
prints the rows. Asserts the window saw exactly the mock miner, with
the same values the CLI reports (339/342 chips, CHECK).
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def wait_port(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> int:
    mock = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_miner.py")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert wait_port(4028), "mock miner did not start on 127.0.0.1:4028"
        print("PASS: mock miner up on 127.0.0.1:4028")

        proc = subprocess.run(
            [sys.executable, "-m", "beesky", "gui", "--smoke", "127.0.0.1"],
            cwd=ROOT, capture_output=True, text=True, timeout=180)
        out = proc.stdout.strip()
        print(out)
        assert proc.returncode == 0, \
            f"gui --smoke exited {proc.returncode}: {proc.stderr[-500:]}"
        print("PASS: beesky gui --smoke exits 0 under the virtual display")
        assert "GUI SMOKE: 1 row(s)" in out, out
        print("PASS: GUI table holds exactly 1 row after one scan")
        first = next((ln for ln in out.splitlines()
                      if ln.startswith("GUI SMOKE first row:")), "")
        for needle in ("127.0.0.1", "Antminer S19 Pro", "339/342", "CHECK"):
            assert needle in first, f"{needle!r} missing from first row: {first}"
        print("PASS: first row = 127.0.0.1 | Antminer S19 Pro | ... | "
              "339/342 chips | CHECK (same values as the CLI)")
    finally:
        mock.terminate()
        try:
            mock.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mock.kill()
    print("\nGUI TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
