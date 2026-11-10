#!/usr/bin/env python3
"""v0.7 GUI smoke test — run under xvfb-run (see run_mock_test_v7.sh).

Starts the scripted sick S19 Pro (tests/mock_miner.py on
127.0.0.1:4028), then launches the real tkinter GUI headlessly via
`python3 -m beesky gui --smoke 127.0.0.1`, which builds the window,
runs one scan through the shared pipeline, fills the Treeview and
prints the rows. Asserts the window saw exactly the mock miner, with
the same values the CLI reports (339/342 chips, CHECK).

v0.19.7 adds first-run assertions on the smoke output:
  * after a scan with results the FIRST row is selected and the
    detail pane shows that miner (auto-land), not the placeholder;
  * an empty scan (nothing answers at 127.0.0.2) leaves NO
    selection and the placeholder text in the detail pane;
  * the window geometry is the screen-fitted size — exactly
    1120x880 whenever the screen is big enough — centred, and
    fully on screen.
"""

import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PLACEHOLDER = ("Chọn một máy trong bảng để xem chi tiết "
               "và danh sách vấn đề.")


def wait_port(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def run_smoke(target: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "gui", "--smoke", target],
        cwd=ROOT, capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout.strip()


def smoke_line(out: str, prefix: str) -> str:
    return next((ln[len(prefix):] for ln in out.splitlines()
                 if ln.startswith(prefix)), "")


def check_geometry(out: str) -> None:
    geo = smoke_line(out, "GUI SMOKE geometry: ")
    m = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+) screen (\d+)x(\d+)", geo)
    assert m, f"unparseable geometry line: {geo!r}"
    w, h, x, y, sw, sh = (int(g) for g in m.groups())
    exp_w, exp_h = min(1120, sw - 32), min(880, sh - 72)
    assert (w, h) == (exp_w, exp_h), \
        f"window {w}x{h}, expected the screen-fitted {exp_w}x{exp_h}"
    print(f"PASS: window size is the screen-fitted {w}x{h} "
          f"(screen {sw}x{sh})")
    assert abs(x - (sw - w) // 2) <= 2 and abs(y - (sh - h) // 2) <= 2, \
        f"window at +{x}+{y}, expected centred near " \
        f"+{(sw - w) // 2}+{(sh - h) // 2}"
    assert x >= 0 and y >= 0 and x + w <= sw and y + h <= sh, \
        f"window +{x}+{y} {w}x{h} not fully on screen {sw}x{sh}"
    print(f"PASS: window centred (+{x}+{y}) and fully on screen")


def main() -> int:
    # -- v0.19.7: empty scan first (mock not up yet, and nothing
    # answers on 127.0.0.2) — the placeholder must survive and no
    # row may be selected.
    rc, out = run_smoke("127.0.0.2")
    print(out)
    assert rc == 1, f"empty gui --smoke exited {rc}, expected 1"
    assert "GUI SMOKE: 0 row(s)" in out, out
    print("PASS: empty scan finds 0 rows (exit 1, as before)")
    assert smoke_line(out, "GUI SMOKE selection: ") == "-", out
    print("PASS: empty scan leaves no selection")
    assert smoke_line(out, "GUI SMOKE detail: ") == PLACEHOLDER, out
    print("PASS: empty scan keeps the detail placeholder "
          "(no stale detail)")

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

        # -- v0.19.7: the scan lands on the first miner.
        assert smoke_line(out, "GUI SMOKE selection: ") == "0", out
        print("PASS: first row is auto-selected after the scan")
        detail = smoke_line(out, "GUI SMOKE detail: ")
        assert "127.0.0.1" in detail and "Antminer S19 Pro" in detail, \
            f"detail pane does not show the first miner: {detail!r}"
        assert PLACEHOLDER not in detail, detail
        print("PASS: detail pane shows the first miner "
              "(not the placeholder)")

        check_geometry(out)
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
